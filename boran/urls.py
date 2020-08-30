from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.shortcuts import render
from django.urls import path
from sentry_sdk import last_event_id


urlpatterns = [
    path('admin/', admin.site.urls),
    url(r'^phonebank/', include('phonebank.urls'), name='phonebank'),
]


def handler500(request, *args, **argv):
    """Handle errors with Sentry user feedback.

    https://docs.sentry.io/enriching-error-data/user-feedback/?platform=django
    """
    return render(request, '500.html', {
        'sentry_dsn': settings.SECRETS['SENTRY_DSN'],
        'sentry_event_id': last_event_id(),
    }, status=500)
