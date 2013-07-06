from oauth2client.tools import run
from oauth2client.client import OAuth2WebServerFlow
from oauth2client import multistore_file
from oauth2client.file import Storage
import json
import os
import gflags
import sys
import httplib2
from apiclient.discovery import build
import io
from apiclient.http import MediaIoBaseUpload

DEFAULT_SCOPE = [
    'https://www.googleapis.com/auth/glass.timeline',
]
FLAGS = gflags.FLAGS
CREDENTIAL_STORAGE_FILE = 'credentials.json'
DEFAULT_MENU_ACTIONS = ('REPLY', 'REPLY_ALL', 'DELETE', 'SHARE', 'READ_ALOUD', 'VOICE_CALL', 'NAVIGATE', 'TOGGLE_PINNED')

class Mirror(object):
    """
    An object that assists with all the connections between you and the Mirror API for a single client.
    Similar to boto's "Connection". Most times you need to query or post to the API, it goes through Mirror,
    usually returning various objects such as Timeline objects.
    You will need one Mirror per user.
    """
    def __init__(self, scopes=None):
        """
        Initialize the scopes this Mirror instance will be able to access on behalf of the user.
        """
        if scopes is None:
            self.scopes = DEFAULT_SCOPE
        else:
            self.scopes = scopes

    def get_my_oauth(self, scope=None):
        """
        For testing only!!!!!!!
        Used to get an oauth token for yourself (or test user)
        Will pop up a browser request to allow access.
        """
        try:
            argv = FLAGS(sys.argv)  # parse flags
        except gflags.FlagsError, e:
            print '%s\\nUsage: %s ARGS\\n%s' % (e, sys.argv[0], FLAGS)
            sys.exit(1)
        # print "ARGV", argv
        flow = self._get_flow(scope)
        storage = self._get_storage()
        credentials = None
        try:
            credentials = storage.get()
            print "get credentials", credentials
        except Exception:
            pass
            # credentials = None
        if credentials is None:
            credentials = run(flow, storage)
            print "credentials was none, now", credentials
        # print credentials
        self.service = self._get_service(credentials)
        return credentials

    def post_timeline(self, timeline):
        """
        Posts the timeline object to the user's Timeline
        return status.
        """
        if timeline.attachment:
            return self.service.timeline().insert(body=timeline.timeline_body(), media_body=timeline.attachment).execute()
        else:
            return self.service.timeline().insert(body=timeline.timeline_body()).execute()
            # return self.service.timeline().insert(body=timeline.timeline_body()).execute()

    def list_timeline(self):
        """
        Returns the list of Timeline objects.
        """
        timeline = self.service.timeline().list().execute()
        timeline_list = []
        for t in timeline['items']:
            timeline_list.append(Timeline(json_data=t))
        return timeline_list

    def get_timeline(self, id):
        """
        Returns a single timeline object
        """
        return Timeline(json_data=self.service.timeline().get(id=id).execute())

    def clear_timeline(self):
        for timeline in self.list_timeline():
            self.delete_timeline(timeline.id)

    def delete_timeline(self, id):
        return self.service.timeline().delete(id=id).execute()

    def post_contact(self, contact):
        """
        Posts a contact/service that the user will be able to share with
        """
        return self.service.contacts().insert(body=contact.contact_body()).execute()

    def list_contacts(self):
        """
        Returns a list of Contact objects
        """
        contact = self.service.contact().list().execute()
        contact_list = []
        for c in contact['items']:
            contact_list.append(Contact(json_data=c))
        return contact_list

    def _get_service(self, credentials):
        """
        Builds a service object using the API discovery document. Sets self.service
        """
        if credentials is None:
            raise Exception("Invalid credentials")
        http = httplib2.Http()
        http = credentials.authorize(http)
        service = build('mirror', 'v1', http=http)
        return service

    def _get_client_secrets(self, filename=None):
        """
        Gets client secrets from the provided filename.
        If filename is none, goes through the default list of places to find a set of client secrets for this app.
        TODO Also throws up an error if client secrets is world readable.
        Default list:
        ./client_secrets.json
        /etc/client_secrets.json

        Returns a tuple of (client_id, client_secret)
        """
        # Ensure provide filename works.
        if filename is not None and not os.path.exists(filename):
            raise Exception("Provided client_secrets file {0} does not exist.".format(filename))
        # Try to find client_secrets file by going through defaults list.
        if filename is not None and os.path.exists(filename):
            json_file = filename
        elif os.path.exists('client_secrets.json'):
            json_file = 'client_secrets.json'
        elif os.path.exists('/etc/client_secrets.json'):
            json_file = '/etc/client_secrets.json'
        else:
            raise Exception("Could not find client secrets.")
        # Read in the file as JSON and try to get the client id and secret.
        try:
            f = open(json_file).read()
        except Exception as e:
            raise Exception("Could not open client secrets file: {0} because {1}".format(json_file, e))
        try:
            data = json.loads(f)
        except Exception as e:
            raise Exception("Could not read JSON data from client secrets file: {0} because {1}".format(json_file, e))
        try:
            print data
            client_id = data['web']['client_id']
            client_secret = data['web']['client_secret']
        except ValueError:
            raise Exception("Clients secret file must have client_id and client_secret.")
        return client_id, client_secret


    def _get_flow(self, redirect_uri=None, client_secrets_filename=None):
        """
        Generates a server flow to obtain an oauth secret.
        Scope is a list of scopes required for this oauth key. Defaults to
        """
        client_id, client_secret = self._get_client_secrets()
        if redirect_uri is None:
            redirect_uri = 'https://localhost:8080'
        flow = OAuth2WebServerFlow(client_id=client_id,
                               client_secret=client_secret,
                               scope=self.scopes,
                               redirect_uri=redirect_uri)
        return flow


    def _get_storage(self):
        return Storage(CREDENTIAL_STORAGE_FILE)

