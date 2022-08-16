#!/usr/bin/env python3

import csv

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'boran.settings'
import sys
sys.path.append('.')
import django
django.setup()
from localflavor.us.us_states import STATES_NORMALIZED
import phonenumbers

from phonebank.models import Voter


with open(sys.argv[1]) as csvfile:
    reader = csv.DictReader(csvfile)
    voters = []
    for row in reader:
        obj = {}
        obj['statename'] = STATES_NORMALIZED.get(row['statename'].lower())
        if obj['statename'] is None:
            print("Skipping invalid/missing state: {}".format(row))
            continue
        for column_name in ['name_last', 'name_first', 'name_middle']:
            obj[column_name] = row[column_name]
        for column_name in Voter.get_phone_field_names():
            if row[column_name]:
                phone = phonenumbers.parse(row[column_name], 'US')
                if phonenumbers.is_valid_number_for_region(phone, 'US'):
                    obj[column_name] = phone
                else:
                    print("Ignoring invalid phone number: {}".format(
                        row[column_name]
                    ))
        voters.append(Voter(**obj))
    Voter.objects.bulk_create(voters)
