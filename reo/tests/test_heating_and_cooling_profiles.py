import json
import copy
import os
import pandas as pd
from tastypie.test import ResourceTestCaseMixin
from reo.nested_to_flat_output import nested_to_flat
from unittest import TestCase  # have to use unittest.TestCase to get tests to store to database, django.test.TestCase flushes db
from unittest import skip
from reo.models import ModelManager
from reo.utilities import check_common_outputs
from reo.validators import ValidateNestedInput
from reo.src.wind import WindSAMSDK, combine_wind_files


post = {"Scenario": {
    "timeout_seconds": 420,
    "optimality_tolerance_techs": 0.7,
    "Site": {
    "latitude": 37.78, "longitude": -122.45,
    "Financial": {
        "om_cost_escalation_pct": 0.01,
        "escalation_pct": 0.006,
        "offtaker_discount_pct": 0.07,
        "analysis_years": 25,
        "offtaker_tax_pct": 0.0
    },
    "LoadProfile": {
        "doe_reference_name": "Hospital",
    },
    "LoadProfileBoilerFuel": {
        "doe_reference_name": "LargeOffice",
    },
    "ElectricTariff": {
        "urdb_label": '5cef0a415457a33576f60fe2',
        #"eia": '14328', # May not be setup to take this input
        #"urdb_rate_name": "E-19 Medium General Demand TOU",
        #"blended_monthly_rates_us_dollars_per_kwh": [0.09] * 12,
        #"blended_monthly_demand_charges_us_dollars_per_kw": [22] * 12,
        "net_metering_limit_kw": 1e6,
        "wholesale_rate_us_dollars_per_kwh": 0
    },
    "FuelTariff": {
        "existing_boiler_fuel_type": "natural_gas",
        "boiler_fuel_blended_monthly_rates_us_dollars_per_mmbtu": [11.0]*12,
        "chp_fuel_type": "natural_gas",
        "chp_fuel_blended_monthly_rates_us_dollars_per_mmbtu": [11.0]*12
    },
    "Storage": {
        "max_kwh": 0,
        "max_kw": 0,
        "installed_cost_us_dollars_per_kw": 1000,
        "installed_cost_us_dollars_per_kwh": 500,
        "replace_cost_us_dollars_per_kw": 460,
        "replace_cost_us_dollars_per_kwh": 230,
        "macrs_option_years": 0,
    },
    "LoadProfileChillerThermal": {
        "doe_reference_name": "LargeOffice",
    },
    "ElectricChiller": {
    },
    "Boiler": {
        "boiler_efficiency": 0.8,
        "existing_boiler_production_type_steam_or_hw": "steam",
    },
    "ColdTES": {
        "min_gal": 0,
        "max_gal": 0,
        "installed_cost_us_dollars_per_gal": 3,
        "thermal_decay_rate_fraction": 0.004,
        "om_cost_us_dollars_per_gal": 0,
        "internal_efficiency_pct": 0.97,
    },
    "HotTES": {
        "min_gal": 0,
        "max_gal": 0,
        "installed_cost_us_dollars_per_gal": 3,
        "thermal_decay_rate_fraction": 0.004,
        "om_cost_us_dollars_per_gal": 0,
        "internal_efficiency_pct": 0.97,
    }
}}}

