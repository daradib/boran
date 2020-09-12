from django.conf import settings
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.utils.timezone import now

from phonebank.models import Agent, Voter


def get_agent(request):
    try:
        key = request.GET['key']
    except KeyError:
        raise KeyError('Missing key parameter')
    try:
        return Agent.objects.get(uuid=key)
    except Agent.DoesNotExist:
        raise KeyError('Invalid key parameter')


def phonebank_view(request):
    try:
        agent = get_agent(request)
    except KeyError as e:
        return HttpResponse(e, status=403)
    return render(request, 'phonebank/index.html', {
        'google_form_url': settings.SECRETS['GOOGLE_FORM_URL'],
        'jitsi_room': agent.room_name,
        'sentry_dsn': settings.SECRETS['SENTRY_DSN'],
        'telnyx_token': agent.telnyx_token
    })


def api_view(request, id=None):
    try:
        agent = get_agent(request)
    except KeyError as e:
        return HttpResponse(e, status=403)
    with transaction.atomic():
        if id:
            voter = Voter.objects.select_for_update().get(id=id)
        else:
            voter = Voter.objects.select_for_update().filter(
                provided_to__isnull=True,
            ).exclude(
                anyphone__exact='', landphone__exact='',
                report_cellphone__exact='', niac_cellphone__exact='',
            ).order_by('?').first()
        voter.provided_to = agent
        voter.provided_at = now()
        voter.save()
    phone_numbers = set(voter.map_phones().values())
    similar_voters = (
        Voter.objects.filter(anyphone__in=phone_numbers)
        | Voter.objects.filter(landphone__in=phone_numbers)
        | Voter.objects.filter(report_cellphone__in=phone_numbers)
        | Voter.objects.filter(niac_cellphone__in=phone_numbers)
    ).exclude(id=voter.id)
    return JsonResponse({
        'voter': voter.to_dict(),
        'similar_voters': [v.to_dict() for v in similar_voters]
    })
