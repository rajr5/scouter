from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from django.views.generic.base import RedirectView
admin.autodiscover()

urlpatterns = patterns(
    '',
    # Examples:
    # url(r'^$', 'scouter.views.home', name='home'),

    # Uncomment the admin/doc line below to enable admin
    # documentation:
    url(r'^admin/doc/', include(
        'django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    (r'^robots\.txt$', 'django.views.generic.simple.direct_to_template', {'template': 'robots.txt', 'mimetype': 'text/plain'}),
    (r'^favicon\.ico$', 'django.views.generic.simple.redirect_to', {'url': '/static/images/favicon.ico'}),
    # All other requests go to website.urls.
)

urlpatterns += patterns(
    'website.views',
    url(r'^oauth/google/redirect/', 'oauth_redirect'),
    url(r'^$', 'homepage'),
    url(r'install/$', 'install'),
    url(r'^clear_contacts/$', 'clear_contacts'),
    url(r'^mirror/subscription/reply/$', 'subscription_reply'),
    url(r'^logout/$', 'logout_view')
)