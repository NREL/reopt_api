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
def nested_to_flat(nested_output):
    """
    Convenience function for comparing two results dictionary.
    Used in many built-in tests (before passing both dicts to check_common_outputs).

    Arguments:
        nested_output: dict, API response
    """
    base = {

        'run_uuid': nested_output['Scenario']['run_uuid'],
        'api_version': nested_output['Scenario']['api_version'],
        'status': nested_output['Scenario']['status'],

        'year_one_electric_load_series': nested_output['Scenario']['Site']['LoadProfile']['year_one_electric_load_series_kw'],

        'lcc': nested_output['Scenario']['Site']['Financial']['lcc_us_dollars'],
        'lcc_bau': nested_output['Scenario']['Site']['Financial']['lcc_bau_us_dollars'],
        'npv': nested_output['Scenario']['Site']['Financial']['npv_us_dollars'],
        'net_capital_costs_plus_om': nested_output['Scenario']['Site']['Financial']['net_capital_costs_plus_om_us_dollars'],
        'avoided_outage_costs_us_dollars': nested_output['Scenario']['Site']['Financial']['avoided_outage_costs_us_dollars'],
        'microgrid_upgrade_cost_us_dollars': nested_output['Scenario']['Site']['Financial']['microgrid_upgrade_cost_us_dollars'],

        'pv_kw': nested_output['Scenario']['Site']['PV']['size_kw'],
        'year_one_energy_produced': nested_output['Scenario']['Site']['PV']['year_one_energy_produced_kwh'],
        'pv_kw_ac_hourly': nested_output['Scenario']['Site']['PV']['year_one_power_production_series_kw'],
        'average_yearly_pv_energy_produced': nested_output['Scenario']['Site']['PV']['average_yearly_energy_produced_kwh'],
        'average_annual_energy_exported': nested_output['Scenario']['Site']['PV']['average_yearly_energy_exported_kwh'],
        'year_one_pv_to_battery_series': nested_output['Scenario']['Site']['PV']['year_one_to_battery_series_kw'],
        'year_one_pv_to_load_series': nested_output['Scenario']['Site']['PV']['year_one_to_load_series_kw'],
        'year_one_pv_to_grid_series': nested_output['Scenario']['Site']['PV']['year_one_to_grid_series_kw'],
        'existing_pv_om_cost_us_dollars': nested_output['Scenario']['Site']['PV']['existing_pv_om_cost_us_dollars'],

        'batt_kw': nested_output['Scenario']['Site']['Storage']['size_kw'],
        'batt_kwh': nested_output['Scenario']['Site']['Storage']['size_kwh'],
        'year_one_battery_to_load_series': nested_output['Scenario']['Site']['Storage']['year_one_to_load_series_kw'],
        'year_one_battery_to_grid_series': nested_output['Scenario']['Site']['Storage']['year_one_to_grid_series_kw'],
        'year_one_battery_soc_series': nested_output['Scenario']['Site']['Storage']['year_one_soc_series_pct'],

        'year_one_energy_cost': nested_output['Scenario']['Site']['ElectricTariff']['year_one_energy_cost_us_dollars'],
        'year_one_demand_cost': nested_output['Scenario']['Site']['ElectricTariff']['year_one_demand_cost_us_dollars'],
        'year_one_fixed_cost': nested_output['Scenario']['Site']['ElectricTariff']['year_one_fixed_cost_us_dollars'],
        'year_one_min_charge_adder': nested_output['Scenario']['Site']['ElectricTariff']['year_one_min_charge_adder_us_dollars'],
        'year_one_energy_cost_bau': nested_output['Scenario']['Site']['ElectricTariff']['year_one_energy_cost_bau_us_dollars'],
        'year_one_demand_cost_bau': nested_output['Scenario']['Site']['ElectricTariff']['year_one_demand_cost_bau_us_dollars'],
        'year_one_fixed_cost_bau': nested_output['Scenario']['Site']['ElectricTariff']['year_one_fixed_cost_bau_us_dollars'],
        'year_one_min_charge_adder_bau': nested_output['Scenario']['Site']['ElectricTariff']['year_one_min_charge_adder_bau_us_dollars'],
        'total_energy_cost': nested_output['Scenario']['Site']['ElectricTariff']['total_energy_cost_us_dollars'],
        'total_demand_cost': nested_output['Scenario']['Site']['ElectricTariff']['total_demand_cost_us_dollars'],
        'total_fixed_cost': nested_output['Scenario']['Site']['ElectricTariff']['total_fixed_cost_us_dollars'],
        'total_min_charge_adder': nested_output['Scenario']['Site']['ElectricTariff']['total_min_charge_adder_us_dollars'],
        'total_energy_cost_bau': nested_output['Scenario']['Site']['ElectricTariff']['total_energy_cost_bau_us_dollars'],
        'total_demand_cost_bau': nested_output['Scenario']['Site']['ElectricTariff']['total_demand_cost_bau_us_dollars'],
        'total_fixed_cost_bau': nested_output['Scenario']['Site']['ElectricTariff']['total_fixed_cost_bau_us_dollars'],
        'total_min_charge_adder_bau': nested_output['Scenario']['Site']['ElectricTariff']['total_min_charge_adder_bau_us_dollars'],
        'year_one_bill': nested_output['Scenario']['Site']['ElectricTariff']['year_one_bill_us_dollars'],
        'year_one_bill_bau': nested_output['Scenario']['Site']['ElectricTariff']['year_one_bill_bau_us_dollars'],
        'year_one_export_benefit': nested_output['Scenario']['Site']['ElectricTariff']['year_one_export_benefit_us_dollars'],
        'year_one_grid_to_load_series': nested_output['Scenario']['Site']['ElectricTariff']['year_one_to_load_series_kw'],
        'year_one_grid_to_battery_series': nested_output['Scenario']['Site']['ElectricTariff']['year_one_to_battery_series_kw'],
        'year_one_energy_cost_series': nested_output['Scenario']['Site']['ElectricTariff']['year_one_energy_cost_series_us_dollars_per_kwh'],
        'year_one_demand_cost_series': nested_output['Scenario']['Site']['ElectricTariff']['year_one_demand_cost_series_us_dollars_per_kw'],
        'year_one_utility_kwh': nested_output['Scenario']['Site']['ElectricTariff']['year_one_energy_supplied_kwh'],
        'year_one_payments_to_third_party_owner': None,
        'total_payments_to_third_party_owner': None,
        'year_one_coincident_peak_cost': nested_output['Scenario']['Site']['ElectricTariff']['year_one_coincident_peak_cost_us_dollars'],
        'year_one_coincident_peak_cost_bau': nested_output['Scenario']['Site']['ElectricTariff']['year_one_coincident_peak_cost_bau_us_dollars'],
        'total_coincident_peak_cost': nested_output['Scenario']['Site']['ElectricTariff']['total_coincident_peak_cost_us_dollars'],
        'total_coincident_peak_cost_bau': nested_output['Scenario']['Site']['ElectricTariff']['total_coincident_peak_cost_bau_us_dollars']
    }
    if nested_output['Scenario']['Site'].get('Wind') is not None:
        base.update({
            'wind_kw':nested_output['Scenario']['Site']['Wind']['size_kw'],
            'average_yearly_wind_energy_produced':nested_output['Scenario']['Site']['Wind']['average_yearly_energy_produced_kwh'],
            'average_annual_energy_exported_wind': nested_output['Scenario']['Site']['Wind']['average_yearly_energy_exported_kwh'],
            'year_one_wind_to_battery_series': nested_output['Scenario']['Site']['Wind']['year_one_to_battery_series_kw'],
            'year_one_wind_to_load_series': nested_output['Scenario']['Site']['Wind']['year_one_to_load_series_kw'],
            'year_one_wind_to_grid_series': nested_output['Scenario']['Site']['Wind']['year_one_to_grid_series_kw']
       })
    if nested_output['Scenario']['Site'].get('Generator') is not None:
        base.update({
            'gen_kw':nested_output['Scenario']['Site']['Generator']['size_kw'],
            'average_yearly_gen_energy_produced':nested_output['Scenario']['Site']['Generator']['average_yearly_energy_produced_kwh'],
            'average_annual_energy_exported_gen': nested_output['Scenario']['Site']['Generator']['average_yearly_energy_exported_kwh'],
            'year_one_gen_to_battery_series': nested_output['Scenario']['Site']['Generator']['year_one_to_battery_series_kw'],
            'year_one_gen_to_load_series': nested_output['Scenario']['Site']['Generator']['year_one_to_load_series_kw'],
            'year_one_gen_to_grid_series': nested_output['Scenario']['Site']['Generator']['year_one_to_grid_series_kw'],
            'fuel_used_gal': nested_output['Scenario']['Site']['Generator']['fuel_used_gal'],
            'existing_gen_total_fixed_om_cost_us_dollars': nested_output['Scenario']['Site']['Generator']['existing_gen_total_fixed_om_cost_us_dollars'],
            'existing_gen_total_variable_om_cost_us_dollars': nested_output['Scenario']['Site']['Generator'][
                'existing_gen_total_variable_om_cost_us_dollars'],
            'total_fuel_cost_us_dollars': nested_output['Scenario']['Site']['Generator'][
                'total_fuel_cost_us_dollars'],
            'gen_total_variable_om_cost_us_dollars': nested_output['Scenario']['Site']['Generator'][
                'total_variable_om_cost_us_dollars'],
            'existing_gen_total_fuel_cost_us_dollars': nested_output['Scenario']['Site']['Generator'][
                'existing_gen_total_fuel_cost_us_dollars'],
       })
    return base

