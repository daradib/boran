from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.utils.timezone import now

from phonebank.models import Agent, Voter
from phonebank.utils import fetch_telnyx_token, register_telnyx_call


def get_agent(request):
    try:
        key = request.GET['key']
    except KeyError:
        raise KeyError('Missing key parameter')
    try:
        agent = Agent.objects.get(uuid=key)
    except Agent.DoesNotExist:
        raise KeyError('Invalid key parameter')
    agent.last_active = now()
    agent.save()
    return agent


def phonebank_view(request):
    try:
        agent = get_agent(request)
    except KeyError as e:
        return HttpResponse(e, status=401)
    return render(request, 'phonebank/index.html', {
        'nav_links': settings.SECRETS['NAV_LINKS'],
        'google_form_url': settings.SECRETS['GOOGLE_FORM_URL'],
        'jitsi_server': settings.SECRETS['JITSI_SERVER'],
        'jitsi_room': agent.room_name,
        'agent_name': agent.nickname,
        'sentry_dsn': settings.SECRETS['SENTRY_DSN'],
    })


def api_view(request, id=None):
    try:
        agent = get_agent(request)
    except KeyError as e:
        return HttpResponse(e, status=401)
    if not agent.is_active:
        return HttpResponse('Your access is not enabled', status=403)
    if id == '0':
        # No voter requested. Client is trying to connect/reconnect to Telnyx.
        return JsonResponse({
            'telnyx_token': fetch_telnyx_token(agent),
        })
    provided_count = Voter.objects.filter(
        provided_to=agent,
        provided_at__gt=now() - timedelta(minutes=5),
    ).count()
    if provided_count > 15:
        agent.is_active = False
        agent.save()
        return HttpResponse('You have requested contacts too fast', status=403)
    with transaction.atomic():
        if id:
            voter = Voter.objects.select_for_update().get(
                id=id,
            )
        else:
            voter = Voter.objects.select_for_update().filter(
                provided_to__isnull=True,
            ).order_by('-priority', '?').first()
        voter.provided_to = agent
        voter.provided_at = now()
        voter.save()
    for phone in voter.map_phones().values():
        register_telnyx_call(phone)
    return JsonResponse({
        'voter': voter.to_dict(),
        'similar_voters': [v.to_dict() for v in voter.find_similar_voters()],
        'telnyx_token': fetch_telnyx_token(agent),
    })
