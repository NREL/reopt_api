import json
import datetime
from django.contrib.auth.models import User
from django.test import TestCase
from tastypie.test import ResourceTestCaseMixin
from reo.api_definitions import *
from reo.validators import *
import numpy as np
import pickle

class EntryResourceTest(ResourceTestCaseMixin, TestCase):

    def setUp(self):
        super(EntryResourceTest, self).setUp()

        self.required =  self.get_defaults_from_list(inputs(just_required=True))
     
        self.base_case_1 = {k:v for k,v in self.required.items() if k not in ['load_8760_kw', 'blended_utility_rate','demand_charge']}
        self.base_case_1['load_size'] = 10000	

        self.url_base = '/api/v1/reopt/'

    def get_defaults_from_list(self, list):
        base = {k: inputs(full_list=True)[k].get('default') for k in list}
        base['user_id'] = 'abc321'
        if 'load_8760_kw' in list:
            base['load_8760_kw'] = [0] * 8760
        if 'load_profile_name' in list:
            base['load_profile_name'] = default_load_profiles()[0]
        if 'latitude' in list:
            base['latitude'] = default_latitudes()[0]
        if 'longitude' in list:
            base['longitude'] = default_longitudes()[0]
        if 'urdb_rate' in list:
            base['urdb_rate'] = default_urdb_rate()
        if 'demand_charge' in list:
            base['demand_charge'] = default_demand_charge()
        if 'blended_utility_rate' in list:
            base['blended_utility_rate'] = default_blended_rate()
        return base

    def expected_base_case_1(self):
        return pickle.load(open('base_case_1','r'))

    def get_response(self, data):

        resp = self.api_client.post(self.url_base, format='json', data=data)
        self.assertHttpCreated(resp)
        d = self.deserialize(resp)

        return d

    def test_base_case_1(self):
        d = self.get_response(self.base_case_1)
        expected_result = self.expected_base_case_1()

        for f in ['resilience_hours_min','resilience_hours_max','resilience_hours_avg','resilience_by_timestep']:
             self.assertEqual(d[f], expected_result[f])
        
        return

    def test_outage(self):
        return

    def test_no_system(self):
        return

    def test_pv_only(self):
        return

    def test_batt_only(self):
        return

    def test_batt_and_pv(self):
        return
