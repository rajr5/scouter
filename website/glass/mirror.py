from oauth2client.tools import run
from oauth2client.client import OAuth2WebServerFlow, OAuth2Credentials
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
import datetime

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



    def get_my_oauth(self, scope=None, hostname='localhost', port="8000"):
        """
        For testing only!!!!!!!
        Used to get an oauth token for yourself (or test user)
        Will pop up a browser request to allow access.
        """
        # Wow! Look at this hack!
        sys.argv.append('--auth_host_port')
        sys.argv.append(port)
        sys.argv.append('--auth_host_name')
        sys.argv.append(hostname)
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
        except Exception:
            pass
            # credentials = None
        if credentials is None:
            credentials = run(flow, storage)
        # print credentials
        self._get_service(credentials)
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

    def update_timeline(self, timeline):
        """
        Updates an existing timeline object in place.
        """
        if timeline.attachment:
            return self.service.timeline().update(id=timeline.id, body=timeline.timeline_body(), media_body=timeline.attachment).execute()
        else:
            return self.service.timeline().update(id=timeline.id, body=timeline.timeline_body()).execute()

    def list_timeline(self):
        """
        Returns the list of Timeline objects.
        """
        print "list"
        timeline = self.service.timeline().list().execute()
        print "after list"
        timeline_list = []
        for t in timeline['items']:
            timeline_list.append(Timeline(json_data=t))
        return timeline_list

    def get_timeline(self, id):
        """
        Returns a single timeline object
        """
        print "timeline id", id
        ##
        print "service", self.service
        print self.service.timeline()
        print self.service.timeline().list().execute()
        ##
        timeline_json = self.service.timeline().get(id=id).execute()
        return Timeline(json_data=timeline_json)

    def clear_timeline(self):
        for timeline in self.list_timeline():
            self.delete_timeline(timeline.id)

    def delete_timeline(self, id):
        return self.service.timeline().delete(id=id).execute()

    def get_timeline_attachment(self, timeline_item):
        print "attachment id", timeline_item.attachment
        args = {'itemId': timeline_item.id, 'attachmentId': timeline_item.attachments}
        # response, content = self.http.request('https://www.googleapis.com/mirror/v1/timeline/{itemId}/attachments/{attachmentId}'.format(**args))
        response, content = self.http.request(timeline_item.attachment_url)
        # timeline_item.attachment = content
        return content

    def insert_timeline_attachement(self, timeline_item, filename):
        img = open(filename, 'r').read()
        media_body = MediaIoBaseUpload(
            io.BytesIO(img), mimetype="image/jpg", resumable=True)
        self.service.timeline().attachments().insert(
        itemId=timeline_item.id, media_body=media_body).execute()

    def list_locations(self):
        locations = []
        locs = self.service.locations().list().execute()
        for l in locs:
            locations.append(Location.from_json(self.service, l))
        return locations

    def locations_on_map(self, locations):
        """
        Given locations and some parameters, create a map of them.
        @param locations:
        @type locations:
        @return:
        @rtype:
        """
        pass

    def post_contact(self, contact):
        """
        Posts a contact/service that the user will be able to share with
        """
        print contact
        print contact.contact_body()
        return self.service.contacts().insert(body=contact.contact_body()).execute()

    def list_contacts(self):
        """
        Returns a list of Contact objects
        """
        contact = self.service.contacts().list().execute()
        contact_list = []
        for c in contact['items']:
            contact_list.append(Contact(json_data=c))
        return contact_list

    def clear_contacts(self):
        for contact in self.list_contacts():
            self.delete_contact(contact.id)

    def delete_contact(self, id):
        return self.service.contacts().delete(id=id).execute()

    # Subscription handler
    def subscribe(self, callback_url, subscription_type="all", user_token=None, verify_token=None, ):
        """
        Creates a new subscription to user actions or location.
        @param callback_url: the url Google will POST the subscription updates to. (HTTP required) You can then use
        Mirror.parse_notification on the update.
        @param subscription_type: Type of actions to list for. One of "all", "share", "reply", "delete", "custom",
        "location"
        @param user_token: Unique user token for app. Can be basically anything.
        @param verify_token: Unique verification token to ensure posts are coming from Google.
        @return: JSON from Google in response to the subscription.
        """
        subscription_to_operation = {
            "share": "UPDATE",
            "reply": "INSERT",
            "delete": "DELETE",
            "custom": "UPDATE",
            "all": None,
            "location": "UPDATE",
        }
        if subscription_type not in ["all", "share", "reply", "delete", "custom", "location"]:
            raise Exception('Subscription type must be one of ["all", "share", "reply", "delete", "custom", "location"] ')
        # build subscription dict to send to Google
        subscription = {}
        if subscription_type == "location":
            subscription['collection'] = "locations"
        else:
            subscription['collection'] = "timeline"
        subscription['operation'] = subscription_to_operation[subscription_type]
        if user_token:
            subscription['userToken'] = user_token
        if verify_token:
            subscription['verifyToken'] = verify_token
        subscription['callbackUrl'] = callback_url

        return self.service.subscriptions().insert(body=subscription).execute()

    def unsubscribe(self, collection="timeline"):
        if collection not in ["timeline", "locations"]:
            raise Exception('Collection must be one of ["timeline", "locations"].')
        return self.service.subscriptions().delete(collection).execute()

    def list_subscriptions(self):
        return self.service.subscriptions().list().execute().get('items', [])

    def parse_notification(self, request_body, subscription_object=None):
        """Parse a request body into a notification dict.
        Params:
          request_body: The notification payload sent by the Mirror API as a string.
          subscription_object: Allows for overriding subscription objects to have built in handling.
        Returns:
          Dict representing the notification payload.
        """
        notification = json.loads(request_body)
        if subscription_object:
            sub = subscription_object()
        else:
            sub = SubscriptionEvent()
        sub.parse(notification, self)
        return sub

    def _get_service(self, credentials):
        """
        Builds a service object using the API discovery document. Sets self.service
        """
        if credentials is None:
            raise Exception("Invalid credentials")
        http = httplib2.Http()
        http = credentials.authorize(http)
        # http = credentials._refresh(http)
        self.http = http
        service = build('mirror', 'v1', http=http)
        self.service = service
        return service



    def get_service_from_token(self, access_token, token_expiry=None, client_secrets_filename=None, refresh_token=None):
        """
        Give tokens, create an OAuth2Credentials object and use it to build the Mirror service. Useful if you only
        have the tokens and don't feel like making the object yourself.
        @param access_token:
        @type access_token:
        @param token_expiry:
        @type token_expiry:
        @param client_secrets_filename:
        @type client_secrets_filename:
        @param refresh_token:
        @type refresh_token:
        @return:
        @rtype:
        """
        client_id, client_secret = self._get_client_secrets(client_secrets_filename)
        credentials = OAuth2Credentials(access_token=access_token, client_id=client_id, client_secret=client_secret,
                                        refresh_token=refresh_token, token_expiry=token_expiry, token_uri="https://accounts.google.com/o/oauth2/token", user_agent=None)
        # print "auth"
        # credentials.authorize()
        # print "authed"
        return self._get_service(credentials)
    
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
            redirect_uri = 'https://localhost:8000'
        print "redir_uri", redirect_uri
        flow = OAuth2WebServerFlow(client_id=client_id,
                               client_secret=client_secret,
                               scope=self.scopes,
                               redirect_uri=redirect_uri,
                               access_type='offline')
        print flow.redirect_uri
        return flow

    def _get_storage(self):
        return Storage(CREDENTIAL_STORAGE_FILE)

    @classmethod
    def from_credentials(cls, credentials, scopes=[]):
        """
        Given a credentials object, get the Mirror object with credentials, service, and http initialized.
        @param credentials:
        @type credentials:
        @return:
        @rtype:
        """

        mirror = cls(scopes)
        mirror._get_service(credentials)
        return mirror

