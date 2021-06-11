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
from tastypie.test import ResourceTestCaseMixin
from django.test import TestCase
from reo.nested_to_flat_output import nested_to_flat
from reo.models import ModelManager
from reo.utilities import check_common_outputs

load_list_2 = [50]*35040
fts_post_2 = {"Scenario":
                  {"webtool_uuid": None, "description": "", "timeout_seconds": 295,
                   "time_steps_per_hour": 4, "user_uuid": None,
                   "Site": {
                       "roof_squarefeet": None,
                       "land_acres": None,
                       "latitude": 35.2468,
                       "longitude": -91.7337,
                       "address": "",
                       "PV": {
                            "pbi_years": 1.0,
                            "macrs_bonus_pct": 0.4,
                            "max_kw": 0.0,
                            "existing_kw": 0.0,
                            "pbi_max_us_dollars": 1000000000.0,
                            "radius": 0.0,
                            "state_ibi_pct": 0.0,
                            "utility_rebate_max_us_dollars": 10000000000.0,
                            "installed_cost_us_dollars_per_kw": 2000.0,
                            "utility_ibi_max_us_dollars": 10000000000.0,
                            "tilt": 35.2468,
                            "federal_rebate_us_dollars_per_kw": 0.0,
                            "gcr": 0.4,
                            "pbi_system_max_kw": 1000000000.0,
                            "utility_ibi_pct": 0.0,
                            "state_ibi_max_us_dollars": 10000000000.0,
                            "state_rebate_us_dollars_per_kw": 0.0,
                            "macrs_option_years": 5,
                            "state_rebate_max_us_dollars": 10000000000.0,
                            "dc_ac_ratio": 1.1,
                            "federal_itc_pct": 0.3,
                            "pbi_us_dollars_per_kwh": 0.0,
                            "module_type": 0,
                            "array_type": 0,
                            "om_cost_us_dollars_per_kw": 16.0,
                            "utility_rebate_us_dollars_per_kw": 0.0,
                            "min_kw": 0.0,
                            "losses": 0.14,
                            "macrs_itc_reduction": 0.5,
                            "degradation_pct": 0.005,
                            "inv_eff": 0.96,
                            "azimuth": 180.0 },
                       "Generator": {"pbi_years": 0.0, "macrs_bonus_pct": 0.0, "om_cost_us_dollars_per_kwh": 0.01,
                                     "max_kw": 10000000.0, "pbi_max_us_dollars": 0.0, "state_ibi_pct": 0.0,
                                     "fuel_intercept_gal_per_hr": 0.0125, "generator_only_runs_during_grid_outage": True,
                                     "state_rebate_us_dollars_per_kw": 0.0, "installed_cost_us_dollars_per_kw": 600.0,
                                     "utility_ibi_max_us_dollars": 0.0, "fuel_avail_gal": 100000.0,
                                     "min_turn_down_pct": 0.0, "pbi_system_max_kw": 0.0, "utility_ibi_pct": 0.0,
                                     "state_ibi_max_us_dollars": 0.0, "diesel_fuel_cost_us_dollars_per_gallon": 3.0,
                                     "fuel_slope_gal_per_kwh": 0.068, "utility_rebate_max_us_dollars": 0.0,
                                     "macrs_option_years": 0, "state_rebate_max_us_dollars": 0.0, "federal_itc_pct": 0.0,
                                     "existing_kw": 0.0, "pbi_us_dollars_per_kwh": 0.0, "om_cost_us_dollars_per_kw": 10.0,
                                     "utility_rebate_us_dollars_per_kw": 0.0, "min_kw": 0.0, "macrs_itc_reduction": 0.0,
                                     "federal_rebate_us_dollars_per_kw": 0.0, "generator_sells_energy_back_to_grid": False},
                       "LoadProfile": {"loads_kw": load_list_2, "critical_loads_kw_is_net": False, "critical_load_pct": 0.5,
                                       "loads_kw_is_net": True, "monthly_totals_kwh": [],
                                       "outage_start_time_step": 400, "outage_end_time_step": 499,
                                       "year": 2018, "outage_is_major_event": True,
                                       "critical_loads_kw": [], "annual_kwh": None},
                       "Storage": {"max_kwh": 0.0, "max_kw": 0.0},
                       "ElectricTariff": {"add_blended_rates_to_urdb_rate": False, "wholesale_rate_us_dollars_per_kwh": 0.0,
                                          "net_metering_limit_kw": 0.0, "interconnection_limit_kw": 100000000.0,
                                          "blended_monthly_demand_charges_us_dollars_per_kw": [20.0, 20.0, 20.0, 20.0, 20.0, 20.0, 20.0, 20.0, 20.0, 20.0, 20.0, 20.0],
                                          "urdb_utility_name": "", "urdb_label": "", "wholesale_rate_above_site_load_us_dollars_per_kwh": 0.0, "urdb_rate_name": "custom",
                                          "urdb_response": None, "blended_annual_demand_charges_us_dollars_per_kw": 0.0, "blended_annual_rates_us_dollars_per_kwh": 0.0,
                                          "blended_monthly_rates_us_dollars_per_kwh": [0.29, 0.29, 0.29, 0.29, 0.29, 0.29, 0.29, 0.29, 0.29, 0.29, 0.29, 0.29]},
                       "Financial": {"escalation_pct": 0.026, "offtaker_discount_pct": 0.081, "value_of_lost_load_us_dollars_per_kwh": 100.0,
                                     "analysis_years": 20, "microgrid_upgrade_cost_pct": 0.3, "offtaker_tax_pct": 0.26,
                                     "om_cost_escalation_pct": 0.025},
                       "Wind": {"max_kw": 0.0}
                   }
                 }
               }