class HeatingCoolingTest(ResourceTestCaseMixin, TestCase):
    REopt_tol = 1e-2

    def setUp(self):
        super(HeatingCoolingTest, self).setUp()
        self.reopt_base = '/v1/job/'

    def get_response(self, data):

        return self.api_client.post(self.reopt_base, format='json', data=data)

    #@skip("CHP test")
    def test_heating_cooling_inputs(self):
        
        resp = self.get_response(data=post)
        self.assertHttpCreated(resp)
        r = json.loads(resp.content)
        run_uuid = r.get('run_uuid')
        d = ModelManager.make_response(run_uuid=run_uuid)
        self.assertEqual(round(d['outputs']['Scenario']['Site']['LoadProfileBoilerFuel']['annual_calculated_boiler_fuel_load_mmbtu_bau'],-1), 2900)
        self.assertEqual(round(sum(d['outputs']['Scenario']['Site']['LoadProfileBoilerFuel']['year_one_boiler_fuel_load_series_mmbtu_per_hr']),-1), 2900)
        self.assertEqual(round(d['outputs']['Scenario']['Site']['LoadProfileChillerThermal']['annual_calculated_kwh_bau'],-1),297490)
        self.assertEqual(round(sum(d['outputs']['Scenario']['Site']['LoadProfileChillerThermal']['year_one_chiller_electric_load_series_kw_bau']),-1), 297490)

        post['Scenario']['Site']['LoadProfileBoilerFuel']['doe_reference_name'] = None
        post['Scenario']['Site']['LoadProfileChillerThermal']['doe_reference_name'] = None        
        resp = self.get_response(data=post)
        self.assertHttpCreated(resp)
        r = json.loads(resp.content)
        run_uuid = r.get('run_uuid')
        d = ModelManager.make_response(run_uuid=run_uuid)
        self.assertEqual(round(d['outputs']['Scenario']['Site']['LoadProfileBoilerFuel']['annual_calculated_boiler_fuel_load_mmbtu_bau'],-1), 0)
        self.assertEqual(round(sum(d['outputs']['Scenario']['Site']['LoadProfileBoilerFuel']['year_one_boiler_fuel_load_series_mmbtu_per_hr']),-1),0)
        self.assertEqual(round(d['outputs']['Scenario']['Site']['LoadProfileChillerThermal']['annual_calculated_kwh_bau'],-1),0)
        self.assertEqual(round(sum(d['outputs']['Scenario']['Site']['LoadProfileChillerThermal']['year_one_chiller_electric_load_series_kw_bau']),-1), 0)

        post['Scenario']['Site']['LoadProfileBoilerFuel']['annual_mmbtu'] = 1000
        post['Scenario']['Site']['LoadProfileChillerThermal']['annual_fraction'] = 0.5
        resp = self.get_response(data=post)
        self.assertHttpCreated(resp)
        r = json.loads(resp.content)
        run_uuid = r.get('run_uuid')
        d = ModelManager.make_response(run_uuid=run_uuid)
        self.assertEqual(round(d['outputs']['Scenario']['Site']['LoadProfileBoilerFuel']['annual_calculated_boiler_fuel_load_mmbtu_bau'],-1), 1000)
        self.assertEqual(round(sum(d['outputs']['Scenario']['Site']['LoadProfileBoilerFuel']['year_one_boiler_fuel_load_series_mmbtu_per_hr']),-1),1000)
        self.assertEqual(round(d['outputs']['Scenario']['Site']['LoadProfileChillerThermal']['annual_calculated_kwh_bau'],-1), round(d['outputs']['Scenario']['Site']['LoadProfile']['annual_calculated_kwh'],-1)* 0.5)
        self.assertEqual(round(sum(d['outputs']['Scenario']['Site']['LoadProfileChillerThermal']['year_one_chiller_electric_load_series_kw_bau']),-1), 3876410)

        post['Scenario']['Site']['LoadProfileBoilerFuel']['annual_mmbtu'] = None
        post['Scenario']['Site']['LoadProfileChillerThermal']['annual_fraction'] = None
        post['Scenario']['Site']['LoadProfileBoilerFuel']['monthly_mmbtu'] = [1000]*12
        post['Scenario']['Site']['LoadProfileChillerThermal']['monthly_fraction'] = [0.1] * 12
        resp = self.get_response(data=post)
        self.assertHttpCreated(resp)
        r = json.loads(resp.content)
        run_uuid = r.get('run_uuid')
        d = ModelManager.make_response(run_uuid=run_uuid)
        self.assertEqual(round(d['outputs']['Scenario']['Site']['LoadProfileBoilerFuel']['annual_calculated_boiler_fuel_load_mmbtu_bau'],-1), 12000)
        self.assertEqual(round(sum(d['outputs']['Scenario']['Site']['LoadProfileBoilerFuel']['year_one_boiler_fuel_load_series_mmbtu_per_hr']),-1), 12000)
        self.assertEqual(round(d['outputs']['Scenario']['Site']['LoadProfileChillerThermal']['annual_calculated_kwh_bau'] - (d['outputs']['Scenario']['Site']['LoadProfile']['annual_calculated_kwh']* 0.1),-1),0)
        self.assertEqual(round(sum(d['outputs']['Scenario']['Site']['LoadProfileChillerThermal']['year_one_chiller_electric_load_series_kw_bau']),-1), 775280)

        post['Scenario']['Site']['LoadProfileBoilerFuel']['annual_calculated_boiler_fuel_load_mmbtu_bau'] = None
        post['Scenario']['Site']['LoadProfileChillerThermal']['annual_fraction'] = None
        post['Scenario']['Site']['LoadProfileBoilerFuel']['monthly_totals_kwh'] = None
        post['Scenario']['Site']['LoadProfileChillerThermal']['monthly_fraction'] = None
        post['Scenario']['Site']['LoadProfileBoilerFuel']['loads_mmbtu_per_hour'] = [1]*8760
        post['Scenario']['Site']['LoadProfileChillerThermal']['loads_fraction'] = [0.01]*8760
        resp = self.get_response(data=post)
        self.assertHttpCreated(resp)
        r = json.loads(resp.content)
        run_uuid = r.get('run_uuid')
        d = ModelManager.make_response(run_uuid=run_uuid)
        self.assertEqual(round(d['outputs']['Scenario']['Site']['LoadProfileBoilerFuel']['annual_calculated_boiler_fuel_load_mmbtu_bau'],-1), 8760)
        self.assertEqual(round(sum(d['outputs']['Scenario']['Site']['LoadProfileBoilerFuel']['year_one_boiler_fuel_load_series_mmbtu_per_hr']),-1),8760)
        self.assertEqual(round(d['outputs']['Scenario']['Site']['LoadProfileChillerThermal']['annual_calculated_kwh_bau'] - (d['outputs']['Scenario']['Site']['LoadProfile']['annual_calculated_kwh']* 0.01),-1),0)
        self.assertEqual(round(sum(d['outputs']['Scenario']['Site']['LoadProfileChillerThermal']['year_one_chiller_electric_load_series_kw_bau']),-1), 77530.0)