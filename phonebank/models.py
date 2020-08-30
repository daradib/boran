from django.db import models
from localflavor.us.models import USStateField
from phonenumber_field.modelfields import PhoneNumberField


class Room(models.Model):
    name = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class Agent(models.Model):
    uuid = models.SlugField(primary_key=True)
    email_address = models.EmailField(unique=True)
    nickname = models.SlugField(unique=True)
    room = models.ForeignKey(
        Room, null=True, blank=True, on_delete=models.SET_NULL,
    )
    is_active = models.BooleanField(default=True)
    last_active = models.DateTimeField(null=True, blank=True)

    @property
    def room_name(self):
        if self.room:
            return self.room.name
        else:
            return ''

    @property
    def telnyx_token(self):
        return TelnyxCredential.objects.filter(
            agent=self
        ).values('token').last()['token']

    def __str__(self):
        return "{} ({})".format(self.uuid, self.nickname)


class TelnyxCredential(models.Model):
    id = models.SlugField(primary_key=True)
    token = models.CharField(max_length=1023, blank=True)
    agent = models.ForeignKey(
        Agent, null=True, blank=True, on_delete=models.SET_NULL
    )

    def __str__(self):
        return self.id


class Voter(models.Model):
    statename = USStateField()
    name_last = models.CharField(max_length=127)
    name_first = models.CharField(max_length=127)
    name_middle = models.CharField(max_length=127, blank=True)
    anyphone = PhoneNumberField(blank=True, db_index=True)
    landphone = PhoneNumberField(blank=True, db_index=True)
    report_cellphone = PhoneNumberField(blank=True, db_index=True)
    niac_cellphone = PhoneNumberField(blank=True, db_index=True)
    provided_to = models.ForeignKey(
        Agent, null=True, blank=True, on_delete=models.SET_NULL
    )
    provided_at = models.DateTimeField(null=True, blank=True)

    def map_phones(self):
        return {
            f.name: getattr(self, f.name) for f in self._meta.get_fields()
            if isinstance(f, PhoneNumberField) and getattr(self, f.name)
        }

    def to_dict(self):
        obj = {
            'id': self.id,
            'statename': self.statename,
            'name':
                ' '.join([self.name_first, self.name_middle, self.name_last]),
        }
        obj['phones'] = ({k: v.as_e164 for k, v in self.map_phones().items()})
        return obj

    def __str__(self):
        return '{}: {}, {} {}'.format(
            self.statename, self.name_last, self.name_first, self.name_middle,
        )
