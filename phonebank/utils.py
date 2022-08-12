from urllib.parse import quote_plus

from django.apps import apps
from django.conf import settings
import requests
import telnyx


if 'TELNYX_API_KEY' in settings.SECRETS:
    telnyx.api_key = settings.SECRETS['TELNYX_API_KEY']


def create_telnyx_token(credential_id):
    """Create access token (JWT) for Telnyx on-demand credential.

    This is equivalent to `telnyx.TelephonyCredential.create_token`
    which requires telnyx-python 2.0.0+ (not yet released to PyPI).
    """
    response = requests.post(
        '/'.join([
            'https://api.telnyx.com/v2/telephony_credentials',
            quote_plus(credential_id), '/token'
        ]),
        json={'connection_id': settings.SECRETS['TELNYX_CONNECTION_ID']},
        headers={
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + settings.SECRETS['TELNYX_API_KEY']
        },
    )
    response.raise_for_status()
    return response.text


def fetch_telnyx_token(agent):
    if not agent.is_active:
        return
    if agent.telnyx_credential is None:
        response = telnyx.TelephonyCredential.create(
            connection_id=settings.SECRETS['TELNYX_CONNECTION_ID'],
        )
        telnyx_credential = apps.get_model('phonebank.TelnyxCredential')(
            id=response['id'], agent=agent,
        )
    else:
        telnyx_credential = agent.telnyx_credential
    telnyx_credential.token = create_telnyx_token(telnyx_credential.id)
    telnyx_credential.save()
    return telnyx_credential.token


def fetch_telnyx_tokens(agents=None):
    if agents is None:
        agents = apps.get_model('phonebank.Agent').objects.filter(
            is_active=True,
        )
    for agent in agents:
        fetch_telnyx_token(agent)


def delete_telnyx_credential(credential_id):
    telnyx_credential = telnyx.TelephonyCredential.retrieve(credential_id)
    try:
        telnyx_credential.delete()
    except telnyx.error.APIError as e:
        # Raise errors other than HTTP 204, which appears intentional.
        if 'HTTP response code was 204' not in e.user_message:
            raise


def delete_telnyx_credentials():
    telnyx_credentials = telnyx.TelephonyCredential.list(page={'size': 250})
    if telnyx_credentials.data:
        for telnyx_credential in telnyx_credentials.auto_paging_iter():
            try:
                telnyx_credential.delete()
            except telnyx.error.APIError as e:
                # Raise errors other than HTTP 204, which appears intentional.
                if 'HTTP response code was 204' not in e.user_message:
                    raise
    apps.get_model('phonebank.TelnyxCredential').objects.all().delete()
