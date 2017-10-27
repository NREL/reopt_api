import copy
import json
import numpy as np
import pickle
from django.test import TestCase
from tastypie.test import ResourceTestCaseMixin
from reo.validators import REoptResourceValidation
from reo.api_definitions import default_load_profiles, default_load_monthly, default_latitudes, default_longitudes,\
    default_urdb_rate, default_demand_charge, default_blended_rate, inputs
import csv

def u2s(d):
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
        self.invalid_urdb_url = '/reopt/invalid_urdb/'
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

        missing_tier_data = copy.copy(data)
        missing_tier_data['urdb_rate']['energyratestructure'][1].append({'rate':0.12})
        text = "Missing 'max' tag for 1 tiers in rate 1 for energyratestructure"
        self.check_data_error_response(missing_tier_data, text)
        

        data['urdb_rate']['flatdemandmonths'] = [0]
        data['urdb_rate']['flatdemandstructure']=[{}]
        text = "Entry 0 flatdemandmonths does not contain 12 entries"
        self.check_data_error_response(data,text)
       
        data['urdb_rate'] =self.missing_rate_urdb
        text = "Missing rate/sell/adj attributes for tier 0 in rate 0 energyratestructure"
        self.check_data_error_response(data,text)
        
        invalid_list = json.loads(self.api_client.get(self.invalid_urdb_url,format='json').content)['Invalid IDs']
        self.assertTrue(data['urdb_rate']['label'] in invalid_list)

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

                     self.assertTrue(u2s(self.deserialize(resp)) in possible_messages )

    def test_required_fields(self):
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

    def check_common_outputs(self, d_calculated, d_expected):

        c = d_calculated
        e = d_expected

        # check all calculated keys against the expected
        for key, value in e.iteritems():
            tolerance = self.REopt_tol
            if key == 'npv':
                tolerance = 2 * self.REopt_tol

            if key in c:
                self.assertTrue((float(c[key]) - e[key]) / e[key] < tolerance)

        # Total LCC BAU is sum of utility costs
        self.assertTrue((float(c['lcc_bau']) - float(c['total_energy_cost_bau']) - float(c['total_min_charge_adder'])
                         - float(c['total_demand_cost_bau']) - float(c['total_fixed_cost_bau'])) / float(c['lcc_bau']) < self.REopt_tol)

    def test_complex_incentives(self):
        #  Tests scenario where: PV has ITC, federal, state, local rebate with maxes, MACRS, bonus, Battery has ITC, rebate, MACRS, bonus.

        null = None
        true = True
        data = {"pv_pbi_system_max":10,"roof_area":5000.0,"pv_ibi_state":0.2,"batt_soc_min":null,"offtaker_discount_rate":null,"owner_tax_rate":null,"pv_itc_federal":0.3,"batt_can_gridcharge":true,"array_type":1,"pv_ibi_utility":0.1,"batt_replacement_cost_kwh":null,"pv_itc_federal_max":null,"losses":0.14,"pv_rebate_utility":50,"pv_kw_max":null,"pv_rebate_federal":100,"analysis_period":null,"pv_rebate_state":200,"offtaker_tax_rate":null,"pv_macrs_schedule":5,"load_profile_name":"RetailStore","load_size":10000000.0,"batt_itc_total":null,"pv_rebate_federal_max":null,"batt_soc_init":null,"longitude":-118.1164613,"batt_kw_max":null,"pv_pbi":0.0,"batt_inverter_efficiency":null,"owner_discount_rate":null,"batt_efficiency":null,"batt_kwh_max":null,"azimuth":null,"pv_ibi_state_max":10000,"batt_macrs_schedule":5,"dc_ac_ratio":null,"batt_replacement_year_kwh":null,"latitude":34.5794343,"batt_replacement_year_kw":null,"module_type":1,"batt_rebate_total":100,"batt_kw_min":null,"tilt":null,"rate_escalation":null,"batt_cost_kw":null,"pv_kw_min":null,"pv_pbi_max":null,"pv_pbi_years":null,"land_area":1.0,"pv_ibi_utility_max":10000,"net_metering_limit":0,"pv_rebate_utility_max":null,"pv_rebate_state_max":null,"urdb_rate":{"sector":"Commercial","peakkwcapacitymax":200,"utility":"SouthernCaliforniaEdisonCo","peakkwcapacityhistory":12,"energyratestructure":[[{"rate":0.0712,"unit":"kWh"}],[{"rate":0.09368,"unit":"kWh"}],[{"rate":0.066,"unit":"kWh"}],[{"rate":0.08888,"unit":"kWh"}],[{"rate":0.1355,"unit":"kWh"}]],"energyweekendschedule":[[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2],[2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2],[2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2],[2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]],"demandweekendschedule":[[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]],"demandrateunit":"kW","flatdemandstructure":[[{"rate":13.2}]],"startdate":1433116800,"phasewiring":"SinglePhase","source":"http://www.sce.com/NR/sc3/tm2/pdf/ce30-12.pdf","label":"55fc81d7682bea28da64f9ae","flatdemandunit":"kW","eiaid":17609,"voltagecategory":"Primary","fixedmonthlycharge":259.2,"revisions":[1433408708,1433409358,1433516188,1441198316,1441199318,1441199417,1441199824,1441199996,1454521683],"demandweekdayschedule":[[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,1,1,1,1,2,2,2,2,2,2,1,1,1,1,1,0],[0,0,0,0,0,0,0,0,1,1,1,1,2,2,2,2,2,2,1,1,1,1,1,0],[0,0,0,0,0,0,0,0,1,1,1,1,2,2,2,2,2,2,1,1,1,1,1,0],[0,0,0,0,0,0,0,0,1,1,1,1,2,2,2,2,2,2,1,1,1,1,1,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]],"voltageminimum":2000,"description":"-Energytieredcharge=generationcharge+deliverycharge\r\n\r\n-Timeofdaydemandcharges(generation-based)aretobeaddedtothemonthlydemandcharge(Deliverybased).","energyattrs":[{"VoltageDiscount(2KV-<50KV)":"$-0.00106/Kwh"},{"VoltageDiscount(>50KV<220KV)":"$-0.00238/Kwh"},{"VoltageDiscountat220KV":"$-0.0024/Kwh"},{"CaliforniaClimatecredit":"$-0.00669/kwh"}],"energyweekdayschedule":[[0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],[0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],[0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],[0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],[0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],[2,2,2,2,2,2,2,2,3,3,3,3,4,4,4,4,4,4,3,3,3,3,3,2],[2,2,2,2,2,2,2,2,3,3,3,3,4,4,4,4,4,4,3,3,3,3,3,2],[2,2,2,2,2,2,2,2,3,3,3,3,4,4,4,4,4,4,3,3,3,3,3,2],[2,2,2,2,2,2,2,2,3,3,3,3,4,4,4,4,4,4,3,3,3,3,3,2],[0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],[0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],[0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0]],"flatdemandmonths":[0,0,0,0,0,0,0,0,0,0,0,0],"approved":true,"enddate":1451520000,"name":"TimeofUse,GeneralService,DemandMetered,OptionB:GS-2TOUB,SinglePhase","country":"USA","uri":"http://en.openei.org/apps/IURDB/rate/view/55fc81d7682bea28da64f9ae","voltagemaximum":50000,"peakkwcapacitymin":20,"demandattrs":[{"FaciltiesVoltageDiscount(2KV-<50KV)":"$-0.18/KW"},{"FaciltiesVoltageDiscount>50kV-<220kV":"$-5.78/KW"},{"FaciltiesVoltageDiscount>220kV":"$-9.96/KW"},{"TimeVoltageDiscount(2KV-<50KV)":"$-0.70/KW"},{"TimeVoltageDiscount>50kV-<220kV":"$-1.93/KW"},{"TimeVoltageDiscount>220kV":"$-1.95/KW"}],"demandratestructure":[[{"rate":0}],[{"rate":5.3}],[{"rate":18.11}]]},"pv_cost":null,"om_cost_growth_rate":null,"batt_kwh_min":null,"batt_replacement_cost_kw":null,"batt_rectifier_efficiency":null,"pv_om":null,"batt_cost_kwh":null}

        resp = self.api_client.post(self.url_base, format='json', data=data)
        self.assertHttpCreated(resp)
        d_calculated = json.loads(resp.content).get('outputs')

        d_expected = dict()
        d_expected['lcc'] = 10950029
        d_expected['npv'] = 11276785 - d_expected['lcc']
        d_expected['pv_kw'] = 216.667
        d_expected['batt_kw'] = 106.055
        d_expected['batt_kwh'] = 307.971
        d_expected['year_one_utility_kwh'] = 9621290

        try:
            self.check_common_outputs(d_calculated, d_expected)
        except:
            print("Run {} expected outputs may have changed. Check the Outputs folder.".format(d_calculated.get('uuid')))
            raise

    def test_valid_test_defaults(self):

        swaps = [['urdb_rate'], ['demand_charge', 'blended_utility_rate']]
        null = None
        data = {"losses":null,"roof_area":5000.0,"owner_tax_rate":null,"pv_itc_federal":null,"batt_can_gridcharge":True,"load_profile_name":"RetailStore","batt_replacement_cost_kwh":null,"pv_rebate_state_max":null,"pv_rebate_utility":null,"pv_ibi_utility":null,"pv_rebate_federal":null,"analysis_period":null,"pv_rebate_state":null,"offtaker_tax_rate":null,"pv_macrs_schedule":5,"pv_kw_max":null,"load_size":10000000.0,"tilt":null,"batt_kwh_max":null,"pv_rebate_federal_max":null,"batt_replacement_cost_kw":null,"batt_rebate_total":null,"longitude":-118.1164613,"pv_ibi_state":null,"batt_kw_max":null,"pv_pbi":null,"batt_inverter_efficiency":null,"offtaker_discount_rate":null,"batt_efficiency":null,"batt_soc_min":null,"batt_macrs_schedule":5,"batt_replacement_year_kwh":null,"latitude":34.5794343,"owner_discount_rate":null,"batt_replacement_year_kw":null,"module_type":1,"batt_kw_min":null,"array_type":1,"rate_escalation":null,"batt_cost_kw":null,"pv_kw_min":null,"pv_pbi_max":null,"pv_pbi_years":null,"land_area":1.0,"dc_ac_ratio":null,"net_metering_limit":null,"batt_itc_total":null,"azimuth":null,"batt_soc_init":null,"pv_rebate_utility_max":null,"pv_ibi_utility_max":null,"pv_itc_federal_max":null,"urdb_rate":{"sector":"Commercial","peakkwcapacitymax":200,"energyweekdayschedule":[[0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],[0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],[0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],[0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],[0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],[2,2,2,2,2,2,2,2,3,3,3,3,4,4,4,4,4,4,3,3,3,3,3,2],[2,2,2,2,2,2,2,2,3,3,3,3,4,4,4,4,4,4,3,3,3,3,3,2],[2,2,2,2,2,2,2,2,3,3,3,3,4,4,4,4,4,4,3,3,3,3,3,2],[2,2,2,2,2,2,2,2,3,3,3,3,4,4,4,4,4,4,3,3,3,3,3,2],[0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],[0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],[0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0]],"demandattrs":[{"Facilties Voltage Discount (2KV-<50KV)":"$-0.18/KW"},{"Facilties Voltage Discount >50 kV-<220kV":"$-5.78/KW"},{"Facilties Voltage Discount >220 kV":"$-9.96/KW"},{"Time Voltage Discount (2KV-<50KV)":"$-0.70/KW"},{"Time Voltage Discount >50 kV-<220kV":"$-1.93/KW"},{"Time Voltage Discount >220 kV":"$-1.95/KW"}],"energyratestructure":[[{"rate":0.0712,"unit":"kWh"}],[{"rate":0.09368,"unit":"kWh"}],[{"rate":0.066,"unit":"kWh"}],[{"rate":0.08888,"unit":"kWh"}],[{"rate":0.1355,"unit":"kWh"}]],"energyweekendschedule":[[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2],[2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2],[2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2],[2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]],"demandweekendschedule":[[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]],"utility":"Southern California Edison Co","flatdemandstructure":[[{"rate":13.2}]],"startdate":1433116800,"phasewiring":"Single Phase","source":"http://www.sce.com/NR/sc3/tm2/pdf/ce30-12.pdf","label":"55fc81d7682bea28da64f9ae","flatdemandunit":"kW","eiaid":17609,"voltagecategory":"Primary","revisions":[1433408708,1433409358,1433516188,1441198316,1441199318,1441199417,1441199824,1441199996,1454521683],"demandweekdayschedule":[[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,1,1,1,1,2,2,2,2,2,2,1,1,1,1,1,0],[0,0,0,0,0,0,0,0,1,1,1,1,2,2,2,2,2,2,1,1,1,1,1,0],[0,0,0,0,0,0,0,0,1,1,1,1,2,2,2,2,2,2,1,1,1,1,1,0],[0,0,0,0,0,0,0,0,1,1,1,1,2,2,2,2,2,2,1,1,1,1,1,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]],"voltageminimum":2000,"description":"- Energy tiered charge = generation charge + delivery charge\r\n\r\n- Time of day demand charges (generation-based) are to be added to the monthly demand charge(Delivery based).","energyattrs":[{"Voltage Discount (2KV-<50KV)":"$-0.00106/Kwh"},{"Voltage Discount (>50 KV<220 KV)":"$-0.00238/Kwh"},{"Voltage Discount at 220 KV":"$-0.0024/Kwh"},{"California Climate credit":"$-0.00669/kwh"}],"demandrateunit":"kW","flatdemandmonths":[0,0,0,0,0,0,0,0,0,0,0,0],"approved":True,"fixedmonthlycharge":259.2,"enddate":1451520000,"name":"Time of Use, General Service, Demand Metered, Option B: GS-2 TOU B, Single Phase","country":"USA","uri":"http://en.openei.org/apps/IURDB/rate/view/55fc81d7682bea28da64f9ae","voltagemaximum":50000,"peakkwcapacitymin":20,"peakkwcapacityhistory":12,"demandratestructure":[[{"rate":0}],[{"rate":5.3}],[{"rate":18.11}]]},"pv_cost":null,"om_cost_growth_rate":null,"batt_kwh_min":null,"pv_ibi_state_max":null,"pv_pbi_system_max":null,"batt_rectifier_efficiency":null,"pv_om":null,"batt_cost_kwh":null,"crit_load_factor":1.0}

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
                d_calculated = json.loads(resp.content).get('outputs')

                d_expected = dict()
                d_expected['npv'] = 347.0
                d_expected['lcc'] = 2914
                d_expected['pv_kw'] = 0.931874
                d_expected['batt_kw'] = 0.0526852
                d_expected['batt_kwh'] = 0.0658565
                d_expected['year_one_utility_kwh'] = 1876.4764

                try:
                    self.check_common_outputs(d_calculated, d_expected)
                except:
                    print("Run {} expected outputs may have changed. Check the Outputs folder.".format(d_calculated.get('uuid')))
                    raise
            else:
                resp = self.api_client.post(self.url_base, format='json', data=data)
                self.assertHttpCreated(resp)
                d_calculated = json.loads(resp.content).get('outputs')

                d_expected = dict()
                d_expected['lcc'] = 12703930
                d_expected['npv'] = 332951
                d_expected['pv_kw'] = 216.667
                d_expected['batt_kw'] = 105.995
                d_expected['batt_kwh'] = 307.14
                d_expected['year_one_utility_kwh'] = 9626472.7392

                try:
                    self.check_common_outputs(d_calculated, d_expected)
                except:
                    print("Run {} expected outputs may have changed. Check the Outputs folder.".format(d_calculated.get('uuid')))
                    raise


    def test_valid_data_types(self):

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

    def test_valid_data_ranges(self):
        # Test Bad Data Types
        checks = set(['min','max','minpct','maxpct','restrict'])
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

    def test_wind(self):
        """
        Validation run for wind scenario that matches REopt desktop results as of 9/26/17.
        Note no tax, no ITC, no MACRS.
        :return:
        """

        wind_post = {
            "load_profile_name": "MediumOffice", "load_size": 10000000,
            "latitude": 39.91065, "longitude": -105.2348,
            "rate_escalation": 0.006, "om_cost_growth_rate": 0.001, "analysis_period": 25,
            "offtaker_tax_rate": 0.0, "offtaker_discount_rate": 0.07,
            "batt_kw_max": 0, "batt_kwh_max": 0, "net_metering_limit": 1e6, "pv_kw_max": 0,
            "demand_charge": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            "blended_utility_rate": [0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2],
            "wind_kw_max": 10000,  "wind_macrs_schedule": 0, "wind_macrs_bonus_fraction": 0.0, "wind_itc_federal": 0
        }

        d_expected = dict()
        d_expected['lcc'] = 9849424
        d_expected['npv'] = 14861356
        d_expected['wind_kw'] = 4077.9
        d_expected['average_annual_energy_exported_wind'] = 5751360
        d_expected['net_capital_costs_plus_om'] = 9835212

        resp = self.api_client.post(self.url_base, format='json', data=wind_post)
        self.assertHttpCreated(resp)
        d_calculated = json.loads(resp.content).get('outputs')

        self.check_common_outputs(d_calculated, d_expected)
