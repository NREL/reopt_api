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
from reo.nested_outputs import nested_output_definitions
import logging
from celery import shared_task, Task
from reo.exceptions import REoptError, UnexpectedError
from reo.models import ModelManager, PVModel, FinancialModel, WindModel, AbsorptionChillerModel
from reo.src.profiler import Profiler
from reo.src.emissions_calculator import EmissionsCalculator
from reo.utilities import annuity, TONHOUR_TO_KWHT, MMBTU_TO_KWH, GAL_DIESEL_TO_KWH, setup_capital_cost_offgrid
from reo.nested_inputs import macrs_five_year, macrs_seven_year
from reo.src.proforma_metrics import calculate_proforma_metrics
from reo.src.storage import HotTES, ColdTES
log = logging.getLogger(__name__)


class ProcessResultsTask(Task):
    """
    Used to define custom Error handling for celery task
    """
    name = 'process_results'
    max_retries = 0

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """
        log a bunch of stuff for debugging
        save message: error and outputs: Scenario: status
        need to stop rest of chain!?
        :param exc: The exception raised by the task.
        :param task_id: Unique id of the failed task. (not the run_uuid)
        :param args: Original arguments for the task that failed.
        :param kwargs: Original keyword arguments for the task that failed.
        :param einfo: ExceptionInfo instance, containing the traceback.
        :return: None, The return value of this handler is ignored.
        """
        if isinstance(exc, REoptError):
            exc.save_to_db()
        self.data["messages"]["error"] = exc.message
        self.data["outputs"]["Scenario"]["status"] = "An error occurred. See messages for more."
        ModelManager.update_scenario_and_messages(self.data, run_uuid=self.run_uuid)

        self.request.chain = None  # stop the chain?
        self.request.callback = None
        self.request.chord = None  # this seems to stop the infinite chord_unlock call


