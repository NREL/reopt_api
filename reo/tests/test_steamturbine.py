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
from reo.nested_to_flat_output import nested_to_flat_chp
from unittest import TestCase  # have to use unittest.TestCase to get tests to store to database, django.test.TestCase flushes db
from reo.models import ModelManager
from reo.utilities import check_common_outputs, MMBTU_TO_KWH, TONHOUR_TO_KWHT
from reo.src.load_profile import default_annual_electric_loads, total_heating_annual_loads

class SteamTurbineTest(ResourceTestCaseMixin, TestCase):
    REopt_tol = 1e-2

    def setUp(self):
        super(SteamTurbineTest, self).setUp()
        self.reopt_base = '/v1/job/'
        self.test_post = os.path.join('reo', 'tests', 'posts', 'test_steamturbine_POST.json')

    def get_response(self, data):

        return self.api_client.post(self.reopt_base, format='json', data=data)

    def test_backpressure_steamturbine(self):
        """
        Validation to ensure that:
         1) Boiler provides the thermal energy (steam) to a backpressure steam turbine for CHP application
         2) ST serves the heating load with the condensing steam

        :return:
        """

        # Call API, get results in "d" dictionary
        nested_data = json.load(open(self.test_post, 'rb'))

        # Modify loads (currently "Hospital" in POST) to get larger SteamTurbine
        city = "SanFrancisco"
        building = "Hospital"
        elec_load_multiplier = 5.0
        heat_load_multiplier = 100.0
        nested_data["Scenario"]["Site"]["LoadProfile"]["doe_reference_name"] = building
        nested_data["Scenario"]["Site"]["LoadProfileBoilerFuel"]["doe_reference_name"] = building
        nested_data["Scenario"]["Site"]["LoadProfile"]["annual_kwh"] = elec_load_multiplier * default_annual_electric_loads[city][building.lower()]
        nested_data["Scenario"]["Site"]["LoadProfileBoilerFuel"]["annual_mmbtu"] = heat_load_multiplier * total_heating_annual_loads[city][building.lower()]

        resp = self.get_response(data=nested_data)
        # TODO pass input_errors if bad post
        self.assertHttpCreated(resp)
        r = json.loads(resp.content)
        run_uuid = r.get('run_uuid')
        d = ModelManager.make_response(run_uuid=run_uuid)
        c = nested_to_flat_chp(d['outputs'])

        # The values compared to the expected values may change if optimization parameters were changed
        d_expected = dict()
        d_expected['lcc'] = 189359280.0
        d_expected['npv'] = 8085233.0
        d_expected['steamturbine_size_kw'] = 2616.418
        d_expected['steamturbine_yearly_thermal_consumption_mmbtu'] = 1000557.6
        d_expected['steamturbine_yearly_electric_energy_produced_kwh'] = 18970374.6
        d_expected['steamturbine_yearly_thermal_energy_produced_mmbtu'] = 924045.1

        try:
            check_common_outputs(self, c, d_expected)
        except:
            print("Run {} expected outputs may have changed. Check the Outputs folder.".format(run_uuid))
            print("Error message: {}".format(d['messages'].get('error')))
            raise

        # BAU boiler loads
        load_boiler_fuel = d["outputs"]["Scenario"]["Site"]["LoadProfileBoilerFuel"]["year_one_boiler_fuel_load_series_mmbtu_per_hr"]
        load_boiler_thermal = d["outputs"]["Scenario"]["Site"]["LoadProfileBoilerFuel"]["year_one_boiler_thermal_load_series_mmbtu_per_hr"]

        # Boiler and SteamTurbine production
        boiler_to_load = d["outputs"]["Scenario"]["Site"]["Boiler"]["year_one_thermal_to_load_series_mmbtu_per_hour"]
        boiler_to_st = d["outputs"]["Scenario"]["Site"]["Boiler"]["year_one_thermal_to_steamturbine_series_mmbtu_per_hour"]
        boiler_total = [a + b for a, b in zip(boiler_to_load, boiler_to_st)]
        st_to_load = d["outputs"]["Scenario"]["Site"]["SteamTurbine"]["year_one_thermal_to_load_series_mmbtu_per_hour"]

        # Fuel/thermal **consumption**
        boiler_fuel = d["outputs"]["Scenario"]["Site"]["Boiler"]["year_one_boiler_fuel_consumption_series_mmbtu_per_hr"]
        steamturbine_thermal_in = d["outputs"]["Scenario"]["Site"]["SteamTurbine"]["year_one_thermal_consumption_series_mmbtu_per_hr"]
        
        # Check that all thermal supply to load meets the BAU load
        thermal_to_load = sum(boiler_to_load) + sum(st_to_load)
        self.assertAlmostEqual(thermal_to_load, sum(load_boiler_thermal), places=2) #delta=5

        # Check the net electric efficiency of Boiler->SteamTurbine (electric out/fuel in) with the expected value from the Fact Sheet 
        steamturbine_electric = d["outputs"]["Scenario"]["Site"]["SteamTurbine"]["year_one_electric_production_series_kw"] 
        net_electric_efficiency = sum(steamturbine_electric) / (sum(boiler_fuel) * MMBTU_TO_KWH)
        self.assertAlmostEqual(net_electric_efficiency, 0.05, delta=0.01)

        # Check that the max production of the boiler is still less than peak heating load times thermal factor
        factor = d['inputs']['Scenario']['Site']['Boiler']['max_thermal_factor_on_peak_load']
        boiler_capacity = max(load_boiler_thermal) * factor
        self.assertLessEqual(max(boiler_total), boiler_capacity)

    def test_all_heatingtechs(self):
        """
        Validation to ensure that:
         1) Heat balance is correct with SteamTurbine (backpressure), CHP, HotTES, and AbsorptionChiller included
         2) The sum of a all thermal from techs supplying SteamTurbine is equal to SteamTurbine thermal consumption
         3) Techs are not supplying SteamTurbine with thermal if can_supply_st = False

        :return:
        """

        # Call API, get results in "d" dictionary
        nested_data = json.load(open(self.test_post, 'rb'))
        nested_data["Scenario"]["optimality_tolerance_techs"] = 0.01

        # Add cooling load so we can test the energy balance on Absorption Chiller too (thermal consumption)
        nested_data["Scenario"]["Site"]["LoadProfileChillerThermal"] = {}
        nested_data["Scenario"]["Site"]["LoadProfileChillerThermal"]["doe_reference_name"] = "Hospital"

        # Fix size of SteamTurbine, even if smaller than practical, because we're just looking at energy balances
        nested_data["Scenario"]["Site"]["SteamTurbine"]["min_kw"] = 30.0
        nested_data["Scenario"]["Site"]["SteamTurbine"]["max_kw"] = 30.0

        # Add CHP 
        nested_data["Scenario"]["Site"]["CHP"] = {"prime_mover": "recip_engine",
                                                  "size_class": 2,
                                                  "min_kw": 250.0,
                                                  "min_allowable_kw":0.0,
                                                  "max_kw": 250.0}
        nested_data["Scenario"]["Site"]["CHP"]["can_supply_st"] = False
        nested_data["Scenario"]["Site"]["FuelTariff"]["chp_fuel_blended_annual_rates_us_dollars_per_mmbtu"] = 8.0
        nested_data["Scenario"]["Site"]["Financial"]["chp_fuel_escalation_pct"] = 0.034

        # Add cooling load and absorption chiller
        nested_data["Scenario"]["Site"]["AbsorptionChiller"] = {}
        nested_data["Scenario"]["Site"]["AbsorptionChiller"]["min_ton"] = 600.0
        nested_data["Scenario"]["Site"]["AbsorptionChiller"]["max_ton"] = 600.0

        # Add Hot TES
        nested_data["Scenario"]["Site"]["HotTES"] = {}
        nested_data["Scenario"]["Site"]["HotTES"]["min_gal"] = 50000.0
        nested_data["Scenario"]["Site"]["HotTES"]["max_gal"] = 50000.0

        resp = self.get_response(data=nested_data)
        self.assertHttpCreated(resp)
        r = json.loads(resp.content)
        run_uuid = r.get('run_uuid')
        d = ModelManager.make_response(run_uuid=run_uuid)

        thermal_techs = {"Boiler", "CHP", "SteamTurbine"}
        thermal_loads = {"load", "tes", "steamturbine", "waste"}  # We don't track AbsorptionChiller thermal consumption by tech
        tech_to_thermal_load = {}
        for tech in thermal_techs:
            tech_to_thermal_load[tech] = {}
            for load in thermal_loads:
                if (tech == "SteamTurbine" and load == "steamturbine") or (load == "waste" and tech != "CHP"):
                    tech_to_thermal_load[tech][load] = [0.0] * 8760
                else:
                    tech_to_thermal_load[tech][load] = d["outputs"]["Scenario"]["Site"][tech]["year_one_thermal_to_"+load+"_series_mmbtu_per_hour"]
        
        # Hot TES is the other thermal supply
        hottes_to_load = d["outputs"]["Scenario"]["Site"]["HotTES"]["year_one_thermal_from_hot_tes_series_mmbtu_per_hr"]
        
        # BAU boiler loads
        load_boiler_fuel = d["outputs"]["Scenario"]["Site"]["LoadProfileBoilerFuel"]["year_one_boiler_fuel_load_series_mmbtu_per_hr"]
        load_boiler_thermal = d["outputs"]["Scenario"]["Site"]["LoadProfileBoilerFuel"]["year_one_boiler_thermal_load_series_mmbtu_per_hr"]

        # Fuel/thermal **consumption**
        boiler_fuel = d["outputs"]["Scenario"]["Site"]["Boiler"]["year_one_boiler_fuel_consumption_series_mmbtu_per_hr"]
        chp_fuel_total = d["outputs"]["Scenario"]["Site"]["CHP"]["year_one_fuel_used_mmbtu"]
        steamturbine_thermal_in = d["outputs"]["Scenario"]["Site"]["SteamTurbine"]["year_one_thermal_consumption_series_mmbtu_per_hr"]
        absorptionchiller_thermal_in = d["outputs"]["Scenario"]["Site"]["AbsorptionChiller"]["year_one_absorp_chl_thermal_consumption_series_mmbtu_per_hr"]
        
        # Check that all thermal supply to load meets the BAU load plus AbsorptionChiller load which is not explicitly tracked
        alltechs_thermal_to_load_total = sum([sum(tech_to_thermal_load[tech]["load"]) for tech in thermal_techs]) + sum(hottes_to_load)
        thermal_load_total = sum(load_boiler_thermal) + sum(absorptionchiller_thermal_in)
        self.assertAlmostEqual(alltechs_thermal_to_load_total, thermal_load_total, places=2)

        # Check that all thermal to steam turbine is equal to steam turbine thermal consumption
        alltechs_thermal_to_steamturbine_total = sum([sum(tech_to_thermal_load[tech]["steamturbine"]) for tech in thermal_techs - {"SteamTurbine"}])
        self.assertAlmostEqual(alltechs_thermal_to_steamturbine_total, sum(steamturbine_thermal_in), places=3)

        # Check that "thermal_to_steamturbine" is zero for each tech which has input of can_supply_st as False
        for tech in thermal_techs - {"SteamTurbine"}:
            if d["inputs"]["Scenario"]["Site"][tech]["can_supply_st"] == False:
                self.assertEqual(sum(tech_to_thermal_load[tech]["steamturbine"]), 0.0)
