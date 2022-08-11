from urllib.parse import quote_plus

from django.conf import settings
import requests
import telnyx

from phonebank.models import Agent, TelnyxCredential


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


def fetch_telnyx_tokens(agents=None):
    if agents is None:
        agents = Agent.objects.filter(is_active=True)
    for agent in agents:
        response = telnyx.TelephonyCredential.create(
            connection_id=settings.SECRETS['TELNYX_CONNECTION_ID'],
        )
        credential_id = response['id']
        token = create_telnyx_token(credential_id)
        telnyx_credential = TelnyxCredential(
            id=credential_id, token=token, agent=agent,
        )
        telnyx_credential.save()


def delete_telnyx_tokens():
    telnyx_credentials = telnyx.TelephonyCredential.list(page={'size': 250})
    if telnyx_credentials.data:
        for telnyx_credential in telnyx_credentials.auto_paging_iter():
            try:
                telnyx_credential.delete()
            except telnyx.error.APIError as e:
                # Raise errors other than HTTP 204, which appears intentional.
                if 'HTTP response code was 204' not in e.user_message:
                    raise
    TelnyxCredential.objects.all().delete()