class TestFlexibleTimeSteps(ResourceTestCaseMixin, TestCase):

    def setUp(self):
        super(TestFlexibleTimeSteps, self).setUp()
        self.reopt_base = '/v1/job/'
        self.REopt_tol = 1e-2

    def get_response(self, data):
        return self.api_client.post(self.reopt_base, format='json', data=data)

    def test_flexible_time_steps(self):
        """
        - Validation to ensure that upon entering time_steps_per_hour = 1 or 4, the results of the analysis
        are as expected (evaluating with only existing PV to keep test fast)
        - the output dimensions (8760, 35040 etc) must also match time_steps_per_hour given as input
        """
        # results for time_steps_per_hour = 4
        response = self.get_response(data=fts_post_2)
        self.assertHttpCreated(response)
        r2 = json.loads(response.content)
        run_uuid2 = r2.get('run_uuid')
        d2 = ModelManager.make_response(run_uuid=run_uuid2)
        c2 = nested_to_flat(d2['outputs'])

        self.assertEqual(len(c2["year_one_grid_to_load_series"]), 35040)

        # results for time_steps_per_hour = 1
        fts_post_2["Scenario"]["time_steps_per_hour"] = 1
        fts_post_2["Scenario"]["Site"]["LoadProfile"]["loads_kw"] = [50] * 8760
        fts_post_2["Scenario"]["Site"]["LoadProfile"]["outage_start_time_step"] = 100
        fts_post_2["Scenario"]["Site"]["LoadProfile"]["outage_end_time_step"] = 124
        response = self.get_response(data=fts_post_2)
        self.assertHttpCreated(response)
        r = json.loads(response.content)
        run_uuid = r.get('run_uuid')
        d = ModelManager.make_response(run_uuid=run_uuid)
        c1 = nested_to_flat(d['outputs'])

        # Seems reasonable that the exact resiliency average will be different due to a great granularity of survival
        # information in a quarter-hourly simulation vs hourly.
        del c1['avoided_outage_costs_us_dollars']
        del c2['avoided_outage_costs_us_dollars']
        check_common_outputs(self, c1, c2)