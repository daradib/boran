import html
from urllib.parse import urlencode
from uuid import uuid4

from django.db import models
from django.urls import reverse
from localflavor.us.models import USStateField
import markdown
from phonenumber_field.modelfields import PhoneNumberField

from phonebank.utils import delete_telnyx_credential


class Room(models.Model):
    name = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class Agent(models.Model):
    uuid = models.SlugField(primary_key=True, default=uuid4)
    email_address = models.EmailField(unique=True)
    nickname = models.SlugField(unique=True)
    room = models.ForeignKey(
        Room, null=True, blank=True, on_delete=models.SET_NULL,
    )
    is_active = models.BooleanField(default=True)
    last_active = models.DateTimeField(null=True, blank=True)

    @property
    def provided_count(self):
        return self.voter_set.count()

    @property
    def room_name(self):
        if self.room:
            return self.room.name
        else:
            return ''

    @property
    def telnyx_credential(self):
        return TelnyxCredential.objects.filter(
            agent=self
        ).last()

    def print_stats(self):
        stats = {'count': 0, 'rank': 0, 'count_to_rank_up': 0}
        provided_counts = Voter.objects.values('provided_to').annotate(
            cnt=models.Count('provided_to'),
        ).order_by('-cnt')
        for (i, record) in enumerate(provided_counts):
            if record['provided_to'] == self.pk:
                stats['count'] = record['cnt']
                stats['rank'] = i + 1
                if i > 0:
                    stats['count_to_rank_up'] = \
                        (provided_counts[i - 1]['cnt'] - record['cnt']) or 1
                break
        s = ""
        if stats['count']:
            s = "You reached {} contacts and are ranked #{}.".format(
                stats['count'] + 1, stats['rank'],
            )
            if stats['count_to_rank_up']:
                s += " Call {} more to rank up!".format(
                    stats['count_to_rank_up'],
                )
            else:
                s += " Congrats!"
        return s

    def get_absolute_url(self):
        return reverse('index') + '?' + urlencode({'key': self.uuid})

    def __str__(self):
        return self.nickname


class TelnyxCredential(models.Model):
    id = models.SlugField(primary_key=True)
    token = models.CharField(max_length=1023, blank=True)
    agent = models.ForeignKey(
        Agent, null=True, blank=True, on_delete=models.SET_NULL
    )

    def delete(self, *args, **kwargs):
        delete_telnyx_credential(self.id)
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.id


class Voter(models.Model):
    id = models.SlugField(primary_key=True)
    statename = USStateField()
    name_last = models.CharField(max_length=127)
    name_first = models.CharField(max_length=127)
    name_middle = models.CharField(max_length=127, blank=True)
    cell_phone_1 = PhoneNumberField(blank=True, db_index=True)
    cell_phone_2 = PhoneNumberField(blank=True, db_index=True)
    land_phone_1 = PhoneNumberField(blank=True, db_index=True)
    land_phone_2 = PhoneNumberField(blank=True, db_index=True)
    notes = models.TextField(blank=True)
    priority = models.SmallIntegerField(default=0, db_index=True)
    provided_to = models.ForeignKey(
        Agent, null=True, blank=True, on_delete=models.SET_NULL
    )
    provided_at = models.DateTimeField(null=True, blank=True)

    @classmethod
    def get_phone_field_names(cls):
        return [
            f.name for f in cls._meta.get_fields()
            if isinstance(f, PhoneNumberField) and getattr(cls, f.name)
        ]

    def map_phones(self):
        return {
            f: getattr(self, f) for f in self.get_phone_field_names()
            if getattr(self, f)
        }

    def format_notes(self):
        formatted_notes = ""
        for line in self.notes.splitlines():
            if formatted_notes:
                formatted_notes += "\n"
            if line.startswith("https://"):
                formatted_notes += \
                    '<a href="{}" rel="noreferrer" target="_blank">'.format(
                        html.escape(line)
                    ) \
                    + 'More Info ' \
                    + '<i class="fa fa-external-link" aria-hidden="true">' \
                    + '</i></a>'
            else:
                formatted_notes += line.replace(' ', '&nbsp;')
        return markdown.markdown(formatted_notes, extensions=['nl2br'])

    def find_similar_voters(self):
        phone_numbers = set(self.map_phones().values())
        query = None
        for phone_field_name in self.get_phone_field_names():
            if query:
                query.add(
                    models.Q(**{phone_field_name + '__in': phone_numbers}),
                    models.Q.OR,
                )
            else:
                query = models.Q(**{phone_field_name + '__in': phone_numbers})
        return Voter.objects.filter(query).exclude(id=self.id).order_by(
            'name_last', 'name_first', 'id',
        )

    def to_name(self):
        return self.name_last + ', ' + self.name_first

    def to_dict(self):
        obj = {
            'id': self.id,
            'statename': self.statename,
            'name': self.to_name(),
            'notes': self.format_notes(),
            'provided': bool(self.provided_to_id),
        }
        obj['phones'] = ({k: v.as_e164 for k, v in self.map_phones().items()})
        return obj

    def __str__(self):
        return '{}: {}'.format(self.id, self.to_name())
