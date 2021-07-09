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
import copy
import time
import numpy as np
import pandas as pd
from tastypie.test import ResourceTestCaseMixin
from unittest import TestCase  # have to use unittest.TestCase to get tests to store to database, django.test.TestCase flushes db
from reo.models import ModelManager
from ghpghx.models import ModelManager as gModelManager
from reo.utilities import MMBTU_TO_KWH, TONHOUR_TO_KWHT

class GHPTest(ResourceTestCaseMixin, TestCase):
    REopt_tol = 1e-2

    def setUp(self):
        super(GHPTest, self).setUp()
        self.reopt_base = '/v1/job/'
        self.test_reopt_post = os.path.join('reo', 'tests', 'posts', 'test_ghp_POST.json')
        self.test_ghpghx_post = os.path.join('ghpghx', 'tests', 'posts', 'test_ghpghx_POST.json')

    def get_ghpghx_response(self, data):
        return self.api_client.post(self.ghpghx_base, format='json', data=data)

    def get_reopt_response(self, data):
        return self.api_client.post(self.reopt_base, format='json', data=data)

    def test_ghp(self):
        """

        This tests multiple unique aspects of GHP:
        1. The inputs validation of the /ghpghx endpoint input ghpghx_inputs
        2. The calling of the /ghpghx endpoint from within the scenario.py celery task
        3. The response created from the /ghpghx endpoint which is an input to reo /job endpoint
        4. GHP serving only the space heating portion of the heating load (LoadProfileBoilerFuel) input, 
            unless it is allowed to serve DHW
        5. Input of a custom COP map for GHP

        """

        nested_data = json.load(open(self.test_reopt_post, 'rb'))
        ghpghx_post = json.load(open(self.test_ghpghx_post, 'rb'))

        # Heat pump performance maps
        hp_cop_filepath = os.path.join('ghpghx', 'tests', 'posts', "heatpump_cop_map_custom.csv" )
        heatpump_copmap_df = pd.read_csv(hp_cop_filepath)
        heatpump_copmap_list_of_dict = heatpump_copmap_df.to_dict('records')
        ghpghx_post["cop_map_eft_heating_cooling"] = heatpump_copmap_list_of_dict

        nested_data["Scenario"]["Site"]["GHP"]["ghpghx_inputs"] = [ghpghx_post]
        
        #nested_data["Scenario"]["Site"]["GHP"]["ghpghx_response"] = json.load(open("reo/tests/posts/ghpghx_response.json", "r"))
        nested_data["Scenario"]["Site"]["LoadProfileBoilerFuel"]["doe_reference_name"] = "FlatLoad_24_5"
        nested_data["Scenario"]["Site"]["LoadProfileBoilerFuel"]["monthly_mmbtu"] = [500.0] + [1000.0]*10 + [1500.0]

        # Call REopt
        resp = self.get_reopt_response(data=nested_data)
        self.assertHttpCreated(resp)
        r = json.loads(resp.content)
        run_uuid = r.get('run_uuid')
        d = ModelManager.make_response(run_uuid=run_uuid)

        ghp_uuid = d["outputs"]["Scenario"]["Site"]["GHP"]["ghp_chosen_uuid"]
        print("GHP uuid chosen = ", ghp_uuid)

        heating_served_mmbtu = sum(d["outputs"]["Scenario"]["Site"]["GHP"]["ghpghx_chosen_outputs"]["heating_thermal_load_mmbtu_per_hr"])
        expected_heating_served_mmbtu = 12000 * 0.8 * 0.9 * 0.7  # (fuel_mmbtu * boiler_effic * addressable_load * space_heat_frac)

        self.assertAlmostEqual(heating_served_mmbtu, expected_heating_served_mmbtu, places=3)

        heating_cop_avg = d["inputs"]["Scenario"]["Site"]["GHP"]["ghpghx_response"]["outputs"]["heating_cop_avg"]
        cooling_cop_avg = d["inputs"]["Scenario"]["Site"]["GHP"]["ghpghx_response"]["outputs"]["cooling_cop_avg"]

        # Average COP which includes pump power should be lower than Heat Pump only COP specified by the map
        self.assertLess(heating_cop_avg, 4.0)
        self.assertLess(cooling_cop_avg, 8.0)
