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

class SOCIncentiveTests(ResourceTestCaseMixin, TestCase):
    REopt_tol = 1.0e-2

    def setUp(self):
        super(SOCIncentiveTests, self).setUp()
        self.reopt_base = '/v1/job/'
        self.test_post = os.path.join('reo', 'tests', 'posts', 'socIncentivePost.json')

    def get_response(self, data):
        return self.api_client.post(self.reopt_base, format='json', data=data)

    def test_soc_incentive(self):
        """
        Test scenario with
        - fixed PV of 100 kW
        - fixed battery of 20kW, 20kWh
        - no other techs
        Toggle on and off the SOC incentive in the objective function and compare average SOC and LCC's.
        """
        nested_data = json.load(open(self.test_post, 'rb'))
        nested_data['Scenario']['add_soc_incentive'] = True
        resp = self.get_response(data=nested_data)
        self.assertHttpCreated(resp)
        r = json.loads(resp.content)
        run_uuid = r.get('run_uuid')
        d = ModelManager.make_response(run_uuid=run_uuid)
        high_avg_soc = (sum(d['outputs']['Scenario']['Site']['Storage']['year_one_soc_series_pct']) /
                        len(d['outputs']['Scenario']['Site']['Storage']['year_one_soc_series_pct']))

        nested_data['Scenario']['add_soc_incentive'] = False
        resp = self.get_response(data=nested_data)
        self.assertHttpCreated(resp)
        r = json.loads(resp.content)
        run_uuid = r.get('run_uuid')
        d = ModelManager.make_response(run_uuid=run_uuid)
        low_avg_soc = (sum(d['outputs']['Scenario']['Site']['Storage']['year_one_soc_series_pct']) /
                       len(d['outputs']['Scenario']['Site']['Storage']['year_one_soc_series_pct']))

        self.assertGreater(high_avg_soc, low_avg_soc, "Average SOC should be higher when including SOC incentive.")
