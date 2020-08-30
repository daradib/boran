from django.conf.urls import url

from phonebank import views

urlpatterns = [
    url(r'^$', views.phonebank_view, name='index'),
    url(r'^api/voter/$', views.api_view),
    url(r'^api/voter/(?P<id>\w+)/$', views.api_view),
]
