from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.utils.timezone import now

from phonebank.models import Agent, Voter
from phonebank.utils import fetch_telnyx_token, register_telnyx_call


def get_agent(request):
    key = request.GET['key']
    agent = Agent.objects.get(uuid=key)
    agent.last_active = now()
    agent.save()
    return agent


def phonebank_view(request):
    try:
        agent = get_agent(request)
    except KeyError:
        return HttpResponse('Missing key parameter', status=400)
    except Agent.DoesNotExist:
        return HttpResponse('Invalid key parameter', status=401)
    return render(request, 'phonebank/index.html', {
        'nav_links': settings.SECRETS['NAV_LINKS'],
        'form_url': settings.SECRETS['FORM_URL'],
        'jitsi_server': settings.SECRETS['JITSI_SERVER'],
        'jitsi_room': agent.room_name,
        'agent_name': agent.nickname,
        'sentry_dsn': settings.SECRETS['SENTRY_DSN'],
    })


def api_view(request, id=None):
    try:
        agent = get_agent(request)
    except KeyError:
        return HttpResponse('Missing key parameter', status=400)
    except Agent.DoesNotExist:
        return HttpResponse('Invalid key parameter', status=401)
    if not agent.is_active:
        return HttpResponse('Your access is not enabled', status=403)
    if id == '0':
        # No voter requested. Client is trying to connect/reconnect to Telnyx.
        return JsonResponse({
            'telnyx_token': fetch_telnyx_token(agent),
            'agent_stats': agent.print_stats(),
        })
    provided_exists_6s = Voter.objects.filter(
        provided_to=agent,
        provided_at__gt=now() - timedelta(seconds=6),
    ).exists()
    if provided_exists_6s:
        return HttpResponse(
            'You requested a new contact too quickly', status=429,
        )
    provided_count_5m = Voter.objects.filter(
        provided_to=agent,
        provided_at__gt=now() - timedelta(minutes=5),
    ).count()
    if provided_count_5m > 25:
        agent.is_active = False
        agent.save()
        return HttpResponse(
            'You requested too many contacts recently', status=429,
        )
    with transaction.atomic():
        if id:
            voter = Voter.objects.select_for_update(skip_locked=True).get(
                id=id,
            )
            if voter.provided_to is not None:
                return HttpResponse('Contact previously assigned', status=403)
        else:
            voter = Voter.objects.select_for_update(skip_locked=True).filter(
                provided_to__isnull=True,
            ).order_by('-priority').first()
            if voter is None:
                if Voter.objects.exists():
                    return HttpResponse('Contacts are completed', status=404)
                else:
                    return HttpResponse('There are no contacts', status=404)
        voter.provided_to = agent
        voter.provided_at = now()
        voter.save()
        response = JsonResponse({
            'voter': voter.to_dict(),
            'similar_voters':
                [v.to_dict() for v in voter.find_similar_voters()],
            'agent_stats': agent.print_stats(),
        })
        phones = voter.map_phones().values()
        register_telnyx_call(phones)
        return response
