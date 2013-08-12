from django.db import models
import json
# from oauth2client.django_orm import FlowField
from django.contrib.auth.models import User
from django.db import models
from oauth2client.django_orm import FlowField
from django.db import models
# from oauth2client.django_orm import FlowField
from django.contrib.auth.models import User
from django.contrib.auth.models import User
from django.db import models
from oauth2client.django_orm import FlowField, CredentialsField
from oauth2client.django_orm import Storage
from django.contrib import admin
from oauth2client.client import Credentials
import datetime
from oauth2client.client import OAuth2Credentials
from django.utils.timezone import utc
import logging

logger = logging.getLogger("debugger")

class GoogleCredential(models.Model):
    """
    Google's provided model was cool, except South didn't like it.
    """
    token_expiry = models.DateTimeField(default=datetime.datetime.now())
    access_token = models.CharField(max_length=255)
    token_uri = models.URLField(default="https://accounts.google.com/o/oauth2/token")
    invalid = models.BooleanField(default=False)
    token_type = models.CharField(max_length=32)
    expires_in = models.IntegerField()
    client_id = models.CharField(max_length=255)
    # id_token = models.CharField(max_length=255)
    client_secret = models.CharField(max_length=64)
    revoke_uri = models.URLField()
    user_agent = models.CharField(max_length=255, blank=True, null=True, default=None)
    user = models.ForeignKey(User, primary_key=True)
    refresh_token = models.CharField(max_length=255, blank=True, null=True, default=None)

    @classmethod
    def from_json(cls, json_data, user=None):
        """
        Given a normal credential JSON response from Google, fill in the blanks.
        @param cls:
        @type cls:
        @param json_data:
        @type json_data:
        @param user:
        @type user:
        @return: credential
        @rtype: GoogleCredential
        """
        cred_data = json.loads(json_data)
        print cred_data
        credential = GoogleCredential()
        # DEBUG CODE ONLY
        # if user is None:
        credential.user = user
        for k, v in cred_data['token_response'].items():
            setattr(credential, k, v)
        del cred_data['token_response']
        for k, v in cred_data.items():
            setattr(credential, k, v)
        credential.save()
        return credential

    def needs_refresh(self):
        now = datetime.datetime.utcnow().replace(tzinfo=utc)
        logger.debug("token expiry {0} now {1} needs refresh? {2}".format(self.token_expiry, now, self.token_expiry < now))
        return self.token_expiry < now

    def refresh(self, http, force=False):
        # Refreshes if necessary.
        if self.needs_refresh() or force:
            credentials = self.oauth2credentials()
            credentials.refresh(http)
            logger.debug("refresh token {0}".format(credentials.refresh_token))
            logger.debug("token expiry {0} old {1}".format(credentials.token_expiry, self.token_expiry))
            self.refresh_token = credentials.refresh_token
            self.token_expiry = credentials.token_expiry
            self.save()
        else:
            logger.debug("Token refresh not needed")

    def oauth2credentials(self):
        kwargs = {
            "token_expiry": self.token_expiry,
            "access_token": self.access_token,
            "token_uri": self.token_uri,
            # "invalid": self.invalid,
            # "token_type": self.token_type,
            # "expires_in": self.expires_in,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "revoke_uri": self.revoke_uri,
            "user_agent": self.user_agent,
            "refresh_token": self.refresh_token,
        }
        return OAuth2Credentials(**kwargs)


class CredentialsAdmin(admin.ModelAdmin):
    pass

admin.site.register(GoogleCredential, CredentialsAdmin)