@shared_task(bind=True, base=ProcessResultsTask, ignore_result=True)
def process_results(self, dfm_list, data, meta, saveToDB=True):
    """
    Processes the two outputs from reopt.jl bau and with-Tech scenarios
    :param self: celery.Task
    :param dfm_list: list of serialized dat_file_managers (passed from group of REopt runs)
    :param data: nested dict mirroring API response format
    :param meta: ={'run_uuid': run_uuid, 'api_version': api_version} from api.py
    :param saveToDB: boolean for saving postgres models
    :return: None
    """
    profiler = Profiler()

    class Results:

        bau_attributes = [
            "lcc",
            "fuel_used_kwh",
            "GridToLoad",
            "year_one_energy_cost",
            "year_one_demand_cost",
            "year_one_fixed_cost",
            "year_one_min_charge_adder",
            "year_one_coincident_peak_cost",
            "year_one_bill",
            "year_one_utility_kwh",
            "year_one_export_benefit",
            "GridToLoad",
            "total_energy_cost",
            "total_demand_cost",
            "total_fixed_cost",
            "total_min_charge_adder",
            "total_coincident_peak_cost",
            "total_export_benefit",
            "net_capital_costs_plus_om",
            "gen_net_fixed_om_costs",
            "gen_net_variable_om_costs",
            "gen_total_fuel_cost",
            "gen_year_one_fuel_cost",
            "gen_year_one_variable_om_costs",
            "year_one_boiler_fuel_cost",
            "total_boiler_fuel_cost",
            "julia_input_construction_seconds",
            "julia_reopt_preamble_seconds",
            "julia_reopt_variables_seconds",
            "julia_reopt_constriants_seconds",
            "julia_reopt_optimize_seconds",
            "julia_reopt_postprocess_seconds",
            "pyjulia_start_seconds",
            "pyjulia_pkg_seconds",
            "pyjulia_activate_seconds",
            "pyjulia_include_model_seconds",
            "pyjulia_make_model_seconds",
            "pyjulia_include_reopt_seconds",
            "pyjulia_run_reopt_seconds"
        ]

        def __init__(self, results_dict, results_dict_bau, dm, inputs):
            """
            Convenience (and legacy) class for handling REopt results
            :param results_dict: flat dict of results from reopt.jl
            :param results_dict_bau: flat dict of results from reopt.jl for bau case
            :param dm: instance of DataManager class
            :param inputs: dict, data['inputs']['Scenario']['Site']
            """
            self.dm = dm
            self.inputs = inputs

            # remove invalid sizes due to optimization error margins
            for r in [results_dict, results_dict_bau]:
                for key, value in r.items():
                    if key.endswith('kw') or key.endswith('kwh'):
                        if value < 0:
                            r[key] = 0

            # add bau outputs to results_dict
            for k in Results.bau_attributes:
                if results_dict_bau.get(k) is None:
                    results_dict[k + '_bau'] = 0
                else:
                    results_dict[k + '_bau'] = results_dict_bau[k]

            for i in range(len(self.inputs["PV"])):
                # b/c of PV & PVNM techs in REopt, if both are zero then no value is written to REopt_results.json
                i += 1
                if results_dict.get('PV{}_kw'.format(i)) is None:
                    results_dict['PV{}_kw'.format(i)] = 0
                pv_bau_keys = ["PV{}_net_fixed_om_costs".format(i),
                               "average_yearly_PV{}_energy_produced".format(i),
                               "year_one_PV{}_energy_produced".format(i),
                               "average_yearly_energy_produced_PV{}".format(i),
                              ]
                for k in pv_bau_keys:
                    if results_dict_bau.get(k) is None:
                        results_dict[k + '_bau'] = 0
                    else:
                        results_dict[k + '_bau'] = results_dict_bau[k]

            # if wind is zero then no value is written to REopt results.json
            if results_dict.get("wind_kw") is None:
                results_dict['wind_kw'] = 0

            # if generator is zero then no value is written to REopt results.json
            if results_dict.get("generator_kw") is None:
                results_dict['generator_kw'] = 0

            # if CHP is zero then no value is written to REopt results.json
            if results_dict.get("chp_kw") is None:
                results_dict['chp_kw'] = 0

            if results_dict.get("absorpchl_kw") is None:
                results_dict['absorpchl_kw'] = 0

            if results_dict.get("hot_tes_size_kwh") is None:
                results_dict['hot_tes_size_kwh'] = 0

            if results_dict.get("cold_tes_size_kwht") is None:
                results_dict['cold_tes_size_kwht'] = 0

            results_dict['npv'] = results_dict['lcc_bau'] - results_dict['lcc']

            self.results_dict = results_dict
            self.nested_outputs = self.setup_nested()

        @property
        def replacement_costs_future_and_present(self):
            future_cost_inverter = self.inputs["Storage"]["replace_cost_us_dollars_per_kw"] * \
                                 self.nested_outputs["Scenario"]["Site"]["Storage"]["size_kw"]
            future_cost_storage = self.inputs["Storage"]["replace_cost_us_dollars_per_kwh"] * \
                                 self.nested_outputs["Scenario"]["Site"]["Storage"]["size_kwh"]
            future_cost = future_cost_inverter + future_cost_storage

            tax_rate = self.inputs["Financial"]["owner_tax_pct"]
            discount_rate = self.inputs["Financial"]["owner_discount_pct"]
            present_cost = 0
            present_cost += future_cost_inverter * (1 - tax_rate) / ((1 + discount_rate) **
                                                                    self.inputs["Storage"]["inverter_replacement_year"])
            present_cost += future_cost_storage * (1 - tax_rate) / ((1 + discount_rate) **
                                                                    self.inputs["Storage"]["battery_replacement_year"])
            return round(future_cost, 2), round(present_cost, 2)

        @property
        def upfront_capex(self):
            upfront_capex = 0
            upfront_capex += max(self.inputs["Generator"]["installed_cost_us_dollars_per_kw"]
                                 * (self.nested_outputs["Scenario"]["Site"]["Generator"]["size_kw"]
                                 - self.inputs["Generator"]["existing_kw"]), 0)
            for pv in self.inputs["PV"]:
                upfront_capex += max(pv["installed_cost_us_dollars_per_kw"]
                                 * (self.nested_outputs["Scenario"]["Site"]["PV"][pv["pv_number"]-1]["size_kw"]
                                 - pv["existing_kw"]), 0)
            for tech in ["Storage", "Wind"]:
                upfront_capex += (self.inputs[tech].get("installed_cost_us_dollars_per_kw") or 0) * \
                                 (self.nested_outputs["Scenario"]["Site"][tech].get("size_kw") or 0)
            # CHP.installed_cost_us_dollars_per_kw is now a list with potentially > 1 elements
            for tech in ["CHP"]:
                cost_list = self.inputs[tech].get("installed_cost_us_dollars_per_kw") or []
                size_list = self.inputs[tech].get("tech_size_for_cost_curve") or []
                chp_size = self.nested_outputs["Scenario"]["Site"][tech].get("size_kw")
                if len(cost_list) > 1:
                    if chp_size <= size_list[0]:
                        upfront_capex += chp_size * cost_list[0]  # Currently not handling non-zero cost ($) for 0 kW size input
                    elif chp_size > size_list[-1]:
                        upfront_capex += chp_size * cost_list[-1]
                    else:
                        for s in range(1, len(size_list)):
                            if (chp_size > size_list[s-1]) and (chp_size <= size_list[s]):
                                slope = (cost_list[s] * size_list[s] - cost_list[s-1] * size_list[s-1]) / \
                                        (size_list[s] - size_list[s-1])
                                upfront_capex += cost_list[s-1] * size_list[s-1] + (chp_size - size_list[s-1]) * slope
                elif len(cost_list) == 1:
                    upfront_capex += (cost_list[0] or 0) * (chp_size or 0)

            # storage capacity
            upfront_capex += (self.inputs["Storage"].get("installed_cost_us_dollars_per_kwh") or 0) * \
                             (self.nested_outputs["Scenario"]["Site"]["Storage"].get("size_kwh") or 0)
            if self.nested_outputs["Scenario"]["Site"]["AbsorptionChiller"].get("size_ton"):
                # Need to update two cost input attributes which are calculated in techs.py and updated in scenario.py
                absorp_chl = AbsorptionChillerModel.objects.filter(run_uuid=data['outputs']['Scenario']['run_uuid'])[0]
                self.inputs["AbsorptionChiller"].update(
                    {"installed_cost_us_dollars_per_ton": absorp_chl.installed_cost_us_dollars_per_ton,
                     "om_cost_us_dollars_per_ton": absorp_chl.om_cost_us_dollars_per_ton})
            upfront_capex += (self.inputs["AbsorptionChiller"].get("installed_cost_us_dollars_per_ton") or 0) * \
                             (self.nested_outputs["Scenario"]["Site"]["AbsorptionChiller"].get("size_ton") or 0)

            upfront_capex += (self.inputs["HotTES"].get("installed_cost_us_dollars_per_gal") or 0) * \
                             (self.nested_outputs["Scenario"]["Site"]["HotTES"].get("size_gal") or 0)

            upfront_capex += (self.inputs["ColdTES"].get("installed_cost_us_dollars_per_gal") or 0) * \
                             (self.nested_outputs["Scenario"]["Site"]["ColdTES"].get("size_gal") or 0)

            return round(upfront_capex, 2)

        @property
        def third_party_factor(self):
            yrs = self.inputs["Financial"]["analysis_years"]
            pwf_offtaker = annuity(yrs, 0, self.inputs["Financial"]["offtaker_discount_pct"])
            pwf_owner = annuity(yrs, 0, self.inputs["Financial"]["owner_discount_pct"])
            return (pwf_offtaker * (1 - self.inputs["Financial"]["offtaker_tax_pct"])) \
                    / (pwf_owner * (1 - self.inputs["Financial"]["owner_tax_pct"]))

        @property
        def upfront_capex_after_incentives(self):
            """
            The net_capital_costs output is the upfront capex after incentives, except it includes the battery
            replacement cost in present value. So we calculate the upfront_capex_after_incentives as net_capital_costs
            minus the battery replacement cost in present value.
            Note that the owner_discount_pct and owner_tax_pct are set to the offtaker_discount_pct and offtaker_tax_pct
            respectively when third_party_ownership is False.
            """
            upfront_capex_after_incentives = self.nested_outputs["Scenario"]["Site"]["Financial"]["net_capital_costs"] \
                                             / self.third_party_factor

            pwf_inverter = 1 / ((1 + self.inputs["Financial"]["owner_discount_pct"])
                                ** self.inputs["Storage"]["inverter_replacement_year"])

            pwf_storage = 1 / ((1 + self.inputs["Financial"]["owner_discount_pct"])
                               ** self.inputs["Storage"]["battery_replacement_year"])

            inverter_future_cost = self.inputs["Storage"]["replace_cost_us_dollars_per_kw"] * \
                                   self.nested_outputs["Scenario"]["Site"]["Storage"]["size_kw"]

            storage_future_cost = self.inputs["Storage"]["replace_cost_us_dollars_per_kwh"] * \
                                  self.nested_outputs["Scenario"]["Site"]["Storage"]["size_kwh"]

            # NOTE these upfront costs include the tax benefit available to commercial entities
            upfront_capex_after_incentives -= inverter_future_cost * pwf_inverter * \
                                              (1 - self.inputs["Financial"]["owner_tax_pct"])
            upfront_capex_after_incentives -= storage_future_cost * pwf_storage * \
                                              (1 - self.inputs["Financial"]["owner_tax_pct"])
            return round(upfront_capex_after_incentives, 2)

        @property
        def get_offgrid_lcoe_breakdown(self):

            lcoe_component_fuel = None
            lcoe_component_re_capex = None
            lcoe_component_diesel_capex = None
            lcoe_component_other_capex = None
            lcoe_component_om = None
            lcoe_component_other_annual_costs = None
            lcoe = self.nested_outputs["Scenario"]["Site"]["Financial"]["microgrid_lcoe_us_dollars_per_kwh"]
            
            if lcoe is not None:
                lcc = self.nested_outputs["Scenario"]["Site"]["Financial"]["lcc_us_dollars"]
                
                fuel = (self.nested_outputs["Scenario"]['Site']['Generator']['total_fuel_cost_us_dollars'] or 0)
                other_capex = (self.nested_outputs["Scenario"]["Site"]["Financial"]["additional_cap_costs_us_dollars"] or 0)
                other_annual_costs = (self.nested_outputs["Scenario"]["Site"]["Financial"]["total_annual_cost_us_dollars"] or 0)
                
                analysis_period = self.inputs["Financial"]["analysis_years"]
                discount_rate = self.inputs["Financial"]["owner_discount_pct"]
                diesel_unit_cost = setup_capital_cost_offgrid(analysis_period, discount_rate,
                                   self.inputs["Generator"]["installed_cost_us_dollars_per_kw"],
                                   self.inputs["Generator"]["installed_cost_us_dollars_per_kw"],
                                   self.inputs["Generator"]["useful_life_years"])
                inverter_unit_cost = setup_capital_cost_offgrid(analysis_period, discount_rate,
                                   self.inputs["Storage"]["installed_cost_us_dollars_per_kw"],
                                   self.inputs["Storage"]["replace_cost_us_dollars_per_kw"],
                                   self.inputs["Storage"]["inverter_replacement_year"])
                battery_unit_cost = setup_capital_cost_offgrid(analysis_period, discount_rate,
                                   self.inputs["Storage"]["installed_cost_us_dollars_per_kwh"],
                                   self.inputs["Storage"]["replace_cost_us_dollars_per_kwh"],
                                   self.inputs["Storage"]["battery_replacement_year"])
                pv_om = 0
                for i in range(len(self.nested_outputs['Scenario']['Site']['PV'])):
                    pv_om += self.nested_outputs['Scenario']['Site']['PV'][i]['total_fixed_om_cost_us_dollars']

                diesel_variable_om = (self.nested_outputs['Scenario']['Site']['Generator']['total_variable_om_cost_us_dollars'] or 0)
                diesel_fixed_om = (self.nested_outputs['Scenario']['Site']['Generator']['total_fixed_om_cost_us_dollars'] or 0)
                total_om = pv_om + diesel_variable_om + diesel_fixed_om

                diesel_capex = max(diesel_unit_cost * (self.nested_outputs["Scenario"]["Site"]["Generator"]["size_kw"]
                                   - self.inputs["Generator"]["existing_kw"]), 0)
                re_capex = 0
                for pv in self.inputs["PV"]:
                    re_capex += max(pv["installed_cost_us_dollars_per_kw"]
                                    * (self.nested_outputs["Scenario"]["Site"]["PV"][pv["pv_number"]-1]["size_kw"]
                                    - pv["existing_kw"]), 0)
                for tech in ["Storage"]:
                    re_capex += inverter_unit_cost * (self.nested_outputs["Scenario"]["Site"][tech].get("size_kw") or 0)

                # storage capacity
                re_capex += battery_unit_cost * (self.nested_outputs["Scenario"]["Site"]["Storage"].get("size_kwh") or 0)
            
                lcoe_component_fuel = round((fuel/lcc) * lcoe, 4)
                lcoe_component_re_capex = round((re_capex/lcc) * lcoe, 4)
                lcoe_component_diesel_capex = round((diesel_capex/lcc) * lcoe, 4)
                lcoe_component_other_capex = round((other_capex/lcc) * lcoe, 4)
                lcoe_component_om = round((total_om/lcc) * lcoe, 4)
                lcoe_component_other_annual_costs = round((other_annual_costs/lcc) * lcoe, 4)

            return lcoe_component_fuel, lcoe_component_re_capex, lcoe_component_diesel_capex, \
                   lcoe_component_other_capex, lcoe_component_om, lcoe_component_other_annual_costs

        def calculate_lcoe(self, tech_results_dict, tech_inputs_dict, financials):
            """
            The LCOE is calculated as annualized costs (capital and O+M translated to current value) divided by annualized energy
            output
            :param tech_results_dict: dict of model results (i.e. outputs from PVModel )
            :param tech_inputs_dict: dict of model results (i.e. inputs to PVModel )
            :param financials: financial model storing input financial parameters
            :return: float, LCOE in US dollars per kWh
            """
            years = financials.analysis_years # length of financial life

            if financials.third_party_ownership:
                discount_pct = financials.owner_discount_pct
                federal_tax_pct = financials.owner_tax_pct
            else:
                discount_pct = financials.offtaker_discount_pct
                federal_tax_pct = financials.offtaker_tax_pct

            new_kw = (tech_results_dict.get('size_kw') or 0) - (tech_inputs_dict.get('existing_kw') or 0) # new capacity

            if new_kw == 0:
                return None

            capital_costs = new_kw * tech_inputs_dict['installed_cost_us_dollars_per_kw'] # pre-incentive capital costs

            annual_om = new_kw * tech_inputs_dict['om_cost_us_dollars_per_kw'] # NPV of O&M charges escalated over financial life

            om_series = [annual_om * (1+financials.om_cost_escalation_pct)**yr for yr in range(1, years+1)]
            npv_om = sum([om * (1.0/(1.0+discount_pct))**yr for yr, om in enumerate(om_series,1)])

            #Incentives as calculated in the spreadsheet, note utility incentives are applied before state incentives
            utility_ibi = min(capital_costs * tech_inputs_dict['utility_ibi_pct'], tech_inputs_dict['utility_ibi_max_us_dollars'])
            utility_cbi = min(new_kw * tech_inputs_dict['utility_rebate_us_dollars_per_kw'], tech_inputs_dict['utility_rebate_max_us_dollars'])
            state_ibi = min((capital_costs - utility_ibi - utility_cbi) * tech_inputs_dict['state_ibi_pct'], tech_inputs_dict['state_ibi_max_us_dollars'])
            state_cbi = min(new_kw * tech_inputs_dict['state_rebate_us_dollars_per_kw'], tech_inputs_dict['state_rebate_max_us_dollars'])
            federal_cbi = new_kw * tech_inputs_dict['federal_rebate_us_dollars_per_kw']
            ibi = utility_ibi + state_ibi  #total investment-based incentives
            cbi = utility_cbi + federal_cbi + state_cbi #total capacity-based incentives

            #calculate energy in the BAU case, used twice later on
            if 'year_one_energy_produced_bau_kwh' in tech_results_dict.keys():
                existing_energy_bau = tech_results_dict['year_one_energy_produced_bau_kwh'] or 0
            else:
                existing_energy_bau = 0

            #calculate the value of the production-based incentive stream
            npv_pbi = 0
            if tech_inputs_dict['pbi_max_us_dollars'] > 0:
                for yr in range(years):
                    if yr < tech_inputs_dict['pbi_years']:
                        degredation_pct = (1- (tech_inputs_dict.get('degradation_pct') or 0))**yr
                        base_pbi = min(tech_inputs_dict['pbi_us_dollars_per_kwh'] * \
                            ((tech_results_dict['year_one_energy_produced_kwh'] or 0) - existing_energy_bau) * \
                             degredation_pct,  tech_inputs_dict['pbi_max_us_dollars'] * degredation_pct )
                        base_pbi = base_pbi * (1.0/(1.0+discount_pct))**(yr+1)
                        npv_pbi += base_pbi

            npv_federal_itc = 0
            depreciation_schedule = np.array([0.0 for _ in range(years)])
            if tech_inputs_dict['macrs_option_years'] in [5,7]:
                if tech_inputs_dict['macrs_option_years'] == 5:
                    schedule = macrs_five_year
                if tech_inputs_dict['macrs_option_years'] == 7:
                    schedule = macrs_seven_year
                federal_itc_basis = capital_costs - state_ibi - utility_ibi - state_cbi - utility_cbi - federal_cbi
                federal_itc_amount = tech_inputs_dict['federal_itc_pct'] * federal_itc_basis
                npv_federal_itc = federal_itc_amount * (1.0/(1.0+discount_pct))
                macrs_bonus_basis = federal_itc_basis - (federal_itc_basis * tech_inputs_dict['federal_itc_pct'] * tech_inputs_dict['macrs_itc_reduction'])
                macrs_basis = macrs_bonus_basis * (1 - tech_inputs_dict['macrs_bonus_pct'])
                for i,r in enumerate(schedule):
                    if i < len(depreciation_schedule):
                        depreciation_schedule[i] = macrs_basis * r
                depreciation_schedule[0] += (tech_inputs_dict['macrs_bonus_pct'] * macrs_bonus_basis)

            tax_deductions = (np.array(om_series)  + np.array(depreciation_schedule)) * federal_tax_pct
            npv_tax_deductions = sum([i* (1.0/(1.0+discount_pct))**yr for yr,i in enumerate(tax_deductions,1)])

            #we only care about the energy produced by new capacity in LCOE calcs
            annual_energy = (tech_results_dict['year_one_energy_produced_kwh'] or 0) - existing_energy_bau
            npv_annual_energy = sum([annual_energy * ((1.0/(1.0+discount_pct))**yr) * \
                (1- (tech_inputs_dict.get('degradation_pct') or 0))**(yr-1) for yr, i in enumerate(tax_deductions,1)])

            #LCOE is calculated as annualized costs divided by annualized energy
            lcoe = (capital_costs + npv_om - npv_pbi - cbi - ibi - npv_federal_itc - npv_tax_deductions ) / \
                    (npv_annual_energy)

            return round(lcoe,4)

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
            nested_outputs["Scenario"]["Profile"] = dict()
            nested_outputs["Scenario"]["Site"] = dict()

            # Loop through all sub-site dicts and init
            for name, d in nested_output_definitions["outputs"]["Scenario"]["Site"].items():
                nested_outputs["Scenario"]["Site"][name] = dict()
                for k in d.keys():
                    nested_outputs["Scenario"]["Site"][name].setdefault(k, None)
            return nested_outputs

        def get_nested(self):
            """
            Translates the "flat" results_dict (which is just the JSON output from REopt mosel code)
            into the nested output dict.
            :return: None (modifies self.nested_outputs)
            """
            # TODO: move the filling in of outputs to reopt.jl
            self.nested_outputs["Scenario"]["status"] = self.results_dict["status"]
            self.nested_outputs["Scenario"]["lower_bound"] = self.results_dict.get("lower_bound")
            self.nested_outputs["Scenario"]["optimality_gap"] = self.results_dict.get("optimality_gap")
            financials = FinancialModel.objects.filter(run_uuid=meta['run_uuid']).first() #getting financial inputs for wind and pv lcoe calculations
            for name, d in nested_output_definitions["outputs"]["Scenario"]["Site"].items():
                if name == "LoadProfile":
                    self.nested_outputs["Scenario"]["Site"][name]["year_one_electric_load_series_kw"] = self.dm["LoadProfile"].get("year_one_electric_load_series_kw")
                    self.nested_outputs["Scenario"]["Site"][name]["critical_load_series_kw"] = self.dm["LoadProfile"].get("critical_load_series_kw")
                    self.nested_outputs["Scenario"]["Site"][name]["annual_calculated_kwh"] = self.dm["LoadProfile"].get("annual_kwh")
                    self.nested_outputs["Scenario"]["Site"][name]["resilience_check_flag"] = self.dm["LoadProfile"].get("resilience_check_flag")
                    self.nested_outputs["Scenario"]["Site"][name]["sustain_hours"] = int(self.dm["LoadProfile"].get("bau_sustained_time_steps") / (len(self.dm["LoadProfile"].get("year_one_electric_load_series_kw"))/8760))
                    self.nested_outputs["Scenario"]["Site"][name]["bau_sustained_time_steps"] = self.dm["LoadProfile"].get("bau_sustained_time_steps")
                    self.nested_outputs["Scenario"]["Site"][name]['loads_kw'] = self.dm["LoadProfile"].get("year_one_electric_load_series_kw")
                    self.nested_outputs["Scenario"]["Site"][name]["load_met_series_kw"] = self.results_dict.get("load_met")
                    self.nested_outputs["Scenario"]["Site"][name]["sr_required_series_kw"] = self.results_dict.get("sr_required_load")
                    #Debug variables
                    self.nested_outputs["Scenario"]["Site"][name]["total_sr_required"] = self.results_dict.get("tot_sr_required")
                    self.nested_outputs["Scenario"]["Site"][name]["total_sr_provided"] = self.results_dict.get("tot_sr_provided")
                elif name == "LoadProfileBoilerFuel":
                    self.nested_outputs["Scenario"]["Site"][name]["annual_calculated_boiler_fuel_load_mmbtu_bau"] = \
                        self.dm["LoadProfile"].get("annual_heating_mmbtu")
                    self.nested_outputs["Scenario"]["Site"][name]["year_one_boiler_fuel_load_series_mmbtu_per_hr"] = \
                        self.dm["LoadProfile"].get("year_one_boiler_fuel_load_series_mmbtu_per_hr")
                    self.nested_outputs["Scenario"]["Site"][name]["year_one_boiler_thermal_load_series_mmbtu_per_hr"] = \
                        [x * self.dm.get("boiler_efficiency", 0) \
                        for x in self.dm["LoadProfile"].get("year_one_boiler_fuel_load_series_mmbtu_per_hr")]
                elif name == "LoadProfileChillerThermal":
                    self.nested_outputs["Scenario"]["Site"][name]["annual_calculated_kwh_bau"] = \
                        self.dm["LoadProfile"].get("annual_cooling_kwh")
                    self.nested_outputs["Scenario"]["Site"][name]["year_one_chiller_electric_load_series_kw"] = \
                        self.dm["LoadProfile"].get("year_one_chiller_electric_load_series_kw")
                    self.nested_outputs["Scenario"]["Site"][name]["year_one_chiller_thermal_load_series_ton"] = \
                        [x * self.dm.get("elecchl_cop", 0) / TONHOUR_TO_KWHT \
                        for x in self.dm["LoadProfile"].get("year_one_chiller_electric_load_series_kw")]
                elif name == "Financial":
                    self.nested_outputs["Scenario"]["Site"][name]["lcc_us_dollars"] = self.results_dict.get("lcc")
                    self.nested_outputs["Scenario"]["Site"][name]["lcc_bau_us_dollars"] = self.results_dict.get(
                        "lcc_bau")
                    self.nested_outputs["Scenario"]["Site"][name]["npv_us_dollars"] = self.results_dict.get("npv")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "net_capital_costs_plus_om_us_dollars"] = self.results_dict.get("net_capital_costs_plus_om")
                    self.nested_outputs["Scenario"]["Site"][name]["net_om_us_dollars_bau"] = self.results_dict.get(
                        "net_capital_costs_plus_om_bau")
                    self.nested_outputs["Scenario"]["Site"][name]["net_capital_costs"] = self.results_dict.get(
                        "net_capital_costs")
                    self.nested_outputs["Scenario"]["Site"][name]["microgrid_upgrade_cost_us_dollars"] = \
                        self.results_dict.get("net_capital_costs") * financials.microgrid_upgrade_cost_pct
                    self.nested_outputs["Scenario"]["Site"][name]["total_om_costs_us_dollars"] = self.results_dict.get(
                        "total_om_costs_after_tax")
                    self.nested_outputs["Scenario"]["Site"][name]["year_one_om_costs_us_dollars"] = self.results_dict.get(
                        "year_one_om_costs_after_tax")
                    self.nested_outputs["Scenario"]["Site"][name]["year_one_om_costs_before_tax_us_dollars"] = \
                        self.results_dict.get("year_one_om_costs_before_tax")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "additional_cap_costs_us_dollars"] = self.results_dict.get("total_other_cap_costs")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "total_annual_cost_us_dollars"] = self.results_dict.get("total_annual_costs")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "microgrid_lcoe_us_dollars_per_kwh"] = self.results_dict.get("microgrid_lcoe")
                elif name == "PV":
                    pv_models = list(PVModel.objects.filter(run_uuid=meta['run_uuid']).order_by('pv_number'))
                    template_pv = copy.deepcopy(self.nested_outputs['Scenario']["Site"][name])
                    self.nested_outputs['Scenario']["Site"][name] = []
                    for i, pv_model in enumerate(pv_models):
                        i += 1
                        pv = copy.deepcopy(template_pv)
                        pv["pv_number"] = i
                        pv["size_kw"] = self.results_dict.get("PV{}_kw".format(i)) or 0
                        pv["average_yearly_energy_produced_kwh"] = self.results_dict.get("average_yearly_energy_produced_PV{}".format(i))
                        pv["average_yearly_energy_produced_bau_kwh"] = self.results_dict.get("average_yearly_energy_produced_PV{}_bau".format(i))
                        pv["average_yearly_energy_exported_kwh"] = self.results_dict.get("average_annual_energy_exported_PV{}".format(i))
                        pv["year_one_energy_produced_kwh"] = self.results_dict.get("year_one_energy_produced_PV{}".format(i))
                        pv["year_one_energy_produced_bau_kwh"] = self.results_dict.get("year_one_PV{}_energy_produced_bau".format(i))
                        pv["year_one_to_battery_series_kw"] = self.results_dict.get("PV{}toBatt".format(i))
                        pv["year_one_to_load_series_kw"] = self.results_dict.get("PV{}toLoad".format(i))
                        pv["year_one_to_grid_series_kw"] = self.results_dict.get("PV{}toGrid".format(i))
                        pv['year_one_curtailed_production_series_kw'] = self.results_dict.get("PV{}toCurtail".format(i))
                        pv['sr_required_series_kw'] = self.results_dict.get("SRrequiredPV{}".format(i))
                        pv['sr_provided_series_kw'] = self.results_dict.get("SRprovidedPV{}".format(i))
                        pv["year_one_power_production_series_kw"] = pv.get("year_one_to_grid_series_kw")
                        if not pv.get("year_one_to_battery_series_kw") is None:
                            if pv["year_one_power_production_series_kw"] is None:
                                pv["year_one_power_production_series_kw"] = pv.get("year_one_to_battery_series_kw")
                            else:
                                pv["year_one_power_production_series_kw"] = \
                                    list(np.array(pv["year_one_power_production_series_kw"]) +
                                         np.array(pv.get("year_one_to_battery_series_kw")))
                        if not pv.get("year_one_to_load_series_kw") is None:
                            if pv["year_one_power_production_series_kw"] is None:
                                pv["year_one_power_production_series_kw"] = pv.get("year_one_to_load_series_kw")
                            else:
                                pv["year_one_power_production_series_kw"] = \
                                    list(np.array(pv["year_one_power_production_series_kw"]) +
                                         np.array(pv.get("year_one_to_load_series_kw")))
                        if pv["year_one_power_production_series_kw"] is None:
                            pv["year_one_power_production_series_kw"] = []
                        pv["total_fixed_om_cost_us_dollars"] = self.results_dict.get("PV{}_net_fixed_om_costs".format(i))
                        pv["existing_pv_om_cost_us_dollars"] = self.results_dict.get("PV{}_net_fixed_om_costs_bau".format(i))
                        pv["station_latitude"] = pv_model.station_latitude
                        pv["station_longitude"] = pv_model.station_longitude
                        pv["station_distance_km"] = pv_model.station_distance_km
                        pv['lcoe_us_dollars_per_kwh'] = self.calculate_lcoe(pv, pv_model.__dict__, financials)
                        self.nested_outputs['Scenario']["Site"][name].append(pv)
                elif name == "Wind":
                    self.nested_outputs["Scenario"]["Site"][name]["size_kw"] = self.results_dict.get("wind_kw", 0)
                    self.nested_outputs["Scenario"]["Site"][name][
                        "average_yearly_energy_produced_kwh"] = self.results_dict.get("average_wind_energy_produced")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "average_yearly_energy_exported_kwh"] = self.results_dict.get(
                        "average_annual_energy_exported_wind")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_energy_produced_kwh"] = self.results_dict.get("year_one_wind_energy_produced")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_to_battery_series_kw"] = self.results_dict.get("WINDtoBatt")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_to_load_series_kw"] = self.results_dict.get("WINDtoLoad")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_to_grid_series_kw"] = self.results_dict.get("WINDtoGrid")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_curtailed_production_series_kw"] = self.results_dict.get("WINDtoCurtail")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_power_production_series_kw"] = self.compute_total_power(name)
                    if self.nested_outputs["Scenario"]["Site"][name]["size_kw"] > 0: #setting up
                        wind_model = WindModel.objects.get(run_uuid=meta['run_uuid'])
                        self.nested_outputs["Scenario"]["Site"][name]['lcoe_us_dollars_per_kwh'] = \
                            self.calculate_lcoe(self.nested_outputs["Scenario"]["Site"][name], wind_model.__dict__, financials)
                        data['inputs']['Scenario']["Site"]["Wind"]["installed_cost_us_dollars_per_kw"] = \
                            wind_model.installed_cost_us_dollars_per_kw
                        data['inputs']['Scenario']["Site"]["Wind"]["federal_itc_pct"] = wind_model.federal_itc_pct
                    else:
                        self.nested_outputs["Scenario"]["Site"][name]['lcoe_us_dollars_per_kwh'] = None
                elif name == "Storage":
                    self.nested_outputs["Scenario"]["Site"][name]["size_kw"] = self.results_dict.get("batt_kw", 0)
                    self.nested_outputs["Scenario"]["Site"][name]["size_kwh"] = self.results_dict.get("batt_kwh", 0)
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_to_load_series_kw"] = self.results_dict.get("ElecFromBatt")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_to_grid_series_kw"] = self.results_dict.get("ElecFromBattExport")
                    self.nested_outputs["Scenario"]["Site"][name]["year_one_soc_series_pct"] = \
                        self.results_dict.get("year_one_soc_series_pct")
                    self.nested_outputs["Scenario"]["Site"][name]["sr_provided_series_kw"] = \
                        self.results_dict.get("sr_provided_batt")
                elif name == "ElectricTariff":
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_energy_cost_us_dollars"] = self.results_dict.get("year_one_energy_cost")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_demand_cost_us_dollars"] = self.results_dict.get("year_one_demand_cost")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_fixed_cost_us_dollars"] = self.results_dict.get("year_one_fixed_cost")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_min_charge_adder_us_dollars"] = self.results_dict.get("year_one_min_charge_adder")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_coincident_peak_cost_us_dollars"] = self.results_dict.get("year_one_coincident_peak_cost")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_energy_cost_bau_us_dollars"] = self.results_dict.get("year_one_energy_cost_bau")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_demand_cost_bau_us_dollars"] = self.results_dict.get("year_one_demand_cost_bau")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_fixed_cost_bau_us_dollars"] = self.results_dict.get("year_one_fixed_cost_bau")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_min_charge_adder_bau_us_dollars"] = self.results_dict.get(
                        "year_one_min_charge_adder_bau")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_coincident_peak_cost_bau_us_dollars"] = self.results_dict.get("year_one_coincident_peak_cost_bau")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "total_energy_cost_us_dollars"] = self.results_dict.get("total_energy_cost")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "total_demand_cost_us_dollars"] = self.results_dict.get("total_demand_cost")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "total_fixed_cost_us_dollars"] = self.results_dict.get("total_fixed_cost")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "total_min_charge_adder_us_dollars"] = self.results_dict.get("total_min_charge_adder")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "total_coincident_peak_cost_us_dollars"] = self.results_dict.get("total_coincident_peak_cost")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "total_energy_cost_bau_us_dollars"] = self.results_dict.get("total_energy_cost_bau")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "total_demand_cost_bau_us_dollars"] = self.results_dict.get("total_demand_cost_bau")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "total_fixed_cost_bau_us_dollars"] = self.results_dict.get("total_fixed_cost_bau")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "total_min_charge_adder_bau_us_dollars"] = self.results_dict.get("total_min_charge_adder_bau")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "total_coincident_peak_cost_bau_us_dollars"] = self.results_dict.get("total_coincident_peak_cost_bau")
                    self.nested_outputs["Scenario"]["Site"][name]["year_one_bill_us_dollars"] = self.results_dict.get(
                        "year_one_bill")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_bill_bau_us_dollars"] = self.results_dict.get("year_one_bill_bau")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_export_benefit_us_dollars"] = self.results_dict.get("year_one_export_benefit")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_export_benefit_bau_us_dollars"] = self.results_dict.get("year_one_export_benefit_bau")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "total_export_benefit_us_dollars"] = self.results_dict.get("total_export_benefit")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "total_export_benefit_bau_us_dollars"] = self.results_dict.get("total_export_benefit_bau")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_energy_cost_series_us_dollars_per_kwh"] = \
                        self.dm.get('year_one_energy_cost_series_us_dollars_per_kwh')
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_demand_cost_series_us_dollars_per_kw"] = \
                        self.dm.get('year_one_demand_cost_series_us_dollars_per_kw')
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_to_load_series_kw"] = self.results_dict.get('GridToLoad')
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_to_load_series_bau_kw"] = self.results_dict.get('GridToLoad_bau')
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_to_battery_series_kw"] = self.results_dict.get('GridToBatt')
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_energy_supplied_kwh"] = self.results_dict.get("year_one_utility_kwh")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_energy_supplied_kwh_bau"] = self.results_dict.get("year_one_utility_kwh_bau")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_chp_standby_cost_us_dollars"] = self.results_dict.get("year_one_chp_standby_cost")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "total_chp_standby_cost_us_dollars"] = self.results_dict.get("total_chp_standby_cost")
                elif name == "FuelTariff":
                    self.nested_outputs["Scenario"]["Site"][name][
                        "total_boiler_fuel_cost_us_dollars"] = self.results_dict.get("total_boiler_fuel_cost")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "total_boiler_fuel_cost_bau_us_dollars"] = self.results_dict.get("total_boiler_fuel_cost_bau")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_boiler_fuel_cost_us_dollars"] = self.results_dict.get("year_one_boiler_fuel_cost")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_boiler_fuel_cost_bau_us_dollars"] = self.results_dict.get("year_one_boiler_fuel_cost_bau")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "total_chp_fuel_cost_us_dollars"] = self.results_dict.get("total_chp_fuel_cost")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_chp_fuel_cost_us_dollars"] = self.results_dict.get("year_one_chp_fuel_cost")
                elif name == "Generator":
                    self.nested_outputs["Scenario"]["Site"][name]["size_kw"] = self.results_dict.get("generator_kw", 0)
                    self.nested_outputs["Scenario"]["Site"][name]["fuel_used_gal"] = self.results_dict.get(
                        "fuel_used_kwh") / GAL_DIESEL_TO_KWH
                    if self.results_dict.get("fuel_used_kwh_series") is None:
                        self.nested_outputs["Scenario"]["Site"][name]["fuel_used_series_gal"] = self.results_dict.get("fuel_used_kwh_series")
                    else:
                        self.nested_outputs["Scenario"]["Site"][name]["fuel_used_series_gal"] = [i/GAL_DIESEL_TO_KWH for i in self.results_dict.get(
                            "fuel_used_kwh_series")] 
                    self.nested_outputs["Scenario"]["Site"][name]["fuel_used_gal_bau"] = self.results_dict.get(
                        "fuel_used_kwh_bau") / GAL_DIESEL_TO_KWH
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_to_load_series_kw"] = self.results_dict.get('GENERATORtoLoad')
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_to_battery_series_kw"] = self.results_dict.get('GENERATORtoBatt')
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_to_grid_series_kw"] = self.results_dict.get('GENERATORtoGrid')
                    self.nested_outputs["Scenario"]["Site"][name][
                        "average_yearly_energy_produced_kwh"] = self.results_dict.get(
                        "average_yearly_gen_energy_produced")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "average_yearly_energy_exported_kwh"] = self.results_dict.get(
                        "average_annual_energy_exported_gen")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_energy_produced_kwh"] = self.results_dict.get(
                        "year_one_gen_energy_produced")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_power_production_series_kw"] = self.compute_total_power(name)
                    self.nested_outputs["Scenario"]["Site"][name][
                        "existing_gen_total_fixed_om_cost_us_dollars"] = self.results_dict.get(
                        "gen_net_fixed_om_costs_bau")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "total_fixed_om_cost_us_dollars"] = self.results_dict.get("gen_net_fixed_om_costs")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_fixed_om_cost_us_dollars"] = self.results_dict.get("gen_year_one_fixed_om_costs")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "existing_gen_total_variable_om_cost_us_dollars"] = self.results_dict.get(
                        "gen_net_variable_om_costs_bau")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "existing_gen_year_one_variable_om_cost_us_dollars"] = self.results_dict.get(
                        "gen_year_one_variable_om_costs_bau")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "total_variable_om_cost_us_dollars"] = self.results_dict.get(
                        "gen_net_variable_om_costs")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_variable_om_cost_us_dollars"] = self.results_dict.get(
                        "gen_year_one_variable_om_costs")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "total_fuel_cost_us_dollars"] = self.results_dict.get(
                        "gen_total_fuel_cost")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_fuel_cost_us_dollars"] = self.results_dict.get(
                        "gen_year_one_fuel_cost")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "existing_gen_total_fuel_cost_us_dollars"] = self.results_dict.get(
                        "gen_total_fuel_cost_bau")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "existing_gen_year_one_fuel_cost_us_dollars"] = self.results_dict.get(
                        "gen_year_one_fuel_cost_bau")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "sr_provided_series_kw"] = self.results_dict.get(
                        "sr_provided_gen")
                elif name == "CHP":
                    self.nested_outputs["Scenario"]["Site"][name][
                        "size_kw"] = self.results_dict.get("chp_kw")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_fuel_used_mmbtu"] = self.results_dict.get("year_one_chp_fuel_used") / MMBTU_TO_KWH
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_electric_energy_produced_kwh"] = self.results_dict.get("year_one_chp_electric_energy_produced")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_thermal_energy_produced_mmbtu"] = self.results_dict.get("year_one_chp_thermal_energy_produced") / MMBTU_TO_KWH
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_electric_production_series_kw"] = self.results_dict.get("chp_electric_production_series")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_to_battery_series_kw"] = self.results_dict.get("chp_to_battery_series")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_to_load_series_kw"] = self.results_dict.get("chp_electric_to_load_series")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_to_grid_series_kw"] = self.results_dict.get("chp_to_grid_series")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_thermal_to_load_series_mmbtu_per_hour"] = [x / MMBTU_TO_KWH for x in self.results_dict.get("chp_thermal_to_load_series")]
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_thermal_to_tes_series_mmbtu_per_hour"] = [x / MMBTU_TO_KWH for x in self.results_dict.get("chp_thermal_to_tes_series")]
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_thermal_to_waste_series_mmbtu_per_hour"] = [x / MMBTU_TO_KWH for x in self.results_dict.get("chp_thermal_to_waste_series")]
                elif name == "Boiler":
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_boiler_fuel_consumption_series_mmbtu_per_hr"] = [x / MMBTU_TO_KWH for x in self.results_dict.get("fuel_to_boiler_series")]
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_boiler_thermal_production_series_mmbtu_per_hr"] = [x / MMBTU_TO_KWH for x in self.results_dict.get("boiler_thermal_production_series")]
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_thermal_to_load_series_mmbtu_per_hour"] = [x / MMBTU_TO_KWH for x in self.results_dict.get("boiler_thermal_to_load_series")]
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_thermal_to_tes_series_mmbtu_per_hour"] = [x / MMBTU_TO_KWH for x in self.results_dict.get("boiler_thermal_to_tes_series")]
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_boiler_fuel_consumption_mmbtu"] = self.results_dict.get("year_one_fuel_to_boiler_kwh") / MMBTU_TO_KWH
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_boiler_thermal_production_mmbtu"] = self.results_dict.get("year_one_boiler_thermal_production_kwh") / MMBTU_TO_KWH
                elif name == "ElectricChiller":
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_electric_chiller_thermal_to_load_series_ton"] = [x / TONHOUR_TO_KWHT for x in self.results_dict.get("electric_chiller_to_load_series")]
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_electric_chiller_thermal_to_tes_series_ton"] =  [x / TONHOUR_TO_KWHT for x in self.results_dict.get("electric_chiller_to_tes_series")]
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_electric_chiller_electric_consumption_series_kw"] = self.results_dict.get("electric_chiller_consumption_series")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_electric_chiller_electric_consumption_kwh"] = self.results_dict.get("year_one_electric_chiller_electric_kwh")
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_electric_chiller_thermal_production_tonhr"] = self.results_dict.get("year_one_electric_chiller_thermal_kwh") / TONHOUR_TO_KWHT
                elif name == "AbsorptionChiller":
                    self.nested_outputs["Scenario"]["Site"][name][
                        "size_ton"] = self.results_dict.get("absorpchl_kw") / TONHOUR_TO_KWHT
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_absorp_chl_thermal_to_load_series_ton"] = [x / TONHOUR_TO_KWHT for x in self.results_dict.get("absorption_chiller_to_load_series")]
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_absorp_chl_thermal_to_tes_series_ton"] = [x / TONHOUR_TO_KWHT for x in self.results_dict.get("absorption_chiller_to_tes_series")]
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_absorp_chl_thermal_consumption_series_mmbtu_per_hr"] = [x / MMBTU_TO_KWH for x in self.results_dict.get("absorption_chiller_consumption_series")]
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_absorp_chl_thermal_consumption_mmbtu"] = self.results_dict.get("year_one_absorp_chiller_thermal_consumption_kwh") / MMBTU_TO_KWH
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_absorp_chl_thermal_production_tonhr"] = self.results_dict.get("year_one_absorp_chiller_thermal_prod_kwh") / TONHOUR_TO_KWHT
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_absorp_chl_electric_consumption_series_kw"] = self.results_dict.get("absorption_chiller_electric_consumption_series")                
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_absorp_chl_electric_consumption_kwh"] = self.results_dict.get("year_one_absorp_chiller_electric_consumption_kwh")
                elif name == "HotTES":
                    self.nested_outputs["Scenario"]["Site"][name][
                        "size_gal"] = self.results_dict.get("hot_tes_size_kwh",0) / HotTES.gal_to_kwh_conversion
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_thermal_from_hot_tes_series_mmbtu_per_hr"] = [x / MMBTU_TO_KWH for x in self.results_dict.get("hot_tes_thermal_production_series")]
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_hot_tes_soc_series_pct"] = self.results_dict.get("hot_tes_pct_soc_series")
                elif name == "ColdTES":
                    self.nested_outputs["Scenario"]["Site"][name][
                        "size_gal"] = self.results_dict.get("cold_tes_size_kwht",0) / ColdTES.gal_to_kwh_conversion
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_thermal_from_cold_tes_series_ton"] = [x / TONHOUR_TO_KWHT for x in self.results_dict.get("cold_tes_thermal_production_series")]
                    self.nested_outputs["Scenario"]["Site"][name][
                        "year_one_cold_tes_soc_series_pct"] = self.results_dict.get("cold_tes_pct_soc_series")

            # outputs that depend on multiple object results:
            future_replacement_cost, present_replacement_cost = self.replacement_costs_future_and_present
            self.nested_outputs["Scenario"]["Site"]["Financial"]["initial_capital_costs"] = self.upfront_capex
            self.nested_outputs["Scenario"]["Site"]["Financial"]["replacement_costs"] = future_replacement_cost
            self.nested_outputs["Scenario"]["Site"]["Financial"]["om_and_replacement_present_cost_after_tax_us_dollars"] = \
                present_replacement_cost + self.results_dict.get("total_om_costs_after_tax", 0)
            self.nested_outputs["Scenario"]["Site"]["Financial"]["initial_capital_costs_after_incentives"] = \
                self.upfront_capex_after_incentives
            if self.third_party_factor != 1:
                self.nested_outputs["Scenario"]["Site"]["Financial"][
                    "developer_om_and_replacement_present_cost_after_tax_us_dollars"] = \
                    self.nested_outputs["Scenario"]["Site"]["Financial"][
                        "om_and_replacement_present_cost_after_tax_us_dollars"] / self.third_party_factor
            if self.nested_outputs["Scenario"]["Site"]["LoadProfile"]["annual_calculated_kwh"] > 0:
                self.nested_outputs["Scenario"]["Site"]["renewable_electricity_energy_pct"] = \
                    self.nested_outputs["Scenario"]["Site"]["Wind"].get("average_yearly_energy_produced_kwh") or 0
                for pv in self.nested_outputs["Scenario"]["Site"]["PV"]:
                    self.nested_outputs["Scenario"]["Site"]["renewable_electricity_energy_pct"] += \
                    pv.get("average_yearly_energy_produced_kwh") or 0
                self.nested_outputs["Scenario"]["Site"]["renewable_electricity_energy_pct"] = round(
                    self.nested_outputs["Scenario"]["Site"]["renewable_electricity_energy_pct"] /
                    self.nested_outputs["Scenario"]["Site"]["LoadProfile"]["annual_calculated_kwh"], 4)
            else:
                #If this is not set to None it will contain a dictionary of data parameters
                self.nested_outputs["Scenario"]["Site"]["renewable_electricity_energy_pct"] = None

            time_outputs = [k for k in self.bau_attributes if (k.startswith("julia") or k.startswith("pyjulia"))]

            for k in time_outputs:
                self.nested_outputs["Scenario"]["Profile"][k] = self.results_dict.get(k)
                self.nested_outputs["Scenario"]["Profile"][k + "_bau"] = self.results_dict.get(k + "_bau")

            lcoe_component_fuel, lcoe_component_re_capex, lcoe_component_diesel_capex, lcoe_component_other_capex, \
            lcoe_component_om, lcoe_component_other_annual_costs = self.get_offgrid_lcoe_breakdown
            self.nested_outputs["Scenario"]["Site"]["Financial"]["lcoe_component_fuel_us_dollars_per_kwh"] = lcoe_component_fuel
            self.nested_outputs["Scenario"]["Site"]["Financial"]["lcoe_component_re_capex_us_dollars_per_kwh"] = lcoe_component_re_capex
            self.nested_outputs["Scenario"]["Site"]["Financial"]["lcoe_component_diesel_capex_us_dollars_per_kwh"] = lcoe_component_diesel_capex
            self.nested_outputs["Scenario"]["Site"]["Financial"]["lcoe_component_other_capex_us_dollars_per_kwh"] = lcoe_component_other_capex
            self.nested_outputs["Scenario"]["Site"]["Financial"]["lcoe_component_om_us_dollars_per_kwh"] = lcoe_component_om
            self.nested_outputs["Scenario"]["Site"]["Financial"]["lcoe_component_other_annual_costs_us_dollars_per_kwh"] = lcoe_component_other_annual_costs

        def compute_total_power(self, tech):
            power_lists = list()
            d = self.nested_outputs["Scenario"]["Site"][tech]

            if d.get("year_one_to_load_series_kw") is not None:
                power_lists.append(d["year_one_to_load_series_kw"])

            if d.get("year_one_to_battery_series_kw") is not None:
                power_lists.append(d["year_one_to_battery_series_kw"])

            if d.get("year_one_to_grid_series_kw") is not None:
                power_lists.append(d["year_one_to_grid_series_kw"])

            power = [sum(x) for x in zip(*power_lists)]
            return power

    self.data = data
    self.run_uuid = data['outputs']['Scenario']['run_uuid']
    self.user_uuid = data['outputs']['Scenario'].get('user_uuid')

    try:
        results_object = Results(results_dict=dfm_list[0]['results'], results_dict_bau=dfm_list[1]['results_bau'],
                                 dm=dfm_list[0], inputs=data['inputs']['Scenario']['Site'])
        results = results_object.get_output()

        data['outputs'].update(results)
        data['outputs']['Scenario'].update(meta)  # run_uuid and api_version

        #simple payback needs all data to be computed so running that calculation here
        simple_payback, irr, net_present_cost, annualized_payment_to_third_party_us_dollars, \
        offtaker_annual_free_cashflow_series_us_dollars, offtaker_annual_free_cashflow_series_bau_us_dollars, \
        offtaker_discounted_annual_free_cashflow_series_us_dollars, offtaker_discounted_annual_free_cashflow_series_bau_us_dollars,\
        developer_annual_free_cashflow_series_us_dollars = \
            calculate_proforma_metrics(data)
        data['outputs']['Scenario']['Site']['Financial']['simple_payback_years'] = simple_payback
        data['outputs']['Scenario']['Site']['Financial']['irr_pct'] = irr if not np.isnan(irr or np.nan) else None
        data['outputs']['Scenario']['Site']['Financial']['net_present_cost_us_dollars'] = net_present_cost
        data['outputs']['Scenario']['Site']['Financial']['annualized_payment_to_third_party_us_dollars'] = \
            annualized_payment_to_third_party_us_dollars
        data['outputs']['Scenario']['Site']['Financial']['developer_annual_free_cashflow_series_us_dollars'] = \
            developer_annual_free_cashflow_series_us_dollars
        data['outputs']['Scenario']['Site']['Financial']['offtaker_annual_free_cashflow_series_us_dollars'] = \
            offtaker_annual_free_cashflow_series_us_dollars
        data['outputs']['Scenario']['Site']['Financial']['offtaker_annual_free_cashflow_series_bau_us_dollars'] = \
            offtaker_annual_free_cashflow_series_bau_us_dollars
        data['outputs']['Scenario']['Site']['Financial']['offtaker_discounted_annual_free_cashflow_series_us_dollars'] = \
            offtaker_discounted_annual_free_cashflow_series_us_dollars
        data['outputs']['Scenario']['Site']['Financial']['offtaker_discounted_annual_free_cashflow_series_bau_us_dollars'] = \
            offtaker_discounted_annual_free_cashflow_series_bau_us_dollars

        data = EmissionsCalculator.add_to_data(data)

        pv_watts_station_check = data['outputs']['Scenario']['Site']['PV'][0].get('station_distance_km') or 0
        if pv_watts_station_check > 322:
            pv_warning = ("The best available solar resource data is {} miles from the site's coordinates."
                " Beyond 200 miles, we display this warning. Consider choosing an alternative location closer"
                " to the continental US with similar solar irradiance and weather patterns and rerunning the analysis."
                " For more information, see https://maps.nrel.gov/nsrdb-viewer/ and the documenation at https://nsrdb.nrel.gov/"
             ).format(round(pv_watts_station_check*0.621,0))

            if data.get('messages') is None:
                data['messages'] = {"PVWatts Warning": pv_warning}
            else:
                data['messages']["PVWatts Warning"] = pv_warning

        # Calculate avoided outage costs moved to resilience stats
        #calc_avoided_outage_costs(data, present_worth_factor=dfm_list[0]['pwf_e'], run_uuid=self.run_uuid)

        data = EmissionsCalculator.add_to_data(data)
        if len(data['outputs']['Scenario']['Site']['PV']) == 1:
            data['outputs']['Scenario']['Site']['PV'] = data['outputs']['Scenario']['Site']['PV'][0]

        profiler.profileEnd()
        data['outputs']["Scenario"]["Profile"]["parse_run_outputs_seconds"] = profiler.getDuration()

        if saveToDB:
            ModelManager.update(data, run_uuid=self.run_uuid)

    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        log.info("Results.py raising the error: {}, detail: {}".format(exc_type, exc_value))
        raise UnexpectedError(exc_type, exc_value.args[0], traceback.format_tb(exc_traceback), task=self.name, run_uuid=self.run_uuid,
                              user_uuid=self.user_uuid)
