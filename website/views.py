from django.http import HttpResponseRedirect,HttpResponseBadRequest,HttpResponseNotFound, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
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
from glass.mirror import Mirror, Timeline, Contact


# Create your views here.
@login_required
def homepage(request):
    print request.user.id
    # try:
    token = _get_token(request.user.id)
    if token is not None:
        mirror = Mirror()
        service = mirror.get_service_from_token(token.token)
        # print "Token", token
        # timeline = Timeline(text="Hello Glass!")
        # mirror.post_timeline(timeline)
        _register_glass_app(mirror, request.user.id)
    # except Exception as e:
    #     print e
    #     print "No token for user id", request.user.id
    return render_to_response('home.html', context_instance=RequestContext(request))

def _register_glass_app(mirror, id):
    """
    Create a Contact object and add it to the user's Glass. Then subscribe to notifications from that contact.
    """
    contact = Contact(display_name="Scouter", id=id, image_urls=['http://scouter.servercobra.com/static/img/glass_display.png'],
                      type="INDIVIDUAL", accept_types=["image/jpeg", "image/png"], priority=1)
    mirror.post_contact(contact)
    for contact in mirror.list_contacts():
        print "contact", contact.id
    mirror.subscribe(callback_url='https://scouter.servercobra.com/mirror/subscription/reply/', subscription_type="reply", user_token=id)


@login_required
def clear_contacts(request):
    token = _get_token(request.user.id)
    mirror = Mirror()
    service = mirror.get_service_from_token(token.token)
    print "got service"
    mirror.clear_contacts()
    return HttpResponse("Clear!")

@login_required
def callback(request):
    pass

@login_required
def auth_return(request):
    pass

def _get_token(id):
    account = SocialAccount.objects.get(user=id)
    token = SocialToken.objects.get(account=account.id)
    return token

def subscription_reply(request):
    pass
