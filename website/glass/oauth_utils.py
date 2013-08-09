import os
import json
import random
from django.contrib.auth.models import User
# from oauth2client.django_orm import Storage
from website.models import GoogleCredential
from oauth2client import xsrfutil
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from oauth2client.client import flow_from_clientsecrets
from django.contrib.auth import login, authenticate


def get_auth_url(request, redirect_uri='http://localhost:8000/oauth/google/redirect/', client_secrets_filename=None):
    flow = _get_flow(redirect_uri=redirect_uri, client_secrets_filename=client_secrets_filename)
    # flow.params['state'] = xsrfutil.generate_token(settings.SECRET_KEY, request.user)
    return flow.step1_get_authorize_url()

def process_oauth_redirect(request, post_auth_redirect='/', client_secrets_filename=None, redirect_uri=None):
    # if not xsrfutil.validate_token(settings.SECRET_KEY, request.REQUEST['state'], request.user):
        # return  HttpResponseBadRequest("State did not validate.")
    flow = _get_flow(client_secrets_filename=client_secrets_filename, redirect_uri=redirect_uri)
    print flow
    print request.REQUEST
    cred = flow.step2_exchange(request.REQUEST)
    if not request.user.is_authenticated():
        # Create a new user automagically.
        user = User()
        user.username = '%030x' % random.randrange(16**30)
        # password = '%030x' % random.randrange(16**30)
        user.set_unusable_password()
        user.save()
        # authenticate(username=user.username)
        user.backend='django.contrib.auth.backends.ModelBackend'
        login(request, user)
    else:
        user = request.user
    print "Cred", cred
    credential = GoogleCredential.from_json(cred.to_json(), request.user)
    return HttpResponseRedirect(post_auth_redirect)

def get_credentials(request):
    if not request.user.is_authenticated():
        raise OauthException("User must be logged in to get credentials.")
    try:
        credentials = GoogleCredential.objects.get(user=request.user.id)
        return credentials
    except Exception as e:
        raise OauthException("Oauth credentials do not exist.")



def _get_client_secrets(filename=None):
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
        json_file = 'client_secrets.rsisejson'
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

def _get_flow(redirect_uri='http://localhost:8000/oauth/google/redirect/', client_secrets_filename=None, ):
    """
    Generates a server flow to obtain an oauth secret.
    Scope is a list of scopes required for this oauth key. Defaults to
    """
    # print "redir_uri", redirect_uri
    scope = getattr(settings, 'GOOGLE_SCOPE', None)
    print "Scope", scope
    if scope is None:
        raise OauthException("No scope provided.")
    # If we're using default redirect URI, check the settings file for a better default.
    if getattr(settings, 'GOOGLE_OAUTH_REDIRECT', False) and redirect_uri == 'https://localhost:8000':
        redirect_uri = getattr(settings, 'GOOGLE_OAUTH_REDIRECT')

    if client_secrets_filename is not None and not os.path.exists(client_secrets_filename):
        raise Exception("Provided client_secrets file {0} does not exist.".format(client_secrets_filename))
    # Try to find client_secrets file by going through defaults list.
    if client_secrets_filename is not None and os.path.exists(client_secrets_filename):
        json_file = client_secrets_filename
    elif os.path.exists('client_secrets.json'):
        json_file = 'client_secrets.json'
    elif os.path.exists('/etc/client_secrets.json'):
        json_file = '/etc/client_secrets.json'
    else:
        raise Exception("Could not find client secrets.")

    flow = flow_from_clientsecrets(
        json_file,
        scope=scope,
        redirect_uri=redirect_uri)
    return flow

class OauthException(Exception):
    pass


