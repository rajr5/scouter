from django.conf.urls import patterns, include, url

urlpatterns = patterns('website.views',
    url(r'^google/redirect/', 'oauth_redirect'),
)