import random
import logging
import json
from django.forms import model_to_dict
import os
from django.http import HttpResponseRedirect, HttpResponseBadRequest, HttpResponse, HttpResponseNotFound
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth import logout
from allauth.socialaccount.models import SocialAccount, SocialToken
from website.models import GoogleCredential, ScoutedPerson
from website.glass.mirror import Mirror, Contact, TimelineMenuItem
from scouter import scout
from glass import oauth_utils


debug_logger = logging.getLogger('debugger')
client_secrets_filename = os.path.join(
    settings.PROJECT_ROOT, 'client_secrets.json')


def homepage(request):
    template_data = {}
    debug_logger.debug("User id: {0}".format(request.user.id))
    if not request.user.is_authenticated():
        # We need to create an auth URL for non authenticated users. They will see an "Install on Glass" button.
        template_data['auth_url'] = oauth_utils.get_auth_url(request, client_secrets_filename=client_secrets_filename,
                                                             redirect_uri=settings.GOOGLE_REDIRECT_URI)
    return render_to_response('home.html', template_data, context_instance=RequestContext(request))


def install(request):
    template_data = {}
    debug_logger.debug("Installing for user id: {0}".format(request.user.id))
    mirror = _get_mirror(request.user.id)
    _register_glass_app(mirror, request.user.id)
    # return HttpResponseRedirect('https://google.com/myglass')
    return HttpResponseRedirect('/')


@csrf_exempt
def subscription_reply(request):
    # debug_logger.debug("Subscription reply")
    # debug_logger.debug(request.POST)
    # debug_logger.debug(request.META)
    # debug_logger.debug(request.body)

    # Load the payload from Google
    try:
        post = json.loads(request.body)
    except Exception:
        debug_logger.exception("Couldn't load request.body")
        post = dict(request.POST)
    # We only care if something was shared to us. If they deleted something, we don't care for now.
    if 'userActions' not in post or post['userActions'][0]['type'] != "SHARE":
        return HttpResponse("Non share ignored.")

    # Find the user that shared it to us.
    user_id = post['userToken']
    user = User.objects.get(id=user_id)
    try:
        mirror = _get_mirror(user_id)
    except ValueError:
        return HttpResponseBadRequest("Need valid userToken")

    # Ask our mirror library to parse the notification for us, returning a timeline item we can use and the shared
    # image.
    item = mirror.parse_notification(request.body)
    timeline_item = item.timeline
    timeline_item.notify = True
    attachment = mirror.get_timeline_attachment(timeline_item)
    # Create a random, 30 character filename to write the image to.
    filename = '%030x.jpg' % random.randrange(16 ** 30)
    full_image_filename = os.path.join(
        settings.PROJECT_ROOT, 'scouter/static/posted_images/', filename)
    with open(full_image_filename, 'w') as f:
        f.write(attachment)
    # Find all the faces.
    cards = scout(full_image_filename, os.path.join(settings.PROJECT_ROOT, 'scouter/static/faces/'))
    try:
        timeline = _create_timelines(cards, mirror, timeline_item)
    except Exception:
        debug_logger.exception("Could not create the timeline card.")
        raise
    # Save the old image and the new image as an object for display later.
    try:
        if len(cards) > 0:
            scouted_person = ScoutedPerson(face=cards[0]['face'], original=filename, user=user,
                                           power_level=cards[0]['power_level'])
        else:
            scouted_person = ScoutedPerson(face=None, original=filename, user=user)
        scouted_person.save()
    except Exception:
        debug_logger.exception("Problem saving ScoutedPerson")
    # Add in SHARE and DELETE options to timeline card.
    share = TimelineMenuItem(action="SHARE")
    delete = TimelineMenuItem(action="DELETE")
    timeline.add_menu_item(share)
    timeline.add_menu_item(delete)
    # Update the returned card.
    mirror.update_timeline(timeline)
    return HttpResponse('OK')


def oauth_redirect(request):
    return oauth_utils.process_oauth_redirect(request, client_secrets_filename=client_secrets_filename,
                                              redirect_uri=settings.GOOGLE_REDIRECT_URI, post_auth_redirect='/install/')