class Timeline(object):
    attachment = None
    text = None
    html = None
    pinned = False
    title = None

    menu_items = []

    def __init__(self, text=None, html=None, json_data=None, notify=False, menu_items=None):
        if json_data is not None:
            for k, v in json_data.items():
                # print "Setting timeline val", k, v
                setattr(self, k, v)
            return
        if text:
            self.text = text
        if html:
            self.html = html
        self.notify = notify
        if menu_items:
            self.menu_items = menu_items

    def add_attachment(self, filename, content_type):
        """
        Add the file at filename identified by content_type. content_type should be something like 'image/jpeg'
        """
        if not os.path.exists(filename):
            raise ValueError("File does not exist: {0}".format(filename))
        self.attachment_filename = filename
        self.attachment_content_type = content_type
        media = open(filename).read()
        self.attachment = MediaIoBaseUpload(io.BytesIO(media), mimetype=content_type, resumable=True)

    def timeline_body(self):
        timeline_body = {}
        if self.text:
            timeline_body['text'] = self.text
        if self.html:
            timeline_body['html'] = self.html
        if self.notify:
            timeline_body['notification'] = {'level': 'DEFAULT'}
        print "Timeline body", timeline_body
        return timeline_body

    def add_menu_item(self, item):
        """
        Adds a menu item to the timeline card.
        Accepts either a string for a default menu item (must be in DEFAULT_MENU_ITEMS), or a TimelineMenuItem.
        """

    def __str__(self):
        if self.title:
            return self.title
        elif self.text:
            return self.text[0:80]
        else:
            return self.html

class TimelineMenuItem(object):
    action = None

    def __init__(self, action, values, id=None, remove_when_selected=False,  ):
        # Check that string items are in default menu items. Non string items should be TimelineMenuItems.
        if action not in DEFAULT_MENU_ACTIONS or action == "CUSTOM":
            raise Exception("{0} not in default menu items or CUSTOM".format(action))
        self.action = action
        if self.action == "CUSTOM":
            # Make sure we have a default value in values
            default = 0
            for value in values:
                if 'displayName' not in value or 'iconUrl' not in value or 'state' not in value:
                    raise Exception("Custom menu actions need displayName, iconUrl, and state.")
                if value['state'] == "DEFAULT":
                    default += 1
            if default != 1:
                raise Exception("Custom menu actions need exactly one menu item with 'state' set to DEFAULT")
            self.values = values

class Contact(object):
    """
    Represents something users can share to.
    """
    def __init__(self, display_name, id=None, image_urls=[], type="INDIVIDUAL", accept_types = [], phone_number=None, priority=1, json_data=None):
        if json_data is not None:
            for k, v in json_data.items():
                setattr(self, k, v)
            return
        if display_name is None or display_name == "":
            raise Exception("Contacts must have display names.")
        self.display_name = display_name
        if id is None:
            self.id = display_name.replace(' ', '_')
        if image_urls == []:
            raise Exception("Contacts must have image urls.")
        if len(image_urls) > 8:
            raise Exception("Contacts cannot have more than 8 image URLs.")
        self.image_urls = image_urls
        if type not in ("INDIVIDUAL", "GROUP"):
            raise Exception("Contact type must be either INDIVIDUAL or GROUP")
        self.type = type
        self.accept_types = accept_types
        self.phone_number = phone_number
        self.priority = priority

    def contact_body(self):
        body = {
            'displayName': self.display_name,
            'imageUrls': self.image_urls,
            'type': self.type,
            'id': self.id
        }
        if self.accept_types:
            body['acceptTypes'] = self.accept_types
        if self.phone_number:
            body['phoneNumber'] = self.phone_number
        if self.priority:
            body['priority'] = self.priority
        return body


# class TimelineAttachment(object):
#     def __init__(self, filename, content_type):
#         if not os.path.exists(filename):
#             raise ValueError("File does not exist: {0}".format(filename))
#         self.filename = filename
#         media = open(filename).read()
#         self.media_body = MediaIoBaseUpload(io.BytesIO(media), mimetype=content_type, resumable=True)