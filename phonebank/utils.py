from django.conf import settings
import requests

from phonebank.models import Agent, TelnyxCredential


def fetch_telnyx_tokens(agents=None):
    if agents is None:
        agents = Agent.objects.filter(is_active=True)
    for agent in agents:
        response = requests.post(
            'https://api.telnyx.com/v2/telephony_credentials',
            json={'connection_id': settings.SECRETS['TELNYX_CONNECTION_ID']},
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization':
                    'Bearer ' + settings.SECRETS['TELNYX_API_KEY'],
            },
        )
        response.raise_for_status()
        print(response.json()['data'])
        credential_id = response.json()['data']['id']
        response = requests.post(
            '/'.join([
                'https://api.telnyx.com/v2/telephony_credentials',
                credential_id, '/token'
            ]),
            json={'connection_id': settings.SECRETS['TELNYX_CONNECTION_ID']},
            headers={
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + settings.SECRETS['TELNYX_API_KEY']
            },
        )
        response.raise_for_status()
        token = response.text
        telnyx_credential = TelnyxCredential(
            id=credential_id, token=token, agent=agent,
        )
        telnyx_credential.save()