class SubscriptionEvent(object):
    def parse(self, notification, mirror):
        """

        @param notification: dict parsed from JSON from Google POST.
        @param mirror: a Mirror object so the object can preemptively get Timeline and Location objects.
        @return: event_type: The parsed event type, also saved to self.event_type. The rest of the parsed information
        will be saved to object attributes, depending on type.
        SHARE and REPLY will a timeline attribute that is a Timeline object.
        DELETE will have a timeline_id attribute which is the deleted card's id.
        CUSTOM will have a actions attribute that is a dict of the custom userActions the user did and
        a menu_item attribute that is the id for a TimelineMenuItem. It is up to you to find that TimelineMenuItem.
        Location updates will have a location attribute that is a Location object representing the user's latest
        location.
        """
        self._mirror = mirror
        try:
            self.item_id = notification["itemId"]
            self.operation = notification["operation"]
            self.user_token = notification["userToken"]
            if 'verifyToken' in notification:
                self.verify_token = notification["verifyToken"]
            else:
                # No verification token in custom type?
                self.verify_token = None
            self.verify(self.verify_token)
            # Dispatch to individual type handlers based on action type
            if notification["collection"] == "locations":
                self.event_type = "locations"
                self._location_update(notification)
            notification_type = notification["userActions"][0]["type"]

            if notification_type == 'SHARE':
                self.event_type = 'share'
                self._share(notification)
            elif notification_type == 'REPLY':
                self.event_type = "reply"
                self._reply(notification)
            elif notification_type == 'DELETE':
                self.event_type = "delete"
                self._delete(notification)
            elif notification_type == 'CUSTOM':
                self.event_type = "custom"
                self._custom(notification)
            else:
                raise Exception("Unknown notification type from Google: {0}".format(notification_type))
            return self.event_type
        except KeyError as e:
            raise Exception("Malformed subscription message from Google.")

    def verify(self, verify_token):
        """
        Override this if you want built in verification of all steps. Raise an exception if it does not verify.
        """
        return

    def _location_update(self, notification):
        raise NotImplementedError()

    def _share(self, notification):
        print "notification", notification['itemId']
        self.timeline = self._mirror.get_timeline(notification['itemId'])

    def _reply(self, notification):
        self.timeline = self._mirror.get_timeline(notification['itemId'])

    def _delete(self, notification):
        """
        Really nothing to do here. We could verify maybe?
        """
        return

    def _custom(self, notification):
        # self.menu_item = self._mirror.
        self.menu_item = notification['itemId']
        self.actions = notification['userActions']
        # Don't need type, already saved.
        del(self.actions['type'])


