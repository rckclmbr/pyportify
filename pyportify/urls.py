from django.conf import settings
from django.conf.urls import patterns, url

print settings.STATIC_ROOT

urlpatterns = patterns('',
    url(r'^google/login$', 'pyportify.views.google_login'),
    url(r'^spotify/login$', 'pyportify.views.spotify_login'),
    url(r'^portify/transfer/start$', 'pyportify.views.transfer_start'),
    url(r'^spotify/playlists', 'pyportify.views.spotify_playlists'),

    url(r'^$', 'django.views.static.serve',
        {'document_root': settings.STATIC_ROOT, 'path': 'index.html'}),
    url(r'^(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.STATIC_ROOT}),
)