def nested_to_flat_chp(nested_output):
    base = {

        'run_uuid': nested_output['Scenario']['run_uuid'],
        'api_version': nested_output['Scenario']['api_version'],
        'status': nested_output['Scenario']['status'],

        'year_one_electric_load_series': nested_output['Scenario']['Site']['LoadProfile'][
            'year_one_electric_load_series_kw'],

        'lcc': nested_output['Scenario']['Site']['Financial']['lcc_us_dollars'],
        'lcc_bau': nested_output['Scenario']['Site']['Financial']['lcc_bau_us_dollars'],
        'npv': nested_output['Scenario']['Site']['Financial']['npv_us_dollars'],
        'net_capital_costs_plus_om': nested_output['Scenario']['Site']['Financial'][
            'net_capital_costs_plus_om_us_dollars'],
        'avoided_outage_costs_us_dollars': nested_output['Scenario']['Site']['Financial'][
            'avoided_outage_costs_us_dollars'],
        'microgrid_upgrade_cost_us_dollars': nested_output['Scenario']['Site']['Financial'][
            'microgrid_upgrade_cost_us_dollars'],

        'year_one_energy_cost': nested_output['Scenario']['Site']['ElectricTariff']['year_one_energy_cost_us_dollars'],
        'year_one_demand_cost': nested_output['Scenario']['Site']['ElectricTariff']['year_one_demand_cost_us_dollars'],
        'year_one_fixed_cost': nested_output['Scenario']['Site']['ElectricTariff']['year_one_fixed_cost_us_dollars'],
        'year_one_min_charge_adder': nested_output['Scenario']['Site']['ElectricTariff'][
            'year_one_min_charge_adder_us_dollars'],
        'year_one_energy_cost_bau': nested_output['Scenario']['Site']['ElectricTariff'][
            'year_one_energy_cost_bau_us_dollars'],
        'year_one_demand_cost_bau': nested_output['Scenario']['Site']['ElectricTariff'][
            'year_one_demand_cost_bau_us_dollars'],
        'year_one_fixed_cost_bau': nested_output['Scenario']['Site']['ElectricTariff'][
            'year_one_fixed_cost_bau_us_dollars'],
        'year_one_min_charge_adder_bau': nested_output['Scenario']['Site']['ElectricTariff'][
            'year_one_min_charge_adder_bau_us_dollars'],
        'total_energy_cost': nested_output['Scenario']['Site']['ElectricTariff']['total_energy_cost_us_dollars'],
        'total_demand_cost': nested_output['Scenario']['Site']['ElectricTariff']['total_demand_cost_us_dollars'],
        'total_fixed_cost': nested_output['Scenario']['Site']['ElectricTariff']['total_fixed_cost_us_dollars'],
        'total_min_charge_adder': nested_output['Scenario']['Site']['ElectricTariff'][
            'total_min_charge_adder_us_dollars'],
        'total_energy_cost_bau': nested_output['Scenario']['Site']['ElectricTariff'][
            'total_energy_cost_bau_us_dollars'],
        'total_demand_cost_bau': nested_output['Scenario']['Site']['ElectricTariff'][
            'total_demand_cost_bau_us_dollars'],
        'total_fixed_cost_bau': nested_output['Scenario']['Site']['ElectricTariff']['total_fixed_cost_bau_us_dollars'],
        'total_min_charge_adder_bau': nested_output['Scenario']['Site']['ElectricTariff'][
            'total_min_charge_adder_bau_us_dollars'],
        'year_one_bill': nested_output['Scenario']['Site']['ElectricTariff']['year_one_bill_us_dollars'],
        'year_one_bill_bau': nested_output['Scenario']['Site']['ElectricTariff']['year_one_bill_bau_us_dollars'],
        'year_one_export_benefit': nested_output['Scenario']['Site']['ElectricTariff'][
            'year_one_export_benefit_us_dollars'],
        'year_one_grid_to_load_series': nested_output['Scenario']['Site']['ElectricTariff'][
            'year_one_to_load_series_kw'],
        'year_one_grid_to_battery_series': nested_output['Scenario']['Site']['ElectricTariff'][
            'year_one_to_battery_series_kw'],
        'year_one_energy_cost_series': nested_output['Scenario']['Site']['ElectricTariff'][
            'year_one_energy_cost_series_us_dollars_per_kwh'],
        'year_one_demand_cost_series': nested_output['Scenario']['Site']['ElectricTariff'][
            'year_one_demand_cost_series_us_dollars_per_kw'],
        'year_one_utility_kwh': nested_output['Scenario']['Site']['ElectricTariff']['year_one_energy_supplied_kwh'],
        'year_one_payments_to_third_party_owner': None,
        'total_payments_to_third_party_owner': None,
        'total_om_costs': nested_output['Scenario']['Site']['Financial'][
            'total_om_costs_us_dollars'],
        'year_one_om_costs': nested_output['Scenario']['Site']['Financial'][
            'year_one_om_costs_us_dollars']
    }
    if nested_output['Scenario']['Site'].get('PV') is not None:
        base.update({
            'pv_kw': nested_output['Scenario']['Site']['PV']['size_kw'],
            'year_one_energy_produced': nested_output['Scenario']['Site']['PV']['year_one_energy_produced_kwh'],
            'pv_kw_ac_hourly': nested_output['Scenario']['Site']['PV']['year_one_power_production_series_kw'],
            'average_yearly_pv_energy_produced': nested_output['Scenario']['Site']['PV'][
                'average_yearly_energy_produced_kwh'],
            'average_annual_energy_exported': nested_output['Scenario']['Site']['PV']['average_yearly_energy_exported_kwh'],
            'year_one_pv_to_battery_series': nested_output['Scenario']['Site']['PV']['year_one_to_battery_series_kw'],
            'year_one_pv_to_load_series': nested_output['Scenario']['Site']['PV']['year_one_to_load_series_kw'],
            'year_one_pv_to_grid_series': nested_output['Scenario']['Site']['PV']['year_one_to_grid_series_kw'],
            'existing_pv_om_cost_us_dollars': nested_output['Scenario']['Site']['PV']['existing_pv_om_cost_us_dollars'],
        })
    if nested_output['Scenario']['Site'].get('Storage') is not None:
        base.update({
            'batt_kw': nested_output['Scenario']['Site']['Storage']['size_kw'],
            'batt_kwh': nested_output['Scenario']['Site']['Storage']['size_kwh'],
            'year_one_battery_to_load_series': nested_output['Scenario']['Site']['Storage']['year_one_to_load_series_kw'],
            'year_one_battery_to_grid_series': nested_output['Scenario']['Site']['Storage']['year_one_to_grid_series_kw'],
            'year_one_battery_soc_series': nested_output['Scenario']['Site']['Storage']['year_one_soc_series_pct'],
        })
    if nested_output['Scenario']['Site'].get('Generator') is not None:
        base.update({
            'gen_kw':nested_output['Scenario']['Site']['Generator']['size_kw'],
            'average_yearly_gen_energy_produced':nested_output['Scenario']['Site']['Generator']['average_yearly_energy_produced_kwh'],
            'average_annual_energy_exported_gen': nested_output['Scenario']['Site']['Generator']['average_yearly_energy_exported_kwh'],
            'year_one_gen_to_battery_series': nested_output['Scenario']['Site']['Generator']['year_one_to_battery_series_kw'],
            'year_one_gen_to_load_series': nested_output['Scenario']['Site']['Generator']['year_one_to_load_series_kw'],
            'year_one_gen_to_grid_series': nested_output['Scenario']['Site']['Generator']['year_one_to_grid_series_kw'],
            'fuel_used_gal': nested_output['Scenario']['Site']['Generator']['fuel_used_gal'],
            'existing_gen_total_fixed_om_cost_us_dollars': nested_output['Scenario']['Site']['Generator']['existing_gen_total_fixed_om_cost_us_dollars'],
            'existing_gen_total_variable_om_cost_us_dollars': nested_output['Scenario']['Site']['Generator'][
                'existing_gen_total_variable_om_cost_us_dollars'],
            'total_fuel_cost_us_dollars': nested_output['Scenario']['Site']['Generator'][
                'total_fuel_cost_us_dollars'],
            'gen_total_variable_om_cost_us_dollars': nested_output['Scenario']['Site']['Generator'][
                'total_variable_om_cost_us_dollars'],
            'existing_gen_total_fuel_cost_us_dollars': nested_output['Scenario']['Site']['Generator'][
                'existing_gen_total_fuel_cost_us_dollars'],
       })
    if nested_output['Scenario']['Site'].get('CHP') is not None:
        base.update({
            'chp_kw': nested_output['Scenario']['Site']['CHP']['size_kw'],
            'chp_year_one_fuel_used_mmbtu': nested_output['Scenario']['Site']['CHP']['year_one_fuel_used_mmbtu'],
            'chp_year_one_electric_energy_produced_kwh': nested_output['Scenario']['Site']['CHP'][
                'year_one_electric_energy_produced_kwh'],
            'chp_year_one_thermal_energy_produced_mmbtu': nested_output['Scenario']['Site']['CHP'][
                'year_one_thermal_energy_produced_mmbtu'],
        })
    if nested_output['Scenario']['Site'].get('Boiler') is not None:
        base.update({
            'boiler_yearly_fuel_consumption_mmbtu': nested_output['Scenario']['Site']['Boiler'][
                'year_one_boiler_fuel_consumption_mmbtu'],
            'boiler_yearly_thermal_production_mmbtu': nested_output['Scenario']['Site']['Boiler'][
                'year_one_boiler_thermal_production_mmbtu'],
        })
    if nested_output['Scenario']['Site'].get('ElectricChiller') is not None:
        base.update({
            'electric_chiller_yearly_electric_consumption_kwh': nested_output['Scenario']['Site']['ElectricChiller'][
                'year_one_electric_chiller_electric_consumption_kwh'],
            'electric_chiller_yearly_thermal_production_tonhr': nested_output['Scenario']['Site']['ElectricChiller'][
                'year_one_electric_chiller_thermal_production_tonhr'],
        })
    if nested_output['Scenario']['Site'].get('AbsorptionChiller') is not None:
        base.update({
            'absorpchl_ton': nested_output['Scenario']['Site']['AbsorptionChiller']['size_ton'],
            'absorp_chl_yearly_thermal_consumption_mmbtu': nested_output['Scenario']['Site']['AbsorptionChiller'][
                'year_one_absorp_chl_thermal_consumption_mmbtu'],
            'absorp_chl_yearly_thermal_production_tonhr': nested_output['Scenario']['Site']['AbsorptionChiller'][
                'year_one_absorp_chl_thermal_production_tonhr'],
        })
    if nested_output['Scenario']['Site'].get('ColdTES') is not None:
        base.update({
            'coldtes_gal': nested_output['Scenario']['Site']['ColdTES']['size_gal'],
            'coldtes_thermal_series_ton': nested_output['Scenario']['Site']['ColdTES'][
                'year_one_thermal_from_cold_tes_series_ton'],
        })
    if nested_output['Scenario']['Site'].get('HotTES') is not None:
        base.update({
            'hottes_gal': nested_output['Scenario']['Site']['HotTES']['size_gal'],
            'hottes_thermal_series_mmbtu_per_hr': nested_output['Scenario']['Site']['HotTES'][
                'year_one_thermal_from_hot_tes_series_mmbtu_per_hr'],
        })
    if nested_output['Scenario']['Site'].get('FuelTariff') is not None:
        base.update({
            'total_boiler_fuel_cost_bau': nested_output['Scenario']['Site']['FuelTariff'][
                'total_boiler_fuel_cost_bau_us_dollars'],
            'boiler_total_fuel_cost_us_dollars': nested_output['Scenario']['Site']['FuelTariff'][
                'total_boiler_fuel_cost_us_dollars'],
            'chp_total_fuel_cost_us_dollars': nested_output['Scenario']['Site']['FuelTariff'][
                'total_chp_fuel_cost_us_dollars'],
            'boiler_bau_total_fuel_cost_us_dollars': nested_output['Scenario']['Site']['FuelTariff'][
                'total_boiler_fuel_cost_bau_us_dollars'],
        })
    return base
