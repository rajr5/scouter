from django.contrib import admin
from website.models import GoogleCredential, ScoutedPerson


class CredentialsAdmin(admin.ModelAdmin):
    pass


admin.site.register(GoogleCredential, CredentialsAdmin)
admin.site.register(ScoutedPerson)
