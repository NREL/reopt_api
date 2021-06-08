# *********************************************************************************
# REopt, Copyright (c) 2019-2020, Alliance for Sustainable Energy, LLC.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
# Redistributions of source code must retain the above copyright notice, this list
# of conditions and the following disclaimer.
#
# Redistributions in binary form must reproduce the above copyright notice, this
# list of conditions and the following disclaimer in the documentation and/or other
# materials provided with the distribution.
#
# Neither the name of the copyright holder nor the names of its contributors may be
# used to endorse or promote products derived from this software without specific
# prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
# OF THE POSSIBILITY OF SUCH DAMAGE.
# *********************************************************************************
import json
from django.test import TestCase
from tastypie.test import ResourceTestCaseMixin
from unittest import skip
import numpy as np
from reo.utilities import annuity


class TestCoincidentPeak(ResourceTestCaseMixin, TestCase):
    """
    Tariff from Florida Light & Power (residential) with simple tiered energy rate:
    "energyratestructure":
    [[{"max": 1000, "rate": 0.07531, "adj": 0.0119, "unit": "kWh"}, {"rate": 0.09613, "adj": 0.0119, "unit": "kWh"}]]

    Testing with "annual_kwh": 24,000 such that the "year_one_energy_charges" should be:
        12,000 kWh * (0.07531 + 0.0119) $/kWh + 12,000 kWh * (0.09613 + 0.0119) $/kWh = $ 2,342.88
    """

    def setUp(self):
        super(TestCoincidentPeak, self).setUp()

        self.submit_url = '/v1/job/'
        self.results_url = '/v1/job/<run_uuid>/results/'
        self.post = {
            "Scenario": {
                "webtool_uuid": None, "description": "", "timeout_seconds": 295, "time_steps_per_hour": 1, "user_uuid": None,
                "Site": {
                    "longitude": -91.7337,
                    "latitude": 35.2468,
                    "Financial": {
                        "om_cost_escalation_pct": 0.025,
                        "escalation_pct": 0.023,
                        "offtaker_tax_pct": 0.26,
                        "offtaker_discount_pct": 0.083,
                        "analysis_years": 25,
                        "value_of_lost_load_us_dollars_per_kwh": 100,
                        "microgrid_upgrade_cost_pct": 0.3
                    },
                    "LoadProfile": {
                        "critical_loads_kw_is_net": False,
                        "year": 2020,
                        "loads_kw_is_net": True,
                        "outage_start_time_step": None,
                        "outage_end_time_step": None,
                        "critical_load_pct": 0.5,
                        "outage_is_major_event": True,
                        "doe_reference_name": "MidriseApartment"
                    },
                    "ElectricTariff": {
                        "coincident_peak_load_active_timesteps": [[1,2,100],[6000,7000]],
                        "coincident_peak_load_charge_us_dollars_per_kw": [10,5],
                        "add_blended_rates_to_urdb_rate": False,
                        "net_metering_limit_kw": 0,
                        "interconnection_limit_kw": 100000000.0,
                        "urdb_label": "5e162e2a5457a3d50873e3af"
                    },
                    "Wind": {
                        "min_kw": 0,
                        "max_kw": 0,
                        "installed_cost_us_dollars_per_kw": 3013,
                        "om_cost_us_dollars_per_kw": 40,
                        "macrs_option_years": 5,
                        "macrs_bonus_pct": 1,
                        "macrs_itc_reduction": 0.5,
                        "federal_itc_pct": 0.26,
                        "state_ibi_pct": 0,
                        "state_ibi_max_us_dollars": 10000000000.0,
                        "utility_ibi_pct": 0,
                        "utility_ibi_max_us_dollars": 10000000000.0,
                        "federal_rebate_us_dollars_per_kw": 0,
                        "state_rebate_us_dollars_per_kw": 0,
                        "state_rebate_max_us_dollars": 10000000000.0,
                        "utility_rebate_us_dollars_per_kw": 0,
                        "utility_rebate_max_us_dollars": 10000000000.0,
                        "pbi_us_dollars_per_kwh": 0,
                        "pbi_max_us_dollars": 1000000000.0,
                        "pbi_years": 1,
                        "pbi_system_max_kw": 1000000000.0
                    },
                    "PV": {
                        "pv_name": "Roof - South Face",
                        "location":"roof",
                        "existing_kw": 0,
                        "min_kw": 0,
                        "max_kw": 1000000000.0,
                        "installed_cost_us_dollars_per_kw": 1600,
                        "om_cost_us_dollars_per_kw": 16,
                        "macrs_option_years": 5,
                        "macrs_bonus_pct": 1,
                        "macrs_itc_reduction": 0.5,
                        "federal_itc_pct": 0.26,
                        "state_ibi_pct": 0,
                        "state_ibi_max_us_dollars": 10000000000.0,
                        "utility_ibi_pct": 0,
                        "utility_ibi_max_us_dollars": 10000000000.0,
                        "federal_rebate_us_dollars_per_kw": 0,
                        "state_rebate_us_dollars_per_kw": 0,
                        "state_rebate_max_us_dollars": 10000000000.0,
                        "utility_rebate_us_dollars_per_kw": 0,
                        "utility_rebate_max_us_dollars": 10000000000.0,
                        "pbi_us_dollars_per_kwh": 0,
                        "pbi_max_us_dollars": 1000000000.0,
                        "pbi_years": 1,
                        "pbi_system_max_kw": 1000000000.0,
                        "degradation_pct": 0.005,
                        "azimuth": 180,
                        "losses": 0.14,
                        "array_type": 1,
                        "module_type": 0,
                        "gcr": 0.4,
                        "dc_ac_ratio": 1.2,
                        "inv_eff": 0.96,
                        "radius": 0,
                        "tilt": 0.537
                    },
                    "Storage": {
                        "min_kw": 0,
                        "max_kw": 1000000,
                        "min_kwh": 0,
                        "max_kwh": 1000000,
                        "internal_efficiency_pct": 0.975,
                        "inverter_efficiency_pct": 0.96,
                        "rectifier_efficiency_pct": 0.96,
                        "soc_min_pct": 0.2,
                        "soc_init_pct": 0.5,
                        "canGridCharge": True,
                        "installed_cost_us_dollars_per_kw": 840,
                        "installed_cost_us_dollars_per_kwh": 420,
                        "replace_cost_us_dollars_per_kw": 410,
                        "replace_cost_us_dollars_per_kwh": 200,
                        "inverter_replacement_year": 10,
                        "battery_replacement_year": 10,
                        "macrs_option_years": 7,
                        "macrs_bonus_pct": 1,
                        "macrs_itc_reduction": 0.5,
                        "total_itc_pct": 0.0,
                        "total_rebate_us_dollars_per_kw": 0
                    },
                    "Generator": {
                        "existing_kw": 0,
                        "min_kw": 0,
                        "max_kw": 1000000000.0,
                        "installed_cost_us_dollars_per_kw": 500,
                        "om_cost_us_dollars_per_kw": 10,
                        "om_cost_us_dollars_per_kwh": 0.0,
                        "diesel_fuel_cost_us_dollars_per_gallon": 3,
                        "fuel_slope_gal_per_kwh": 0.076,
                        "fuel_intercept_gal_per_hr": 0,
                        "fuel_avail_gal": 660,
                        "min_turn_down_pct": 0,
                        "generator_only_runs_during_grid_outage": True,
                        "generator_sells_energy_back_to_grid": False,
                        "macrs_option_years": 0,
                        "macrs_bonus_pct": 1,
                        "macrs_itc_reduction": 0,
                        "federal_itc_pct": 0,
                        "state_ibi_pct": 0,
                        "state_ibi_max_us_dollars": 0,
                        "utility_ibi_pct": 0,
                        "utility_ibi_max_us_dollars": 0,
                        "federal_rebate_us_dollars_per_kw": 0,
                        "state_rebate_us_dollars_per_kw": 0,
                        "state_rebate_max_us_dollars": 0,
                        "utility_rebate_us_dollars_per_kw": 0,
                        "utility_rebate_max_us_dollars": 0,
                        "pbi_us_dollars_per_kwh": 0,
                        "pbi_max_us_dollars": 0,
                        "pbi_years": 0,
                        "pbi_system_max_kw": 0
                    }
                },
                "timeout_seconds": 295,
                "time_steps_per_hour": 1
            }
        }

    def get_response(self, data):
        initial_post = self.api_client.post(self.submit_url, format='json', data=data)
        postjsoncontent = json.loads(initial_post.content)
        try:
            uuid = postjsoncontent['run_uuid']
        except Exception as e:
            error_msg = postjsoncontent['messages']['error']
            print("test_coincident_peak API error message: {}".format(error_msg))
            raise e
        response = json.loads(self.api_client.get(self.results_url.replace('<run_uuid>', str(uuid))).content)
        return response

    def test_coincident_peak(self):
        response = self.get_response(data=self.post)
        messages = response['messages']
        tariff_out = response['outputs']['Scenario']['Site']['ElectricTariff']
        demand = np.array(tariff_out['year_one_to_battery_series_kw']) + np.array(tariff_out['year_one_to_load_series_kw'])
        tariff_in = response['inputs']['Scenario']['Site']['ElectricTariff']
        cp_timesteps = tariff_in["coincident_peak_load_active_timesteps"]
        cp_rates = tariff_in["coincident_peak_load_charge_us_dollars_per_kw"]
        fin_in = response['inputs']['Scenario']['Site']['Financial']
        cp_charge_expected_yr1 = 0
        if type(cp_rates) is list:
            cp_periods = len(cp_rates)
            for p in range(cp_periods):
                cp_peak_demand = max([demand[int(ts-1)] for ts in list(filter(None,cp_timesteps[p]))])
                cp_charge_expected_yr1 += cp_rates[p] * cp_peak_demand
        else:
            cp_peak_demand = max([demand[int(ts-1)] for ts in list(filter(None,cp_timesteps))])
            cp_charge_expected_yr1 = cp_rates * cp_peak_demand
        pwf_e = annuity(fin_in['analysis_years'], fin_in['escalation_pct'], fin_in['offtaker_discount_pct'])
        cp_charge_expected_total = cp_charge_expected_yr1 * \
                annuity(fin_in['analysis_years'], fin_in['escalation_pct'], fin_in['offtaker_discount_pct']) * \
                (1 - fin_in['offtaker_tax_pct'])

        try:
            self.assertAlmostEqual(tariff_out['year_one_coincident_peak_cost_us_dollars'], cp_charge_expected_yr1, places=0,
                            msg="Year one coincident peak cost ({}) does not equal expected year 1 coincident peak cost ({})."
                            .format(tariff_out['year_one_coincident_peak_cost_us_dollars'], cp_charge_expected_yr1))

        except Exception as e:
            error_msg = None
            if hasattr(messages, "error"):
                error_msg = messages.error
            print("test_coincident_peak API error message: {}".format(error_msg))
            print("Run uuid: {}".format(response['outputs']['Scenario']['run_uuid']))
            raise e

        try:
            self.assertAlmostEqual(round(tariff_out['total_coincident_peak_cost_us_dollars']), round(cp_charge_expected_total), places=0,
                            msg="Year one coincident peak cost ({}) does not equal expected total coincident peak cost ({})."
                            .format(tariff_out['total_coincident_peak_cost_us_dollars'], cp_charge_expected_total))

        except Exception as e:
            error_msg = None
            if hasattr(messages, "error"):
                error_msg = messages.error
            print("test_coincident_peak API error message: {}".format(error_msg))
            print("Run uuid: {}".format(response['outputs']['Scenario']['run_uuid']))
            raise e
        