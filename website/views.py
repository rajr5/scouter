from django.http import HttpResponseRedirect,HttpResponseBadRequest,HttpResponseNotFound, HttpResponse
from django.contrib.auth.decorators import login_required
# from django.contrib.auth import logout
from django.shortcuts import render_to_response
from django.core.exceptions import ObjectDoesNotExist
from django.template import RequestContext
from django.contrib import messages
from django.conf import settings
from django.db import IntegrityError
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.forms.models import model_to_dict
from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialAccount, SocialToken
from website.models import GoogleCredential
from glass.mirror import Mirror, Timeline, Contact
import logging
from django.views.decorators.csrf import csrf_exempt
import json
from scouter import scout
import io
from apiclient.http import MediaIoBaseUpload
import urllib
from glass import oauth_utils
from django.contrib.auth import login, authenticate, logout
import os

debug_logger = logging.getLogger('debugger')
client_secrets_filename = os.path.join(settings.PROJECT_ROOT, 'client_secrets.json')


def homepage(request):
    debug_logger.debug("User id: {0}".format(request.user.id))
    if not request.user.is_authenticated():
        return HttpResponseRedirect(oauth_utils.get_auth_url(request, client_secrets_filename=client_secrets_filename, redirect_uri=settings.GOOGLE_REDIRECT_URI))
    print request.user.id
    try:
        credentials = oauth_utils.get_credentials(request)
    except Exception:
        return logout(request)
    # try:
    # token = _get_token(request.user.id)
    if credentials is not None:
        mirror = Mirror()
        service = mirror.get_service_from_token(credentials.access_token, refresh_token=credentials.refresh_token, token_expiry=credentials.token_expiry)
        # print "Token", token
        # timeline = Timeline(text="Hello Glass!")
        # mirror.post_timeline(timeline)
        _register_glass_app(mirror, request.user.id)
    # except Exception as e:
    #     print e
    #     print "No token for user id", request.user.id
    return render_to_response('home.html', context_instance=RequestContext(request))

def oauth_redirect(request):
    return oauth_utils.process_oauth_redirect(request, client_secrets_filename=client_secrets_filename, redirect_uri=settings.GOOGLE_REDIRECT_URI)

def _register_glass_app(mirror, id):
    """
    Create a Contact object and add it to the user's Glass. Then subscribe to notifications from that contact.
    """
    contacts = mirror.list_contacts()
    for contact in contacts:
        print "contact", contact.id
    # if len(contacts) == 0:
    mirror.clear_contacts()
    contact = Contact(display_name="Scouter", id=id, image_urls=['https://scouteronglass.com/static/img/logo_square.png'],
                      type="INDIVIDUAL", accept_types=["image/jpeg", "image/png"], priority=1)
    mirror.post_contact(contact)
    mirror.subscribe(callback_url='https://scouteronglass.com/mirror/subscription/reply/', subscription_type="reply", user_token=id)


@login_required
def clear_contacts(request):
    credentials = _get_credentials(request.user.id)
    mirror = Mirror()
    service = mirror.get_service_from_token(credentials.access_token, refresh_token=credentials.client_secret)
    print "got service"
    mirror.clear_contacts()
    return HttpResponse("Clear!")

@login_required
def callback(request):
    pass

@login_required
def auth_return(request):
    pass

def _get_credentials(id):
    debug_logger.info("Get credentials for user: {0}".format(id))
    return GoogleCredential.objects.get(user=id)

def _get_token(id):
    # print "token id", id

    account = SocialAccount.objects.get(user=id)
    token = SocialToken.objects.get(account=account.id)
    return token


@csrf_exempt
def subscription_reply(request):
    debug_logger.debug("Subscription reply")
    debug_logger.debug(request.POST)
    debug_logger.debug(request.META)
    debug_logger.debug(request.body)
    # Get user id
    # print "Req body", request.body
    print request.POST
    try:
        post = json.loads(request.body)
    except Exception:
        debug_logger.exception("Couldn't load request.body")
        post = dict(request.POST)
    print "post", post.items()
    user_id = post['userToken']
    user = User.objects.get(id=user_id)
    # print "token", user, "userid", user.id, "socialaccountid", SocialAccount.objects.all()[0].user.id
    credentials = _get_credentials(user.id)

    if credentials is not None:
        mirror = Mirror()
        service = mirror.get_service_from_token(credentials.access_token)
        for m in mirror.list_timeline():
            print m.id
    else:
        return HttpResponseBadRequest("Need valid userToken")
    #print "list timeline", mirror.list_timeline()[0]
    item = mirror.parse_notification(request.body)
    timeline_item = item.timeline
    #print "TA", timeline_item.attachments
    attachment = mirror.get_timeline_attachment(timeline_item)
    #print "attach", type(attachment), attachment
    with open('image.jpg', 'w') as f:
        f.write(attachment)
    #print "Attachment", attachment
    cards = scout('image.jpg')
    #print "Power levels", cards
    try:
        timeline = _create_timelines(cards, mirror, timeline_item)
    except Exception:
        debug_logger.exception("Could not create the timeline card.")
        raise
    mirror.update_timeline(timeline)
    return HttpResponse('OK')

def _create_timelines(cards, mirror, timeline_item):
    """
    Take the faces and power levels in cards, and modify timeline_item using mirror to be a bundle of power level
    timeline cards.
    """
    card_template = """
    <article>
        <figure>
            <img src="attachment:1">
        </figure>
        <section>
            <h1 style="color:yellow">Power Level:</h1>
            <h1 style="color:yellow">{power_level}</h1>
            {over_9000}
        </section>
    </article>
    """
    fail_template = """
    <article>
        <section>
            <h1 style="color:yellow;text-align:center">No lifeforms</h1>
            <h1 style="color:yellow;text-align:center">Detected</h1>
        </section>
    </article>
    """
    if len(cards) == 0:
        # No faces, replace old image with this one.
        timeline_item.html = fail_template
        mirror.update_timeline(timeline_item)
        return timeline_item
    elif len(cards) > 1:
        for card in cards[1:]:
            # Create a new timeline card for each of the other cards, adding them to a bundle.
            pass
    template_data = {'power_level': cards[0][1]}
    if template_data['power_level'] > 9000:
        template_data['over_9000'] = """<h1 style="color:red">It's over 9000!!!!</h1>"""
    else:
        template_data['over_9000'] = ""
    timeline_item.html = card_template.format(**template_data)
    img_file = '/tmp/{0}.jpg'.format(cards[0][0])
    mirror.insert_timeline_attachement(timeline_item, img_file)
    # timeline_item.add_attachment(img_file, 'image/jpg')
    return timeline_item


