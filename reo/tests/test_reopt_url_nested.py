import json
import pickle
from tastypie.test import ResourceTestCaseMixin
from reo.nested_inputs import nested_input_definitions
from reo.validators import ValidateNestedInput
from reo.nested_to_flat_output import nested_to_flat
from unittest import TestCase  # have to use unittest.TestCase to get tests to store to database, django.test.TestCase flushes db
from reo.models import ModelManager
from reo.nested_inputs import flat_to_nested


class EntryResourceTest(ResourceTestCaseMixin, TestCase):

    REopt_tol = 1e-2

    def setUp(self):
        super(EntryResourceTest, self).setUp()

        self.data_definitions = nested_input_definitions
        self.reopt_base = '/api/v1/reopt/'
        self.missing_rate_urdb = pickle.load(open('reo/tests/missing_rate.p','rb'))
        self.missing_schedule_urdb = pickle.load(open('reo/tests/missing_schedule.p','rb'))

    @property
    def complete_valid_nestedpost(self):
        return json.load(open('reo/tests/nestedPOST.json'))

    def make_url(self,string):
        return self.reopt_base + string

    def get_response(self, data):
        return self.api_client.post(self.reopt_base, format='json', data=data)

    def check_data_error_response(self, data, text):
        response = self.get_response(data)
        self.assertTrue(text in response.content)

    def check_common_outputs(self, d_calculated, d_expected):

        c = d_calculated
        e = d_expected

        # check all calculated keys against the expected
        for key, value in e.iteritems():
            tolerance = self.REopt_tol
            if key == 'npv':
                tolerance = 2 * self.REopt_tol

            if key in c and key in e:
                if e[key] == 0:
                    self.assertEqual(c[key], e[key])
                else:
                    self.assertTrue(abs((float(c[key]) - e[key]) / e[key]) < tolerance)

        # Total LCC BAU is sum of utility costs
        self.assertTrue(abs((float(c['lcc_bau']) - float(c['total_energy_cost_bau']) - float(c['total_min_charge_adder'])
                        - float(c['total_demand_cost_bau']) - float(c['total_fixed_cost_bau'])) / float(c['lcc_bau']))
                        < self.REopt_tol)

    def test_required(self):

        required = ['latitude','longitude']

        for r in required:
            test_case = self.complete_valid_nestedpost
            del test_case['Scenario']['Site'][r]
            response = self.get_response(test_case)
            text = "Missing Required for Scenario>Site: " + r
            self.assertTrue(text in str(json.loads(response.content)['messages']['input_errors']))

        electric_tarrif_cases = [['urdb_utility_name','urdb_rate_name','urdb_response','blended_monthly_demand_charges_us_dollars_per_kw'], ['urdb_utility_name','urdb_rate_name','urdb_response','blended_monthly_rates_us_dollars_per_kwh'], ['urdb_rate_name',"urdb_response",'blended_monthly_demand_charges_us_dollars_per_kw','blended_monthly_rates_us_dollars_per_kwh']] 
        for c in electric_tarrif_cases:
            test_case = self.complete_valid_nestedpost
            for r in c:
                del test_case['Scenario']['Site']['ElectricTariff'][r]
            response = self.get_response(test_case)
            text = "Missing Required for Scenario>Site>ElectricTariff"
            self.assertTrue(text in str(json.loads(response.content)['messages']['input_errors']))

        load_profile_cases = [['doe_reference_name','annual_kwh','monthly_totals_kwh','loads_kw'],['loads_kw','monthly_totals_kwh','annual_kwh'],  ['loads_kw','doe_reference_name','annual_kwh']]
        for c in load_profile_cases:
            test_case = self.complete_valid_nestedpost
            for r in c:
                del test_case['Scenario']['Site']['LoadProfile'][r]
            response = self.get_response(test_case)
            text = "Missing Required for Scenario>Site>LoadProfile"
            self.assertTrue(text in str(json.loads(response.content)['messages']['input_errors']))

    def test_valid_data_types(self):

        input = ValidateNestedInput(self.complete_valid_nestedpost)

        for attribute, test_data in input.test_data('type'):

            response = self.get_response(test_data)
            text = "Could not convert " + attribute

            self.assertTrue(text in str(json.loads(response.content)['messages']['input_errors']))
            self.assertTrue("(OOPS)" in str(json.loads(response.content)['messages']['input_errors']))
    
    def test_valid_data_ranges(self):

        input = ValidateNestedInput(self.complete_valid_nestedpost)

        for attribute, test_data in input.test_data('min'):
            text = "exceeds allowable min"
            response = self.get_response(test_data)
            t = json.loads(response.content)
            self.assertTrue(text in str(json.loads(response.content)['messages']['input_errors']))

        for attribute, test_data in input.test_data('max'):
                text = "exceeds allowable max"
                response = self.get_response(test_data)
                self.assertTrue(text in str(json.loads(response.content)['messages']['input_errors']))

        for attribute, test_data in input.test_data('restrict_to'):
            text = "not in allowable inputs"
            response = self.get_response(test_data)
            self.assertTrue(text in str(json.loads(response.content)['messages']['input_errors']))

    def test_urdb_rate(self):

        data = self.complete_valid_nestedpost

        data['Scenario']['Site']['ElectricTariff']['urdb_response'] = self.missing_rate_urdb
        data['Scenario']['Site']['ElectricTariff']['urdb_response']['label'] = '539f6b63ec4f024411ec9c69'
        text = "URDB Rate (label=539f6b63ec4f024411ec9c69) is currently restricted due to performance limitations"
        self.check_data_error_response(data,text)

        data['Scenario']['Site']['ElectricTariff']['urdb_response'] = self.missing_rate_urdb
        text = "Missing rate/sell/adj attributes for tier 0 in rate 0 energyratestructure"
        self.check_data_error_response(data,text)

        data['Scenario']['Site']['ElectricTariff']['urdb_response'] = self.missing_schedule_urdb

        text = 'energyweekdayschedule contains value 1 which has no associated rate in energyratestructure'
        self.check_data_error_response(data,text)

        text = 'energyweekendschedule contains value 1 which has no associated rate in energyratestructure'
        self.check_data_error_response(data,text)

    def test_complex_incentives(self):
        """
        Tests scenario where: PV has ITC, federal, state, local rebate with maxes, MACRS, bonus, Battery has ITC,
        rebate, MACRS, bonus.
        :return: None
        """

        data = {'Scenario': {'Site': {'land_acres': 1.0,
                                      'latitude': 34.5794343,
                                      'longitude': -118.1164613,
                                      'roof_squarefeet': 5000.0,
                                      'LoadProfile': {'annual_kwh': 10000000.0,
                                                      'doe_reference_name': 'RetailStore'
                                                      },
                                      'Storage': {'total_rebate_us_dollars_per_kw': 100,
                                                  'canGridCharge': True,
                                                  'macrs_option_years': 5
                                                  },
                                      'PV': {'utility_ibi_max_us_dollars': 10000,
                                             'pbi_system_max_kw': 10,
                                             'utility_ibi_pct': 0.1,
                                             'state_ibi_pct': 0.2,
                                             'state_ibi_max_us_dollars': 10000,
                                             'macrs_option_years': 5,
                                             'federal_itc_pct': 0.3,
                                             'module_type': 1,
                                             'array_type': 1,
                                             'pbi_us_dollars_per_kwh': 0.0,
                                             'utility_rebate_us_dollars_per_kw': 50,
                                             'federal_rebate_us_dollars_per_kw': 100,
                                             'state_rebate_us_dollars_per_kw': 200,
                                             },
                                      'ElectricTariff': {'net_metering_limit_kw': 0,
                                                         'urdb_response':
                                                             {'sector': 'Commercial', 'voltageminimum': 2000, 'description': '-Energytieredcharge=generationcharge+deliverycharge\r\n\r\n-Timeofdaydemandcharges(generation-based)aretobeaddedtothemonthlydemandcharge(Deliverybased).', 'peakkwcapacitymax': 200, 'energyattrs': [{'VoltageDiscount(2KV-<50KV)': '$-0.00106/Kwh'}, {'VoltageDiscount(>50KV<220KV)': '$-0.00238/Kwh'}, {'VoltageDiscountat220KV': '$-0.0024/Kwh'}, {'CaliforniaClimatecredit': '$-0.00669/kwh'}], 'enddate': 1451520000, 'peakkwcapacityhistory': 12, 'energyratestructure': [[{'rate': 0.0712, 'unit': 'kWh'}], [{'rate': 0.09368, 'unit': 'kWh'}], [{'rate': 0.066, 'unit': 'kWh'}], [{'rate': 0.08888, 'unit': 'kWh'}], [{'rate': 0.1355, 'unit': 'kWh'}]], 'flatdemandmonths': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 'energyweekdayschedule': [[0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0], [2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 3, 3, 3, 3, 3, 2], [2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 3, 3, 3, 3, 3, 2], [2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 3, 3, 3, 3, 3, 2], [2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 3, 3, 3, 3, 3, 2], [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0]], 'energyweekendschedule': [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]], 'demandweekendschedule': [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]], 'approved': True, 'utility': 'SouthernCaliforniaEdisonCo', 'flatdemandstructure': [[{'rate': 13.2}]], 'startdate': 1433116800, 'fixedmonthlycharge': 259.2, 'phasewiring': 'SinglePhase', 'name': 'TimeofUse,GeneralService,DemandMetered,OptionB:GS-2TOUB,SinglePhase', 'eiaid': 17609, 'country': 'USA', 'uri': 'http://en.openei.org/apps/IURDB/rate/view/55fc81d7682bea28da64f9ae', 'voltagemaximum': 50000, 'label': '55fc81d7682bea28da64f9ae', 'flatdemandunit': 'kW', 'source': 'http://www.sce.com/NR/sc3/tm2/pdf/ce30-12.pdf', 'voltagecategory': 'Primary', 'peakkwcapacitymin': 20, 'demandattrs': [{'FaciltiesVoltageDiscount(2KV-<50KV)': '$-0.18/KW'}, {'FaciltiesVoltageDiscount>50kV-<220kV': '$-5.78/KW'}, {'FaciltiesVoltageDiscount>220kV': '$-9.96/KW'}, {'TimeVoltageDiscount(2KV-<50KV)': '$-0.70/KW'}, {'TimeVoltageDiscount>50kV-<220kV': '$-1.93/KW'}, {'TimeVoltageDiscount>220kV': '$-1.95/KW'}], 'demandrateunit': 'kW', 'revisions': [1433408708, 1433409358, 1433516188, 1441198316, 1441199318, 1441199417, 1441199824, 1441199996, 1454521683], 'demandratestructure': [[{'rate': 0}], [{'rate': 5.3}], [{'rate': 18.11}]], 'demandweekdayschedule': [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 0], [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 0], [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 0], [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]]}
                                                         },
                                      }
                             }
                }
        resp = self.get_response(data=data)
        self.assertHttpCreated(resp)
        r = json.loads(resp.content)
        run_uuid = r.get('run_uuid')
        d = ModelManager.make_response(run_uuid=run_uuid)

        c = nested_to_flat(d['outputs'])

        d_expected = dict()
        d_expected['lcc'] = 10984555
        d_expected['npv'] = 11276785 - d_expected['lcc']
        d_expected['pv_kw'] = 216.667
        d_expected['batt_kw'] = 35.1549
        d_expected['batt_kwh'] = 66.6194
        d_expected['year_one_utility_kwh'] = 9614813.643

        try:
            self.check_common_outputs(c, d_expected)
        except:
            print("Run {} expected outputs may have changed. Check the Outputs folder.".format(run_uuid))
            print("Error message: {}".format(d['messages']))
            raise

    def test_wind(self):
        """
        Validation run for wind scenario that matches REopt desktop results as of 9/26/17.
        Note no tax, no ITC, no MACRS.
        :return:
        """

        wind_post = {'Scenario': {'Site': {
                                        'LoadProfile': {
                                           'annual_kwh': 10000000,
                                            'doe_reference_name': 'MediumOffice',
                                        },
                                        'Storage': {
                                            'max_kwh': 0,
                                            'max_kw': 0,
                                        },
                                        'latitude': 39.91065, 'longitude': -105.2348,
                                        'PV': {
                                            'max_kw': 0,
                                        },
                                        'Wind': {
                                            'macrs_bonus_pct': 0.0,
                                            'max_kw': 10000,
                                            'federal_itc_pct': 0,
                                            'macrs_option_years': 0,
                                        },
                                        'Financial': {
                                            'om_cost_escalation_pct': 0.001,
                                            'escalation_pct': 0.006,
                                            'offtaker_discount_pct': 0.07,
                                            'analysis_years': 25,
                                            'offtaker_tax_pct': 0.0,
                                        },
                                        'ElectricTariff': {
                                            'blended_monthly_demand_charges_us_dollars_per_kw': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                                            'net_metering_limit_kw': 1e6,
                                            'blended_monthly_rates_us_dollars_per_kwh': [0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2],
                                        },
        }}}

        d_expected = dict()
        d_expected['lcc'] = 9849424
        d_expected['npv'] = 14861356
        d_expected['wind_kw'] = 4077.9
        d_expected['average_annual_energy_exported_wind'] = 5751360
        d_expected['net_capital_costs_plus_om'] = 9835212

        resp = self.get_response(data=wind_post)
        self.assertHttpCreated(resp)
        r = json.loads(resp.content)
        run_uuid = r.get('run_uuid')
        d = ModelManager.make_response(run_uuid=run_uuid)
        c = nested_to_flat(d['outputs'])

        try:
            self.check_common_outputs(c, d_expected)
        except:
            print("Run {} expected outputs may have changed. Check the Outputs folder.".format(run_uuid))
            print("Error message: {}".format(d['messages']))
            raise
        
    def test_valid_nested_posts(self):

        flat_data = {"roof_area": 5000.0, "batt_can_gridcharge": True, "load_profile_name": "RetailStore", "pv_macrs_schedule": 5, "load_size": 10000000.0, "longitude": -118.1164613, "batt_macrs_schedule": 5, "latitude": 34.5794343, "module_type": 1, "array_type": 1, "land_area": 1.0, "crit_load_factor": 1.0,
                     "urdb_rate": {"sector": "Commercial", "peakkwcapacitymax": 200, "energyweekdayschedule": [[0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],[0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],[0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],[0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],[0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],[2,2,2,2,2,2,2,2,3,3,3,3,4,4,4,4,4,4,3,3,3,3,3,2],[2,2,2,2,2,2,2,2,3,3,3,3,4,4,4,4,4,4,3,3,3,3,3,2],[2,2,2,2,2,2,2,2,3,3,3,3,4,4,4,4,4,4,3,3,3,3,3,2],[2,2,2,2,2,2,2,2,3,3,3,3,4,4,4,4,4,4,3,3,3,3,3,2],[0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],[0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],[0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0]], "demandattrs": [{"Facilties Voltage Discount (2KV-<50KV)": "$-0.18/KW"},{"Facilties Voltage Discount >50 kV-<220kV": "$-5.78/KW"},{"Facilties Voltage Discount >220 kV": "$-9.96/KW"},{"Time Voltage Discount (2KV-<50KV)": "$-0.70/KW"},{"Time Voltage Discount >50 kV-<220kV": "$-1.93/KW"},{"Time Voltage Discount >220 kV": "$-1.95/KW"}], "energyratestructure": [[{"rate": 0.0712, "unit": "kWh"}],[{"rate": 0.09368, "unit": "kWh"}],[{"rate": 0.066, "unit": "kWh"}],[{"rate": 0.08888, "unit": "kWh"}],[{"rate": 0.1355, "unit": "kWh"}]], "energyweekendschedule": [[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2],[2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2],[2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2],[2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]], "demandweekendschedule": [[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]], "utility": "Southern California Edison Co", "flatdemandstructure": [[{"rate": 13.2}]], "startdate": 1433116800, "phasewiring": "Single Phase", "source": "http://www.sce.com/NR/sc3/tm2/pdf/ce30-12.pdf", "label": "55fc81d7682bea28da64f9ae", "flatdemandunit": "kW", "eiaid": 17609, "voltagecategory": "Primary", "revisions": [1433408708,1433409358,1433516188,1441198316,1441199318,1441199417,1441199824,1441199996,1454521683], "demandweekdayschedule": [[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,1,1,1,1,2,2,2,2,2,2,1,1,1,1,1,0],[0,0,0,0,0,0,0,0,1,1,1,1,2,2,2,2,2,2,1,1,1,1,1,0],[0,0,0,0,0,0,0,0,1,1,1,1,2,2,2,2,2,2,1,1,1,1,1,0],[0,0,0,0,0,0,0,0,1,1,1,1,2,2,2,2,2,2,1,1,1,1,1,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]], "voltageminimum": 2000, "description": "- Energy tiered charge = generation charge + delivery charge\r\n\r\n- Time of day demand charges (generation-based) are to be added to the monthly demand charge(Delivery based).", "energyattrs": [{"Voltage Discount (2KV-<50KV)": "$-0.00106/Kwh"},{"Voltage Discount (>50 KV<220 KV)": "$-0.00238/Kwh"},{"Voltage Discount at 220 KV": "$-0.0024/Kwh"},{"California Climate credit": "$-0.00669/kwh"}], "demandrateunit": "kW", "flatdemandmonths": [0,0,0,0,0,0,0,0,0,0,0,0], "approved": True, "fixedmonthlycharge": 259.2, "enddate": 1451520000, "name": "Time of Use, General Service, Demand Metered, Option B: GS-2 TOU B, Single Phase", "country": "USA", "uri": "http://en.openei.org/apps/IURDB/rate/view/55fc81d7682bea28da64f9ae", "voltagemaximum": 50000, "peakkwcapacitymin": 20, "peakkwcapacityhistory": 12, "demandratestructure": [[{"rate": 0}],[{"rate": 5.3}],[{"rate": 18.11}]]}}

        nested_data = flat_to_nested(flat_data)
        resp = self.get_response(data=nested_data)
        self.assertHttpCreated(resp)
        r = json.loads(resp.content)
        run_uuid = r.get('run_uuid')
        d = ModelManager.make_response(run_uuid=run_uuid)
        c = nested_to_flat(d['outputs'])

        d_expected = dict()
        d_expected['lcc'] = 11040988
        d_expected['npv'] = 235797
        d_expected['pv_kw'] = 216.667
        d_expected['batt_kw'] = 24.4715
        d_expected['batt_kwh'] = 41.2215
        d_expected['year_one_utility_kwh'] = 9614527.2568

        try:
            self.check_common_outputs(c, d_expected)
        except:
            print("Run {} expected outputs may have changed. Check the Outputs folder.".format(run_uuid))
            print("Error message: {}".format(d['messages']))
            raise

        # another test with custom rate and monthly kwh
        del flat_data['urdb_rate']
        del flat_data['load_size']
        flat_data['load_monthly_kwh'] = [100, 200, 250, 300, 350, 350, 400, 400, 350, 250, 250, 200]
        flat_data['blended_utility_rate'] = [i*2 for i in [0.05066, 0.05066, 0.05066, 0.05066, 0.05066, 0.05066, 0.05066, 0.05066, 0.05066, 0.05066, 0.05066, 0.05066]]
        flat_data['demand_charge'] = [10.00, 10.00, 10.00, 10.00, 10.00, 10.00, 10.00, 10.00, 10.00, 10.00, 10.00, 10.00]

        nested_data = flat_to_nested(flat_data)
        resp = self.get_response(data=nested_data)
        self.assertHttpCreated(resp)
        r = json.loads(resp.content)
        run_uuid = r.get('run_uuid')
        d = ModelManager.make_response(run_uuid=run_uuid)
        c = nested_to_flat(d['outputs'])

        d_expected = dict()
        d_expected['npv'] = 328.0
        d_expected['lcc'] = 2933
        d_expected['pv_kw'] = 0.915545
        d_expected['batt_kw'] = 0
        d_expected['batt_kwh'] = 0
        d_expected['year_one_utility_kwh'] = 1916.4787

        try:
            self.check_common_outputs(c, d_expected)
        except:
            print("Run {} expected outputs may have changed. Check the Outputs folder.".format(run_uuid))
            print("Error message: {}".format(c['messages']))
            raise

    def test_not_optimal_solution(self):
        data = {
            "Scenario" :{
                "Site" :{
                    "latitude": 39.91065, "longitude": -105.2348,
                    "LoadProfile" :{
                        "doe_reference_name": "MediumOffice", "annual_kwh": 10000000,
                        "outage_start_hour": 0, "outage_end_hour": 20
                    },
                    "ElectricTariff": {
                        "blended_monthly_rates_us_dollars_per_kwh": [0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2],
                        "blended_monthly_demand_charges_us_dollars_per_kw": [0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2]
                    },
                    "Storage": {
                        "max_kw": 0
                    }
                }
            }
        }
        response = self.get_response(data=data)
        r = json.loads(response.content)
        run_uuid = r.get('run_uuid')
        d = ModelManager.make_response(run_uuid=run_uuid)
        self.assertTrue('REopt could not find an optimal solution for these inputs.' in d['messages']['error'])