@login_required
def clear_contacts(request):
    credentials = _get_credentials(request.user.id)
    mirror = _get_mirror(request.user.id)
    mirror.clear_contacts()
    return HttpResponse("Clear!")


def logout_view(request):
    """
    Log out the user
    @param request:
    @type request:
    @return:
    @rtype:
    """
    # try:
    #     credentials = _get_credentials(request.user.id)
    #     mirror = _get_mirror(request.user.id)
    #     mirror.clear_contacts()
    # except Exception:
    #     pass
    logout(request)
    return HttpResponseRedirect('/')

@login_required
def person(request, person_id=None):
    """
    Four possible ways. If person_id, show it, logged in or not. If logged in and no person_id, show all for user.
    If neither, throw errror.
    If person_id = 'staff' and user is staff, show all images.
    @param request:
    @type request:
    @param person_id:
    @type person_id:
    @return:
    @rtype:
    """
    template_data = {
        'persons': []
    }
    if person_id:
        persons = ScoutedPerson.objects.filter(id=person_id)
    elif request.user.is_authenticated():
        persons = ScoutedPerson.objects.filter(user=request.user.id)
    elif request.user.is_staff and person_id == 'staff':
        persons = ScoutedPerson.objects.all()
    else:
        persons = ScoutedPerson.objects.none()

    # Error handling
    if len(persons) == 0:
        if person_id:
            return HttpResponseNotFound()
        else:
            return render_to_response("person.html", template_data, context_instance=RequestContext(request))
    # Convert queryset to objects to return to template renderer
    for person in persons:
        person_dict = model_to_dict(person)
        person_dict['face_path'] = person.face_path()
        person_dict['original_path'] = person.original_path()
        person_dict['created'] = person.created
        template_data['persons'].append(person_dict)

    return render_to_response("person.html", template_data, context_instance=RequestContext(request))

def _get_mirror(user_id):
    """
    Given a request, build the mirror object by getting the credentials from the DB and building it.
    @param request:
    @type request:
    @return:
    @rtype:
    """
    try:
        google_credentials = GoogleCredential.objects.get(user=user_id)
    except Exception:
        raise ValueError("User {0} has no GoogleCredential".format(user_id))
    oauth_credentials = google_credentials.oauth2credentials()
    mirror = Mirror.from_credentials(oauth_credentials)
    google_credentials.refresh(http=mirror.http)
    return mirror


def _register_glass_app(mirror, id):
    """
    Create a Contact object and add it to the user's Glass. Then subscribe to notifications from that contact.
    """
    contacts = mirror.list_contacts()
    # if len(contacts) == 0:
    mirror.clear_contacts()
    if settings.ENV == "production":
        display_name = "Scouter"
    else:
        display_name = "Scouter Dev"
    contact = Contact(
        display_name=display_name, id=id, image_urls=[
            'https://scouteronglass.com/static/img/contact_img4.png'],
        type="INDIVIDUAL", accept_types=["image/jpeg", "image/png"], priority=1)
    mirror.post_contact(contact)
    mirror.subscribe(
        callback_url='https://scouteronglass.com/mirror/subscription/reply/', subscription_type="reply", user_token=id)


def _get_credentials(id):
    debug_logger.info("Get credentials for user: {0}".format(id))
    return GoogleCredential.objects.get(user=id)


def _get_token(id):
    account = SocialAccount.objects.get(user=id)
    token = SocialToken.objects.get(account=account.id)
    return token


def _create_timelines(cards, mirror, timeline_item):
    """
    Take the faces and power levels in cards, and modify timeline_item using mirror to be a bundle of power level
    timeline cards.
    """
    card_template = """
    <article>
        <figure>
            <img src="attachment:1" height="360" width="240">
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
            <h1 style="color:yellow;text-align:center">scouted</h1>
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
            # Create a new timeline card for each of the other cards, adding
            # them to a bundle.
            pass
    template_data = cards[0]
    if template_data['power_level'] > 9000:
        template_data[
            'over_9000'] = """<h1 style="color:red">It's over 9000!!!!</h1>"""
    else:
        template_data['over_9000'] = ""
    timeline_item.html = card_template.format(**template_data)
    mirror.insert_timeline_attachement(timeline_item, cards[0]['face'])
    # timeline_item.add_attachment(img_file, 'image/jpg')
    return timeline_item