class Timeline(object):
    attachment = None
    text = None
    html = None
    pinned = False
    title = None
    notify = None

    menu_items = []

    def __init__(self, text=None, html=None, json_data=None, notify=False, menu_items=None):
        if json_data is not None:
            for k, v in json_data.items():
                if k == 'attachments':
                    for a in v:
                        print "A", a
                        if 'contentUrl' in a:
                            self.attachment_url = a['contentUrl']
                print "Setting timeline val", k, v
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
        return str(self.id)


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
    Requires either display_name or json_data.
    """
    def __init__(self, display_name=None, id=None, image_urls=[], type="INDIVIDUAL", accept_types = [], phone_number=None, priority=1, json_data=None):
        if json_data is not None:
            for k, v in json_data.items():
                setattr(self, k, v)
            return
        if display_name is None or display_name == "":
            raise Exception("Contacts must have display names.")
        self.display_name = display_name
        if id is None:
            self.id = display_name.replace(' ', '_')
        else:
            self.id = id
        if image_urls == []:
            raise Exception("Contacts must have image urls.")
        elif len(image_urls) > 8:
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
        print "body", body
        return body


class Location(object):
    """
    An object representing the latest location.
    """
    # Stores historical locations

    def __init__(self, service, location_id="latest"):
        self.service = service
        if location_id is None:
            return
        self.get_location(location_id=location_id)

    def get_location(self, location_id="latest"):
        """
        Get the latest location and store it in the Location object.
        @param location_id: The location_id specified by Google in the subscription notice. Defaults to latest
        @type location_id:
        @return:
        @rtype:
        """
        location = self.service.locations().get(id=location_id).execute()
        self.latitude = location.get('latitude', None)
        self.longitude = location.get('longitude', None)
        self.accuracy = location.get('accuracy', None)
        self.displayName = location.get('displayName', None)
        self.address = location.get('address', None)
        self.id = location.get('id', None)
        self.timestamp = location.get('timestamp', None)
        return location

    def on_map(self, height, width):
        """
        Displays this location on a map.
        @param height:
        @type height:
        @param width:
        @type width:
        @return:
        @rtype:
        """
        pass

    @classmethod
    def from_json(cls, service, location):
        cls.__init__(service, None)
        cls.latitude = location.get('latitude', None)
        cls.longitude = location.get('longitude', None)
        cls.accuracy = location.get('accuracy', None)
        cls.displayName = location.get('displayName', None)
        cls.address = location.get('address', None)
        cls.id = location.get('id', None)
        cls.timestamp = location.get('timestamp', None)
        return cls








# class TimelineAttachment(object):
#     def __init__(self, filename, content_type):
#         if not os.path.exists(filename):
#             raise ValueError("File does not exist: {0}".format(filename))
#         self.filename = filename
#         media = open(filename).read()
#         self.media_body = MediaIoBaseUpload(io.BytesIO(media), mimetype=content_type, resumable=True)



if __name__ == '__main__':
    mirror = Mirror()
    mirror.get_my_oauth()

