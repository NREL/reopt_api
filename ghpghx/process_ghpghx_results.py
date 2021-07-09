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
import sys
import traceback
import copy
import numpy as np
import logging
from ghpghx.models import GHPGHXModel, ModelManager
log = logging.getLogger(__name__)


#TODO Update this to use celery for task queuing /ghpghx jobs (or wait until V2 to parallelize in Julia)

def process_ghpghx_results(data, meta, saveToDB=True):
    """
    Processes the two outputs from reopt.jl bau and with-Tech scenarios
    :param data: nested dict mirroring API response format
    :param meta: ={'run_uuid': run_uuid, 'api_version': api_version} from api.py
    :param saveToDB: boolean for saving postgres models
    :return: None
    """
    # profiler = Profiler()

    class Results:

        def __init__(self, results_dict, inputs):
            """
            Convenience (and legacy) class for handling REopt results
            :param results_dict: flat dict of results from reopt.jl
            :param inputs: dict, data['inputs']['Scenario']['Site']
            """
            self.inputs = inputs

            if results_dict.get("heat_pump_size_ton") is None:
                results_dict['heat_pump_size_ton'] = 0

            # results_dict['npv'] = results_dict['lcc_bau'] - results_dict['lcc']

            self.results_dict = results_dict
            self.nested_outputs = self.setup_nested()

        @property
        def example_property_calc(self):
            exmpl_calc = 3.14
            return exmpl_calc

        def get_output(self):
            self.get_nested()
            output_dict = self.nested_outputs
            return output_dict

        @staticmethod
        def setup_nested():
            """
            Set up up empty nested dict for outputs.
            :return: nested dict for outputs with values set to None. Results are filled in using "get_nested" method
            """
            nested_outputs = dict()
            nested_outputs["Scenario"] = dict()
            # nested_outputs["Scenario"]["Profile"] = dict()
            nested_outputs["Scenario"]["Site"] = dict()

            # Loop through all sub-site dicts and init
            for name, d in nested_output_definitions["outputs"]["Scenario"]["Site"].items():
                nested_outputs["Scenario"]["Site"][name] = dict()
                for k in d.keys():
                    nested_outputs["Scenario"]["Site"][name].setdefault(k, None)
            return nested_outputs

        def get_nested(self):
            """
            Translates the "flat" results_dict (which is just the JSON output from REopt optimization model)
            into the nested output dict.
            :return: None (modifies self.nested_outputs)
            """
            self.nested_outputs["Scenario"]["status"] = self.results_dict["status"]
            # financials = FinancialModel.objects.filter(run_uuid=meta['run_uuid']).first() #getting financial inputs for wind and pv lcoe calculations
            for name, d in nested_output_definitions["outputs"]["Scenario"]["Site"].items():
                if name == "HeatPump":
                    self.nested_outputs["Scenario"]["Site"][name]["output_test"] = self.results_dict.get("output_test")
                    
            # outputs that depend on multiple object results:
            exampl_calc_value = self.example_property_calc
            # self.nested_outputs["Scenario"]["Site"]["Financial"]["initial_capital_costs"] = self.upfront_capex


    self.data = data
    self.run_uuid = data['outputs']['Scenario']['run_uuid']
    # self.user_uuid = data['outputs']['Scenario'].get('user_uuid')

    try:
        results_object = Results(results_dict=dfm_list[0]['results'], inputs=data['inputs']['Scenario']['Site'])
        results = results_object.get_output()

        data['outputs'].update(results)
        data['outputs']['Scenario'].update(meta)  # run_uuid and api_version

        # profiler.profileEnd()
        # data['outputs']["Scenario"]["Profile"]["parse_run_outputs_seconds"] = profiler.getDuration()

        if saveToDB:
            ModelManager.update(data, run_uuid=self.run_uuid)

    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        log.info("Results.py raising the error: {}, detail: {}".format(exc_type, exc_value))
        raise UnexpectedError(exc_type, exc_value.args[0], traceback.format_tb(exc_traceback), task=self.name, run_uuid=self.run_uuid,
                              user_uuid=self.user_uuid)
