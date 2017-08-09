import json
import datetime
from django.contrib.auth.models import User
from django.test import TestCase
from tastypie.test import ResourceTestCaseMixin
from reo.api_definitions import *
from reo.validators import *
import numpy as np
import pickle

from django.db.models import signals
from tastypie.models import ApiKey

from IPython import embed

def u2s (d):
    sub_d = d['reopt']['Error']
    return {'reopt':{'Error':{str(k):[str(i) for i in v]  for k,v in sub_d.items()}}}


class EntryResourceTest(ResourceTestCaseMixin, TestCase):

    REopt_tol = 1e-2

    def setUp(self):
        super(EntryResourceTest, self).setUp()

        self.required  = inputs(just_required=True).keys()

        self.base_case_fields = ['latitude','longitude','urdb_rate','load_profile_name','load_size']

        self.optional = [["urdb_rate"],["blended_utility_rate",'demand_charge']]
     
        self.url_base = '/api/v1/reopt/'

	self.missing_rate_urdb = pickle.load(open('reo/tests/missing_rate.p','rb'))
	self.missing_schedule_urdb = pickle.load(open('reo/tests/missing_schedule.p','rb'))


    def make_url(self,string):
        return self.url_base + string

    def get_defaults_from_list(self,list):
        base = {k:inputs(full_list=True)[k].get('default') for k in list}
  
        if 'load_8760_kw' in list:
            base['load_8760_kw'] = [0]*8760
        if 'load_profile_name' in list:
            base['load_profile_name'] = default_load_profiles()[0]
        if 'load_size' in list:
            base['load_size'] = 10000
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
        base = {k:v for k,v in base.items() if v is not None}
        
        return base

    def list_to_default_string(self,list_inputs):
        output  = ""
        for f in list_inputs:
            output  += "&%s=%s" % (f,self.get_default(f))
        return output

    def request_swap_value(self,k,dummy_data,swaps,add):
        list = [i for i in self.required if i not in sum(swaps, [])] + add
        data = self.get_defaults_from_list(list)
        data[k] = dummy_data
        return self.api_client.post(self.url_base, format='json', data=data)

    def get_response(self, data):
        return self.api_client.post(self.url_base, format='json', data=data)

    def check_data_error_response(self, data, text):	
      response = self.get_response(data)
      self.assertTrue(text in response.content)

    def test_urdb_rate(self):
      data = self.get_defaults_from_list(self.base_case_fields)

      data['urdb_rate'] =self.missing_rate_urdb
      text = "Missing rate attribute for tier 0 in rate 0 energyratestructure"
      self.check_data_error_response(data,text)

      data['urdb_rate']=self.missing_schedule_urdb

      text = 'energyweekdayschedule contains value 1 which has no associated rate in energyratestructure'
      self.check_data_error_response(data,text)

      text = 'energyweekendschedule contains value 1 which has no associated rate in energyratestructure'
      self.check_data_error_response(data,text)
	

    def test_valid_swapping(self):
        swaps = [[['urdb_rate'],['demand_charge','blended_utility_rate']],[['load_profile_name'],['load_8760_kw']]]
        for sp in swaps:
            other_pairs = list(np.concatenate([i[0] for i in swaps if i!=sp ]))
            possible_messages = [{r"reopt":{"Error":{"Missing_Required": [REoptResourceValidation().get_missing_required_message(ii)]}}} for ii in sp[0]+sp[1]]
            for ss in sp:
                for f in ss:
                     dependent_fields = [i for i in ss if i != f]
                     l = [i for i in self.required if i not in sp[0]+sp[1] ] + dependent_fields + other_pairs
                     data = self.get_defaults_from_list(l)
                     resp = self.api_client.post(self.url_base, format='json', data=data) 
                    # try:
                     self.assertTrue(u2s(self.deserialize(resp)) in possible_messages )
                    # except:     
                         #embed()
    def test_required_fields(self):
        #try:
        for f in self.required:
            swaps = inputs(full_list=True)[f].get('swap_for')
            if swaps == None:
                swaps = []
            alt_field = inputs(full_list=True)[f].get('alt_field')
            if alt_field == None:
                alt_field = []
            else:
                alt_field= [alt_field]
            possible_messages = [{r"reopt":{"Error":{"Missing_Required":[REoptResourceValidation().get_missing_required_message(ii)]}}} for ii in [f]+swaps+alt_field] 
            fields = [i for i in list(set(self.required) - set([f]+swaps+alt_field)) if i != f]
            data = self.get_defaults_from_list(fields)
            resp = self.get_response(data)

            self.assertTrue(u2s(self.deserialize(resp)) in possible_messages )
        #except:
           # embed()

    def test_valid_test_defaults(self):

        swaps = [['urdb_rate'], ['demand_charge', 'blended_utility_rate']]
        null = None
        true = True
        data = {"losses": null, "roof_area": 5000.0, "batt_rebate_utility_max": null, "batt_rebate_utility": null,
                "owner_tax_rate": null, "pv_itc_federal": null, "batt_can_gridcharge": true,
                "load_profile_name": "RetailStore", "batt_replacement_cost_kwh": null, "pv_rebate_state_max": null,
                "batt_itc_utility_max": null, "batt_rebate_state_max": null, "pv_rebate_utility": null,
                "pv_itc_utility": null, "pv_rebate_federal": null, "analysis_period": null, "pv_rebate_state": null,
                "offtaker_tax_rate": null, "pv_macrs_schedule": 5, "pv_kw_max": null, "load_size": 10000000.0,
                "tilt": null, "batt_kwh_max": null, "pv_rebate_federal_max": null, "batt_replacement_cost_kw": null,
                "batt_rebate_federal": null, "longitude": -118.1164613, "pv_itc_state": null, "batt_kw_max": null,
                "pv_pbi": null, "batt_inverter_efficiency": null, "offtaker_discount_rate": null,
                "batt_efficiency": null, "batt_itc_federal_max": null, "batt_soc_min": null, "batt_itc_state_max": null,
                "batt_rebate_state": null, "batt_itc_utility": null, "batt_macrs_schedule": 5,
                "batt_replacement_year_kwh": null, "latitude": 34.5794343, "owner_discount_rate": null,
                "batt_replacement_year_kw": null, "module_type": 1, "batt_kw_min": null, "array_type": 1,
                "rate_escalation": null, "batt_cost_kw": null, "pv_kw_min": null, "pv_pbi_max": null,
                "pv_pbi_years": null, "land_area": 1.0, "dc_ac_ratio": null, "net_metering_limit": null,
                "batt_itc_state": null, "batt_itc_federal": null, "batt_rebate_federal_max": null, "azimuth": null,
                "batt_soc_init": null, "pv_rebate_utility_max": null, "pv_itc_utility_max": null,
                "pv_itc_federal_max": null, "urdb_rate": {"sector": "Commercial", "peakkwcapacitymax": 200,
                                                          "energyweekdayschedule": [
                                                              [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                                                               1, 1, 0, 0, 0],
                                                              [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                                                               1, 1, 0, 0, 0],
                                                              [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                                                               1, 1, 0, 0, 0],
                                                              [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                                                               1, 1, 0, 0, 0],
                                                              [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                                                               1, 1, 0, 0, 0],
                                                              [2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 3,
                                                               3, 3, 3, 3, 2],
                                                              [2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 3,
                                                               3, 3, 3, 3, 2],
                                                              [2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 3,
                                                               3, 3, 3, 3, 2],
                                                              [2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 3,
                                                               3, 3, 3, 3, 2],
                                                              [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                                                               1, 1, 0, 0, 0],
                                                              [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                                                               1, 1, 0, 0, 0],
                                                              [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                                                               1, 1, 0, 0, 0]], "demandattrs": [
                    {"Facilties Voltage Discount (2KV-<50KV)": "$-0.18/KW"},
                    {"Facilties Voltage Discount >50 kV-<220kV": "$-5.78/KW"},
                    {"Facilties Voltage Discount >220 kV": "$-9.96/KW"},
                    {"Time Voltage Discount (2KV-<50KV)": "$-0.70/KW"},
                    {"Time Voltage Discount >50 kV-<220kV": "$-1.93/KW"},
                    {"Time Voltage Discount >220 kV": "$-1.95/KW"}],
                                                          "energyratestructure": [[{"rate": 0.0712, "unit": "kWh"}],
                                                                                  [{"rate": 0.09368, "unit": "kWh"}],
                                                                                  [{"rate": 0.066, "unit": "kWh"}],
                                                                                  [{"rate": 0.08888, "unit": "kWh"}],
                                                                                  [{"rate": 0.1355, "unit": "kWh"}]],
                                                          "energyweekendschedule": [
                                                              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                                               0, 0, 0, 0, 0],
                                                              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                                               0, 0, 0, 0, 0],
                                                              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                                               0, 0, 0, 0, 0],
                                                              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                                               0, 0, 0, 0, 0],
                                                              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                                               0, 0, 0, 0, 0],
                                                              [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
                                                               2, 2, 2, 2, 2],
                                                              [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
                                                               2, 2, 2, 2, 2],
                                                              [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
                                                               2, 2, 2, 2, 2],
                                                              [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
                                                               2, 2, 2, 2, 2],
                                                              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                                               0, 0, 0, 0, 0],
                                                              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                                               0, 0, 0, 0, 0],
                                                              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                                               0, 0, 0, 0, 0]], "demandweekendschedule": [
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]],
                                                          "utility": "Southern California Edison Co",
                                                          "flatdemandstructure": [[{"rate": 13.2}]],
                                                          "startdate": 1433116800, "phasewiring": "Single Phase",
                                                          "source": "http://www.sce.com/NR/sc3/tm2/pdf/ce30-12.pdf",
                                                          "label": "55fc81d7682bea28da64f9ae", "flatdemandunit": "kW",
                                                          "eiaid": 17609, "voltagecategory": "Primary",
                                                          "revisions": [1433408708, 1433409358, 1433516188, 1441198316,
                                                                        1441199318, 1441199417, 1441199824, 1441199996,
                                                                        1454521683], "demandweekdayschedule": [
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]], "voltageminimum": 2000,
                                                          "description": "- Energy tiered charge = generation charge + delivery charge\r\n\r\n- Time of day demand charges (generation-based) are to be added to the monthly demand charge(Delivery based).",
                                                          "energyattrs": [
                                                              {"Voltage Discount (2KV-<50KV)": "$-0.00106/Kwh"},
                                                              {"Voltage Discount (>50 KV<220 KV)": "$-0.00238/Kwh"},
                                                              {"Voltage Discount at 220 KV": "$-0.0024/Kwh"},
                                                              {"California Climate credit": "$-0.00669/kwh"}],
                                                          "demandrateunit": "kW",
                                                          "flatdemandmonths": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                                          "approved": true, "fixedmonthlycharge": 259.2,
                                                          "enddate": 1451520000,
                                                          "name": "Time of Use, General Service, Demand Metered, Option B: GS-2 TOU B, Single Phase",
                                                          "country": "USA",
                                                          "uri": "http://en.openei.org/apps/IURDB/rate/view/55fc81d7682bea28da64f9ae",
                                                          "voltagemaximum": 50000, "peakkwcapacitymin": 20,
                                                          "peakkwcapacityhistory": 12,
                                                          "demandratestructure": [[{"rate": 0}], [{"rate": 5.3}],
                                                                                  [{"rate": 18.11}]]}, "pv_cost": null,
                "rate_inflation": null, "batt_kwh_min": null, "pv_itc_state_max": null, "pv_pbi_system_max": null,
                "batt_rectifier_efficiency": null, "pv_om": null, "batt_cost_kwh": null, "crit_load_factor": 1.0
                }

        for add in swaps:
           # Test All  Data and  Valid Rate Inputs

            if add == swaps[1]:
                del data['urdb_rate']
                del data['load_size']
                data['load_monthly_kwh'] = default_load_monthly()
                data['blended_utility_rate'] = [i*2 for i in default_blended_rate()]
                data['demand_charge'] = default_demand_charge()                    

                resp = self.api_client.post(self.url_base, format='json', data=data)
                self.assertHttpCreated(resp)
                d = json.loads(resp.content)
           
                npv = 800.0
                lcc = 2973.0
                pv_kw = 1.25342
                batt_kw = 0.208157
                batt_kwh = 0.644807
                yr_one = 1353.2225
                r_min = 0.16
                r_max = 22.44
                r_avg = 4.23

                self.assertTrue((float(d['lcc']) - lcc) / lcc < self.REopt_tol)
                self.assertTrue((float(d['npv']) - npv) / npv < self.REopt_tol * 2)  # *2 b/c npv is difference of two outputs
                self.assertTrue((float(d['pv_kw']) - pv_kw) / pv_kw < self.REopt_tol)
                self.assertTrue((float(d['batt_kw']) - batt_kw) / batt_kw < self.REopt_tol)
                self.assertTrue((float(d['batt_kwh']) - batt_kwh) / batt_kwh < self.REopt_tol)
                self.assertTrue((float(d['year_one_utility_kwh']) - yr_one) / yr_one < self.REopt_tol)
                self.assertTrue((float(d['resilience_hours_min']) - r_min) / r_min < self.REopt_tol)
                self.assertTrue((float(d['resilience_hours_max']) - r_max) / r_max < self.REopt_tol)
                self.assertTrue((float(d['resilience_hours_avg']) - r_avg) / r_avg < self.REopt_tol)
            
            else:
                resp = self.api_client.post(self.url_base, format='json', data=data)
                self.assertHttpCreated(resp)
                d = json.loads(resp.content)

                lcc = 12651213.0
                npv = 385668.0
                pv_kw = 185.798
                batt_kw = 200.866
                batt_kwh = 960.659
                yr_one_kwh = 9709753.5354
                r_min = 0.07
                r_max = 2.4
                r_avg = 0.34

                self.assertTrue((float(d['lcc']) -lcc) /lcc  < self.REopt_tol)
                self.assertTrue((float(d['npv']) - npv) / npv < self.REopt_tol * 2)  # *2 b/c npv is difference of two outputs
                self.assertTrue((float(d['pv_kw']) - pv_kw) / pv_kw < self.REopt_tol)
                self.assertTrue((float(d['batt_kw']) - batt_kw) / batt_kw < self.REopt_tol)
                self.assertTrue((float(d['batt_kwh']) - batt_kwh) / batt_kwh < self.REopt_tol)
                self.assertTrue((float(d['year_one_utility_kwh']) - yr_one_kwh) / yr_one_kwh < self.REopt_tol)
                self.assertTrue((float(d['resilience_hours_min']) - r_min)/r_min < self.REopt_tol)
                self.assertTrue((float(d['resilience_hours_max']) - r_max)/r_max < self.REopt_tol)
                self.assertTrue((float(d['resilience_hours_avg']) -  r_avg)/r_avg < self.REopt_tol)

    def test_valid_data_types(self):
        #try: 
        for k,v in inputs(full_list=True).items():
            list = self.base_case_fields
            if k not in list:
                list.append(k)

            if v.get('depends_on') is not None:
                for d in v.get('depends_on'):
                    if d not in list:
                        list.append(d)

            if v.get('swap_for') is not None:
                for s in v.get('swap_for'):
                    list = [i for i in list if i != s]
            
            data = self.get_defaults_from_list(list)

            dummy_data = 1
            if v['type'] in [bool,float,int]:
                dummy_data  = u"A"

            data[k] = dummy_data

            resp = self.get_response(data)
            self.assertEqual(u2s(self.deserialize(resp)), {r"reopt": {"Error": {k: ['Invalid format: Expected %s, got %s'%(v['type'].__name__, type(dummy_data).__name__)]}}})
       # except:
        #    embed()

    def test_valid_data_ranges(self):
        #try:
        # Test Bad Data Types
        checks  = set(['min','max','minpct','maxpct','restrict'])
        completed_checks = []

        while completed_checks != checks:
            for k, v in inputs(full_list=True).items():
       
                if v.get('min') is not None and v.get('pct') is not True:
                    dummy_data =  -1e20
                    data = self.get_defaults_from_list(self.base_case_fields)
                    data[k] = dummy_data
                    resp = self.get_response(data)
                    self.assertEqual(u2s(self.deserialize(resp)), {
                        r"reopt": {"Error": {k: ['Invalid value: %s: %s is less than the minimum, %s' % (k, dummy_data, v.get('min'))]}}})
                    completed_checks = set(list(completed_checks) + ['min'])

                if v.get('max') is not None and v.get('pct') is not True:
                    dummy_data = 1e20
                    data = self.get_defaults_from_list(self.base_case_fields)
                    data[k] = dummy_data    
                    resp = self.get_response(data)
                    self.assertEqual(u2s(self.deserialize(resp)), {
                            r"reopt": {"Error": {k: ['Invalid value: %s: %s is greater than the  maximum, %s' % (k, dummy_data, v.get('max'))]}}})
                    completed_checks = set(list(completed_checks) + ['max'])

                if v.get('min') is not None and bool(v.get('pct')):
                    dummy_data =  -1000000
                    data = self.get_defaults_from_list(self.base_case_fields)
                    data[k] = dummy_data         
                    resp = self.get_response(data)
                    self.assertEqual(u2s(self.deserialize(resp)), {
                            r"reopt": {"Error": {
                                k: ['Invalid value: %s: %s is less than the minimum, %s %%' % (k, dummy_data, v.get('min')*100)]}}})
                    completed_checks = set(list(completed_checks) + ['minpct'])

                if v.get('max') is not None and bool(v.get('pct')):
                    dummy_data = 1000000
                    data = self.get_defaults_from_list(self.base_case_fields)
                    data[k] = dummy_data          
                    resp = self.get_response(data)
                    self.assertEqual(u2s(self.deserialize(resp)), {
                            r"reopt": {"Error": {
                                k: ['Invalid value: %s: %s is greater than the  maximum, %s %%' % (k, dummy_data, v.get('max')*100)]}}})
                    completed_checks = set(list(completed_checks) + ['maxpct'])

                if bool(v.get('restrict_to')):
                     if v.get('type') in [int,float]:
                         dummy_data = -123
                     else:
                        dummy_data  =  "!@#$%^&*UI("
                     data = self.get_defaults_from_list(self.base_case_fields)
                     data[k] = dummy_data
                     resp = self.get_response(data)
                     self.assertEqual(u2s(self.deserialize(resp)), {
                        r"reopt": {
                            "Error": {k: ['Invalid value: %s: %s is not in %s' % (k, dummy_data, v.get('restrict_to'))]}}})
                     completed_checks = set(list(completed_checks) + ['restrict'])

        completed_checks = set(checks)
