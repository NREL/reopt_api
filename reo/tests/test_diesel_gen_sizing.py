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
import os
from tastypie.test import ResourceTestCaseMixin
from reo.nested_to_flat_output import nested_to_flat
from django.test import TestCase
from reo.models import ModelManager
from reo.utilities import check_common_outputs


class GeneratorSizingTests(ResourceTestCaseMixin, TestCase):
    REopt_tol = 1.0e-2

    def setUp(self):
        super(GeneratorSizingTests, self).setUp()
        self.reopt_base = '/v1/job/'
        self.test_post = os.path.join('reo', 'tests', 'posts', 'generatorSizingPost.json')

    def get_response(self, data):
        return self.api_client.post(self.reopt_base, format='json', data=data)

    def outage_tech_to_load(self, list_to_load, outage_start, outage_end):
        """
        To resolve indexing empty list when checking critical_load=generator_to_load,
        define a function that sums up all technologies_to_load and skip if the tech is empty
        @param list_to_load:
        @param outage_start:
        @param outage_end:
        @return:
        """
        tech_to_load = list()
        for tech in list_to_load:
            if tech is not None:
                tech_to_load = [sum_t + t for sum_t, t in zip(tech_to_load, tech[outage_start:outage_end])]
        return tech_to_load

    def test_generator_sizing_with_existing_pv(self):
        """
        Test scenario with
        - no existing diesel generator
        - existing PV considered
        - new PV and Wind disabled
        - Unlimited max storage
        - generator doesn't sell energy to grid
        - generator is only allowed to operate during outage hours
        """
        nested_data = json.load(open(self.test_post, 'rb'))
        nested_data['Scenario']['Site']['LoadProfile']['outage_is_major_event'] = True
        nested_data['Scenario']['Site']['PV']['max_kw'] = 0
        nested_data['Scenario']['Site']['Generator']['existing_kw'] = 0
        nested_data['Scenario']['Site']['PV']['existing_kw'] = 100
        resp = self.get_response(data=nested_data)
        self.assertHttpCreated(resp)
        r = json.loads(resp.content)
        run_uuid = r.get('run_uuid')
        d = ModelManager.make_response(run_uuid=run_uuid)
        c = nested_to_flat(d['outputs'])
        c['year_one_emissions_lb_C02'] = d['outputs']['Scenario']['Site']['year_one_emissions_lb_C02']
        c['year_one_emissions_bau_lb_C02'] = d['outputs']['Scenario']['Site']['year_one_emissions_bau_lb_C02']
        c['utility_year_one_emissions_lb_C02'] = d['outputs']['Scenario']['Site']['ElectricTariff']['year_one_emissions_lb_C02']
        c['utility_year_one_emissions_bau_lb_C02'] = d['outputs']['Scenario']['Site']['ElectricTariff']['year_one_emissions_bau_lb_C02']
        c['generator_year_one_emissions_lb_C02'] = d['outputs']['Scenario']['Site']['Generator']['year_one_emissions_lb_C02']
        c['generator_year_one_emissions_bau_lb_C02'] = d['outputs']['Scenario']['Site']['Generator']['year_one_emissions_bau_lb_C02']


        c['year_one_emissions_lb_C02'] = d['outputs']['Scenario']['Site']['year_one_emissions_lb_C02']
        c['year_one_emissions_bau_lb_C02'] = d['outputs']['Scenario']['Site']['year_one_emissions_bau_lb_C02']
        c['utility_year_one_emissions_lb_C02'] = d['outputs']['Scenario']['Site']['ElectricTariff']['year_one_emissions_lb_C02']
        c['utility_year_one_emissions_bau_lb_C02'] = d['outputs']['Scenario']['Site']['ElectricTariff']['year_one_emissions_bau_lb_C02']
        c['generator_year_one_emissions_lb_C02'] = d['outputs']['Scenario']['Site']['Generator']['year_one_emissions_lb_C02']
        c['generator_year_one_emissions_bau_lb_C02'] = d['outputs']['Scenario']['Site']['Generator']['year_one_emissions_bau_lb_C02']

        d_expected = dict()
        d_expected['lcc'] = 242935.0
        d_expected['npv'] = -3963.0
        d_expected['pv_kw'] = 100.0
        d_expected['batt_kw'] = 0.0
        d_expected['batt_kwh'] = 0.0
        d_expected['gen_kw'] = 5.85713
        d_expected['fuel_used_gal'] = 0.912
        #d_expected['avoided_outage_costs_us_dollars'] = 2982.63
        d_expected['microgrid_upgrade_cost_us_dollars'] = 1054.2
        d_expected['gen_total_variable_om_cost_us_dollars'] = 1.0
        d_expected['existing_pv_om_cost_us_dollars'] = 11507.0
        d_expected['net_capital_costs_plus_om'] = 15470.0
        d_expected['year_one_emissions_lb_C02'] = 421693.1
        d_expected['year_one_emissions_bau_lb_C02'] = 421672.6
        d_expected['utility_year_one_emissions_lb_C02'] = 421672.6
        d_expected['utility_year_one_emissions_bau_lb_C02'] = 421672.6
        d_expected['generator_year_one_emissions_lb_C02'] = 20.5
        d_expected['generator_year_one_emissions_bau_lb_C02'] = 0

        try:
            self.assertEqual(d['outputs']['Scenario']['Site']['ElectricTariff']['emissions_region'], 'Southeast')
            check_common_outputs(self, c, d_expected)
        except:
            print("Run {} expected outputs may have changed.".format(run_uuid))
            print("Error message: {}".format(d['messages']))
            raise

        critical_load = d['outputs']['Scenario']['Site']['LoadProfile']['critical_load_series_kw']
        generator_to_load = d['outputs']['Scenario']['Site']['Generator']['year_one_to_load_series_kw']
        storage_to_load = d['outputs']['Scenario']['Site']['Storage']['year_one_to_load_series_kw']
        pv_to_load = d['outputs']['Scenario']['Site']['PV']['year_one_to_load_series_kw']
        outage_start = d['inputs']['Scenario']['Site']['LoadProfile']['outage_start_time_step']
        outage_end = d['inputs']['Scenario']['Site']['LoadProfile']['outage_end_time_step']

        list_to_load = [generator_to_load, storage_to_load, pv_to_load]
        tech_to_load = self.outage_tech_to_load(list_to_load, outage_start, outage_end)
        for x, y in zip(critical_load[outage_start:outage_end], tech_to_load):
            self.assertAlmostEquals(x, y, places=3)
