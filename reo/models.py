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
# from django.contrib.auth.models import User
from django.db import models
from django.contrib.postgres.fields import *
from django.forms.models import model_to_dict
from picklefield.fields import PickledObjectField
from reo.nested_inputs import nested_input_definitions
import logging
log = logging.getLogger(__name__)
import sys
import traceback as tb
import warnings


class URDBError(models.Model):
    label = models.TextField(null=True, blank=True, default='')
    type = models.TextField(null=True, blank=True, default='')
    message = models.TextField(null=True, blank=True, default='')

    def save_to_db(self):
        try:
            self.save()
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            message = 'Could not save URDBError {} for label {} error to the database - {} \n\n{}'.format(self.type,
                                                                                                          self.label,
                                                                                                          self.message,
                                                                                                          tb.format_tb(
                                                                                                              exc_traceback))
            warnings.warn(message)
            log.debug(message)


class ProfileModel(models.Model):
    run_uuid = models.UUIDField(unique=True)
    pre_setup_scenario_seconds = models.FloatField(null=True, blank=True)
    setup_scenario_seconds = models.FloatField(null=True, blank=True)
    reopt_seconds = models.FloatField(null=True, blank=True)
    reopt_bau_seconds = models.FloatField(null=True, blank=True)
    parse_run_outputs_seconds = models.FloatField(null=True, blank=True)

    julia_input_construction_seconds = models.FloatField(null=True, blank=True)
    julia_reopt_preamble_seconds = models.FloatField(null=True, blank=True)
    julia_reopt_variables_seconds = models.FloatField(null=True, blank=True)
    julia_reopt_constriants_seconds = models.FloatField(null=True, blank=True)
    julia_reopt_optimize_seconds = models.FloatField(null=True, blank=True)
    julia_reopt_postprocess_seconds = models.FloatField(null=True, blank=True)
    pyjulia_start_seconds = models.FloatField(null=True, blank=True)
    pyjulia_pkg_seconds = models.FloatField(null=True, blank=True)
    pyjulia_activate_seconds = models.FloatField(null=True, blank=True)
    pyjulia_include_model_seconds = models.FloatField(null=True, blank=True)
    pyjulia_make_model_seconds = models.FloatField(null=True, blank=True)
    pyjulia_include_reopt_seconds = models.FloatField(null=True, blank=True)
    pyjulia_run_reopt_seconds = models.FloatField(null=True, blank=True)

    julia_input_construction_seconds_bau = models.FloatField(null=True, blank=True)
    julia_reopt_preamble_seconds_bau = models.FloatField(null=True, blank=True)
    julia_reopt_variables_seconds_bau = models.FloatField(null=True, blank=True)
    julia_reopt_constriants_seconds_bau = models.FloatField(null=True, blank=True)
    julia_reopt_optimize_seconds_bau = models.FloatField(null=True, blank=True)
    julia_reopt_postprocess_seconds_bau = models.FloatField(null=True, blank=True)
    pyjulia_start_seconds_bau = models.FloatField(null=True, blank=True)
    pyjulia_pkg_seconds_bau = models.FloatField(null=True, blank=True)
    pyjulia_activate_seconds_bau = models.FloatField(null=True, blank=True)
    pyjulia_include_model_seconds_bau = models.FloatField(null=True, blank=True)
    pyjulia_make_model_seconds_bau = models.FloatField(null=True, blank=True)
    pyjulia_include_reopt_seconds_bau = models.FloatField(null=True, blank=True)
    pyjulia_run_reopt_seconds_bau = models.FloatField(null=True, blank=True)

    @classmethod
    def create(cls, **kwargs):
        obj = cls(**kwargs)
        obj.save()
        return obj


class ScenarioModel(models.Model):
    # Inputs
    # user = models.ForeignKey(User, null=True, blank=True)
    run_uuid = models.UUIDField(unique=True)
    api_version = models.TextField(null=True, blank=True)
    user_uuid = models.TextField(null=True, blank=True)
    webtool_uuid = models.TextField(null=True, blank=True)
    job_type = models.TextField(null=True, blank=True)

    description = models.TextField(null=True, blank=True)
    status = models.TextField(null=True, blank=True)
    timeout_seconds = models.IntegerField(null=True, blank=True)
    time_steps_per_hour = models.IntegerField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    optimality_tolerance_bau = models.FloatField(null=True, blank=True)
    optimality_tolerance_techs = models.FloatField(null=True, blank=True)
    add_soc_incentive = models.BooleanField(null=True, blank=True)

    lower_bound = models.FloatField(null=True, blank=True)
    optimality_gap = models.FloatField(null=True, blank=True)

    @classmethod
    def create(cls, **kwargs):
        obj = cls(**kwargs)
        obj.save()
        return obj


class SiteModel(models.Model):
    # Inputs
    run_uuid = models.UUIDField(unique=True)
    address = models.TextField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    land_acres = models.FloatField(null=True, blank=True)
    roof_squarefeet = models.FloatField(null=True, blank=True)
    year_one_emissions_lb_C02 = models.FloatField(null=True, blank=True)
    year_one_emissions_bau_lb_C02 = models.FloatField(null=True, blank=True)
    outdoor_air_temp_degF = ArrayField(models.FloatField(blank=True, null=True), default=list, null=True)
    elevation_ft = models.FloatField(null=True, blank=True)
    renewable_electricity_energy_pct = models.FloatField(null=True, blank=True)

    @classmethod
    def create(cls, **kwargs):
        obj = cls(**kwargs)
        obj.save()

        return obj


class FinancialModel(models.Model):
    # Input
    run_uuid = models.UUIDField(unique=True)
    analysis_years = models.IntegerField(null=True, blank=True)
    escalation_pct = models.FloatField(null=True, blank=True)
    boiler_fuel_escalation_pct = models.FloatField(null=True, blank=True)
    chp_fuel_escalation_pct = models.FloatField(null=True, blank=True)
    om_cost_escalation_pct = models.FloatField(null=True, blank=True)
    offtaker_discount_pct = models.FloatField(null=True, blank=True)
    offtaker_tax_pct = models.FloatField(null=True, blank=True)
    value_of_lost_load_us_dollars_per_kwh = models.FloatField(null=True, blank=True)
    microgrid_upgrade_cost_pct = models.FloatField(null=True, blank=True)
    third_party_ownership = models.BooleanField(null=True, blank=True)
    owner_discount_pct = models.FloatField(null=True, blank=True)
    owner_tax_pct = models.FloatField(null=True, blank=True)

    # Outputs
    lcc_us_dollars = models.FloatField(null=True, blank=True)
    lcc_bau_us_dollars = models.FloatField(null=True, blank=True)
    npv_us_dollars = models.FloatField(null=True, blank=True)
    net_capital_costs_plus_om_us_dollars = models.FloatField(null=True, blank=True)
    avoided_outage_costs_us_dollars = models.FloatField(null=True, blank=True)
    microgrid_upgrade_cost_us_dollars = models.FloatField(null=True, blank=True)
    net_capital_costs = models.FloatField(null=True, blank=True)
    net_om_us_dollars_bau = models.FloatField(null=True, blank=True)
    initial_capital_costs = models.FloatField(null=True, blank=True)
    replacement_costs = models.FloatField(null=True, blank=True)
    om_and_replacement_present_cost_after_tax_us_dollars = models.FloatField(null=True, blank=True)
    initial_capital_costs_after_incentives = models.FloatField(null=True, blank=True)
    total_om_costs_us_dollars = models.FloatField(null=True, blank=True)
    year_one_om_costs_us_dollars = models.FloatField(null=True, blank=True)
    year_one_om_costs_before_tax_us_dollars = models.FloatField(null=True, blank=True)
    simple_payback_years = models.FloatField(null=True, blank=True)
    irr_pct = models.FloatField(null=True, blank=True)
    net_present_cost_us_dollars = models.FloatField(null=True, blank=True)
    annualized_payment_to_third_party_us_dollars = models.FloatField(null=True, blank=True)
    offtaker_annual_free_cashflow_series_us_dollars = ArrayField(
            models.FloatField(null=True, blank=True), default=list, null=True)
    offtaker_discounted_annual_free_cashflow_series_us_dollars = ArrayField(
            models.FloatField(null=True, blank=True), default=list, null=True)
    offtaker_annual_free_cashflow_series_bau_us_dollars = ArrayField(
            models.FloatField(null=True, blank=True), default=list, null=True)
    offtaker_discounted_annual_free_cashflow_series_bau_us_dollars = ArrayField(
            models.FloatField(null=True, blank=True), default=list, null=True)
    developer_annual_free_cashflow_series_us_dollars = ArrayField(
            models.FloatField(null=True, blank=True), default=list, null=True)
    developer_om_and_replacement_present_cost_after_tax_us_dollars = models.FloatField(null=True, blank=True)

    @classmethod
    def create(cls, **kwargs):
        obj = cls(**kwargs)
        obj.save()

        return obj


class LoadProfileModel(models.Model):
    # Inputs
    run_uuid = models.UUIDField(unique=True)
    doe_reference_name = ArrayField(
            models.TextField(null=True, blank=True), default=list, null=True)
    annual_kwh = models.FloatField(null=True, blank=True)
    percent_share = ArrayField(models.FloatField(null=True, blank=True), default=list, null=True)
    year = models.IntegerField(null=True, blank=True)
    monthly_totals_kwh = ArrayField(models.FloatField(blank=True), default=list, null=True)
    loads_kw = ArrayField(models.FloatField(blank=True), default=list, null=True)
    critical_loads_kw = ArrayField(models.FloatField(blank=True), default=list, null=True)
    loads_kw_is_net = models.BooleanField(null=True, blank=True)
    critical_loads_kw_is_net = models.BooleanField(null=True, blank=True)
    outage_start_time_step = models.IntegerField(null=True, blank=True)
    outage_end_time_step = models.IntegerField(null=True, blank=True)
    critical_load_pct = models.FloatField(null=True, blank=True)
    outage_is_major_event = models.BooleanField(null=True, blank=True)

    #Outputs
    year_one_electric_load_series_kw = ArrayField(models.FloatField(null=True, blank=True), default=list, null=True)
    critical_load_series_kw = ArrayField(models.FloatField(null=True, blank=True), default=list, null=True)
    annual_calculated_kwh = models.FloatField(null=True, blank=True)
    sustain_hours = models.IntegerField(null=True, blank=True)
    bau_sustained_time_steps = models.IntegerField(null=True, blank=True)
    resilience_check_flag = models.BooleanField(null=True, blank=True)

    @classmethod
    def create(cls, **kwargs):
        obj = cls(**kwargs)
        obj.save()

        return obj


class LoadProfileBoilerFuelModel(models.Model):
    # Inputs
    run_uuid = models.UUIDField(unique=True)
    annual_mmbtu = models.FloatField(null=True, blank=True)
    monthly_mmbtu = ArrayField(models.FloatField(blank=True),default=list, null=True)
    loads_mmbtu_per_hour = ArrayField(models.FloatField(blank=True), default=list, null=True)
    doe_reference_name = ArrayField(
            models.TextField(null=True, blank=True), default=list, null=True)
    percent_share = ArrayField(models.FloatField(null=True, blank=True), default=list, null=True)

    # Outputs
    annual_calculated_boiler_fuel_load_mmbtu_bau = models.FloatField(null=True, blank=True)
    year_one_boiler_fuel_load_series_mmbtu_per_hr = ArrayField(models.FloatField(null=True, blank=True), default=list, null=True)
    year_one_boiler_thermal_load_series_mmbtu_per_hr = ArrayField(models.FloatField(null=True, blank=True), default=list, null=True)

    @classmethod
    def create(cls, **kwargs):
        obj = cls(**kwargs)
        obj.save()

        return obj


class LoadProfileChillerThermalModel(models.Model):
    # Inputs
    run_uuid = models.UUIDField(unique=True)
    loads_ton = ArrayField(models.FloatField(null=True, blank=True), default=list, null=True)
    annual_tonhour = models.FloatField(null=True, blank=True)
    monthly_tonhour = ArrayField(models.FloatField(blank=True), default=list, null=True)
    annual_fraction = models.FloatField(null=True, blank=True)
    monthly_fraction = ArrayField(models.FloatField(blank=True), default=list, null=True)
    loads_fraction = ArrayField(models.FloatField(blank=True), default=list, null=True)
    doe_reference_name = ArrayField(
            models.TextField(null=True, blank=True), default=list, null=True)
    percent_share = ArrayField(models.FloatField(null=True, blank=True), default=list, null=True)
    chiller_cop = models.FloatField(null=True, blank=True)

    # Outputs
    annual_calculated_kwh_bau = models.FloatField(blank=True, null=True)
    year_one_chiller_electric_load_series_kw_bau = ArrayField(models.FloatField(null=True, blank=True), default=list, null=True)
    year_one_chiller_electric_load_series_kw = ArrayField(models.FloatField(null=True, blank=True), default=list, null=True)
    year_one_chiller_thermal_load_series_ton = ArrayField(models.FloatField(null=True, blank=True), default=list, null=True)

    @classmethod
    def create(cls, **kwargs):
        obj = cls(**kwargs)
        obj.save()

        return obj

class ElectricTariffModel(models.Model):

    #Inputs
    run_uuid = models.UUIDField(unique=True)
    urdb_utility_name = models.TextField(null=True, blank=True)
    urdb_rate_name = models.TextField(null=True, blank=True)
    urdb_label = models.TextField(null=True, blank=True)
    blended_monthly_rates_us_dollars_per_kwh = ArrayField(models.FloatField(blank=True), default=list, null=True)
    blended_monthly_demand_charges_us_dollars_per_kw = ArrayField(models.FloatField(null=True, blank=True), default=list, null=True)
    blended_annual_rates_us_dollars_per_kwh = models.FloatField(blank=True, default=0, null=True)
    blended_annual_demand_charges_us_dollars_per_kw = models.FloatField(blank=True, default=0, null=True)
    net_metering_limit_kw = models.FloatField(null=True, blank=True)
    interconnection_limit_kw = models.FloatField(null=True, blank=True)
    wholesale_rate_us_dollars_per_kwh = ArrayField(models.FloatField(null=True, blank=True))
    wholesale_rate_above_site_load_us_dollars_per_kwh = ArrayField(
            models.FloatField(null=True, blank=True, default=list))
    urdb_response = PickledObjectField(null=True, editable=True)
    add_blended_rates_to_urdb_rate = models.BooleanField(null=True, blank=True)
    add_tou_energy_rates_to_urdb_rate = models.BooleanField(null=True, blank=True)
    tou_energy_rates_us_dollars_per_kwh = ArrayField(models.FloatField(null=True, blank=True), null=True, default=list)
    emissions_factor_series_lb_CO2_per_kwh = ArrayField(models.FloatField(null=True, blank=True), null=True, default=list)
    chp_standby_rate_us_dollars_per_kw_per_month = models.FloatField(blank=True, null=True)
    chp_does_not_reduce_demand_charges = models.BooleanField(null=True, blank=True)
    emissions_region = models.TextField(null=True, blank=True)
    coincident_peak_load_active_timesteps = ArrayField(ArrayField(models.FloatField(null=True, blank=True), null=True, default=list), null=True, default=list)
    coincident_peak_load_charge_us_dollars_per_kw = ArrayField(models.FloatField(null=True, blank=True), null=True, default=list)

    # Ouptuts
    year_one_energy_cost_us_dollars = models.FloatField(null=True, blank=True)
    year_one_demand_cost_us_dollars = models.FloatField(null=True, blank=True)
    year_one_fixed_cost_us_dollars = models.FloatField(null=True, blank=True)
    year_one_min_charge_adder_us_dollars = models.FloatField(null=True, blank=True)
    year_one_energy_cost_bau_us_dollars = models.FloatField(null=True, blank=True)
    year_one_demand_cost_bau_us_dollars = models.FloatField(null=True, blank=True)
    year_one_fixed_cost_bau_us_dollars = models.FloatField(null=True, blank=True)
    year_one_min_charge_adder_bau_us_dollars = models.FloatField(null=True, blank=True)
    total_energy_cost_us_dollars = models.FloatField(null=True, blank=True)
    total_demand_cost_us_dollars = models.FloatField(null=True, blank=True)
    total_fixed_cost_us_dollars = models.FloatField(null=True, blank=True)
    total_min_charge_adder_us_dollars = models.FloatField(null=True, blank=True)
    total_energy_cost_bau_us_dollars = models.FloatField(null=True, blank=True)
    total_demand_cost_bau_us_dollars = models.FloatField(null=True, blank=True)
    total_fixed_cost_bau_us_dollars = models.FloatField(null=True, blank=True)
    total_export_benefit_us_dollars = models.FloatField(null=True, blank=True)
    total_export_benefit_bau_us_dollars = models.FloatField(null=True, blank=True)
    total_min_charge_adder_bau_us_dollars = models.FloatField(null=True, blank=True)
    year_one_bill_us_dollars = models.FloatField(null=True, blank=True)
    year_one_bill_bau_us_dollars = models.FloatField(null=True, blank=True)
    year_one_export_benefit_us_dollars = models.FloatField(null=True, blank=True)
    year_one_export_benefit_bau_us_dollars = models.FloatField(null=True, blank=True)
    year_one_energy_cost_series_us_dollars_per_kwh = ArrayField(models.FloatField(null=True, blank=True), default=list, null=True, blank=True)
    year_one_demand_cost_series_us_dollars_per_kw = ArrayField(models.FloatField(null=True, blank=True), default=list, null=True, blank=True)
    year_one_to_load_series_kw = ArrayField(models.FloatField(null=True, blank=True), default=list, null=True, blank=True)
    year_one_to_load_series_bau_kw = ArrayField(models.FloatField(null=True, blank=True), default=list, null=True, blank=True)
    year_one_to_battery_series_kw = ArrayField(models.FloatField(null=True, blank=True), default=list, null=True, blank=True)
    year_one_energy_supplied_kwh = models.FloatField(null=True, blank=True)
    year_one_energy_supplied_kwh_bau = models.FloatField(null=True, blank=True)
    year_one_emissions_lb_C02 = models.FloatField(null=True, blank=True)
    year_one_emissions_bau_lb_C02 = models.FloatField(null=True, blank=True)
    year_one_coincident_peak_cost_us_dollars = models.FloatField(null=True, blank=True)
    year_one_coincident_peak_cost_bau_us_dollars = models.FloatField(null=True, blank=True)
    total_coincident_peak_cost_us_dollars = models.FloatField(null=True, blank=True)
    total_coincident_peak_cost_bau_us_dollars = models.FloatField(null=True, blank=True)
    year_one_chp_standby_cost_us_dollars = models.FloatField(null=True, blank=True)
    total_chp_standby_cost_us_dollars = models.FloatField(null=True, blank=True)

    @classmethod
    def create(cls, **kwargs):
        obj = cls(**kwargs)
        obj.save()

        return obj


class FuelTariffModel(models.Model):
    # Inputs
    run_uuid = models.UUIDField(unique=True)
    existing_boiler_fuel_type = models.TextField(null=True, blank=True)
    boiler_fuel_blended_annual_rates_us_dollars_per_mmbtu = models.FloatField(null=True, blank=True)
    boiler_fuel_blended_monthly_rates_us_dollars_per_mmbtu = ArrayField(models.FloatField(null=True, blank=True), default=list, null=True)
    chp_fuel_type = models.TextField(null=True, blank=True)
    chp_fuel_blended_annual_rates_us_dollars_per_mmbtu = models.FloatField(null=True, blank=True)
    chp_fuel_blended_monthly_rates_us_dollars_per_mmbtu = ArrayField(models.FloatField(null=True, blank=True), default=list, null=True)

    # Outputs
    total_boiler_fuel_cost_us_dollars = models.FloatField(null=True, blank=True)
    year_one_boiler_fuel_cost_us_dollars = models.FloatField(null=True, blank=True)
    year_one_boiler_fuel_cost_bau_us_dollars = models.FloatField(null=True, blank=True)
    total_chp_fuel_cost_us_dollars = models.FloatField(null=True, blank=True)
    year_one_chp_fuel_cost_us_dollars = models.FloatField(null=True, blank=True)
    total_boiler_fuel_cost_bau_us_dollars = models.FloatField(null=True, blank=True)

    @classmethod
    def create(cls, **kwargs):
        obj = cls(**kwargs)
        obj.save()

        return obj


class PVModel(models.Model):

    #Inputs
    run_uuid = models.UUIDField(unique=False)
    existing_kw = models.FloatField(null=True, blank=True)
    min_kw = models.FloatField(null=True, blank=True)
    max_kw = models.FloatField(null=True, blank=True)
    installed_cost_us_dollars_per_kw = models.FloatField(null=True, blank=True)
    om_cost_us_dollars_per_kw = models.FloatField(null=True, blank=True)
    macrs_option_years = models.IntegerField(null=True, blank=True)
    macrs_bonus_pct = models.FloatField(null=True, blank=True)
    macrs_itc_reduction = models.FloatField(null=True, blank=True)
    federal_itc_pct = models.FloatField(null=True, blank=True)
    state_ibi_pct = models.FloatField(null=True, blank=True)
    state_ibi_max_us_dollars = models.FloatField(null=True, blank=True)
    utility_ibi_pct = models.FloatField(null=True, blank=True)
    utility_ibi_max_us_dollars = models.FloatField(null=True, blank=True)
    federal_rebate_us_dollars_per_kw = models.FloatField(null=True, blank=True)
    state_rebate_us_dollars_per_kw = models.FloatField(null=True, blank=True)
    state_rebate_max_us_dollars = models.FloatField(null=True, blank=True)
    utility_rebate_us_dollars_per_kw = models.FloatField(null=True, blank=True)
    utility_rebate_max_us_dollars = models.FloatField(null=True, blank=True)
    pbi_us_dollars_per_kwh = models.FloatField(null=True, blank=True)
    pbi_max_us_dollars = models.FloatField(null=True, blank=True)
    pbi_years = models.FloatField(null=True, blank=True)
    pbi_system_max_kw = models.FloatField(null=True, blank=True)
    degradation_pct = models.FloatField(null=True, blank=True)
    azimuth = models.FloatField(null=True, blank=True)
    losses = models.FloatField(null=True, blank=True)
    array_type = models.IntegerField(null=True, blank=True)
    module_type = models.IntegerField(null=True, blank=True)
    gcr = models.FloatField(null=True, blank=True)
    dc_ac_ratio = models.FloatField(null=True, blank=True)
    inv_eff = models.FloatField(null=True, blank=True)
    radius = models.FloatField(null=True, blank=True)
    tilt = models.FloatField(null=True, blank=True)
    prod_factor_series_kw = ArrayField(
            models.FloatField(null=True, blank=True), default=list, null=True)
    pv_number = models.IntegerField(null=True, blank=True)
    pv_name = models.TextField(null=True, blank=True)
    location = models.TextField(null=True, blank=True)
    can_net_meter = models.BooleanField(null=True, blank=True)
    can_wholesale = models.BooleanField(null=True, blank=True)
    can_export_beyond_site_load = models.BooleanField(null=True, blank=True)
    can_curtail = models.BooleanField(null=True, blank=True)

    # Outputs
    size_kw = models.FloatField(null=True, blank=True)
    station_latitude = models.FloatField(null=True, blank=True)
    station_longitude = models.FloatField(null=True, blank=True)
    station_distance_km = models.FloatField(null=True, blank=True)
    average_yearly_energy_produced_kwh = models.FloatField(null=True, blank=True)
    average_yearly_energy_produced_bau_kwh = models.FloatField(null=True, blank=True)
    average_yearly_energy_exported_kwh = models.FloatField(null=True, blank=True)
    year_one_energy_produced_kwh = models.FloatField(null=True, blank=True)
    year_one_energy_produced_bau_kwh = models.FloatField(null=True, blank=True)
    year_one_power_production_series_kw = ArrayField(
            models.FloatField(null=True, blank=True), null=True, blank=True, default=list)
    year_one_to_battery_series_kw = ArrayField(
            models.FloatField(null=True, blank=True), null=True, blank=True, default=list)
    year_one_to_load_series_kw = ArrayField(
            models.FloatField(null=True, blank=True), null=True, blank=True, default=list)
    year_one_to_grid_series_kw = ArrayField(
            models.FloatField(null=True, blank=True), null=True, blank=True, default=list)
    existing_pv_om_cost_us_dollars = models.FloatField(null=True, blank=True)
    year_one_curtailed_production_series_kw = ArrayField(
            models.FloatField(null=True, blank=True), null=True, blank=True, default=list)
    existing_pv_om_cost_us_dollars = models.FloatField(null=True, blank=True)
    lcoe_us_dollars_per_kwh = models.FloatField(null=True, blank=True)

    @classmethod
    def create(cls, **kwargs):
        obj = cls(**kwargs)
        obj.save()

        return obj


class WindModel(models.Model):
    # Inputs
    run_uuid = models.UUIDField(unique=True)
    size_class = models.TextField(null=True, blank=True)
    wind_meters_per_sec = ArrayField(
            models.FloatField(null=True, blank=True), null=True, blank=True, default=list)
    wind_direction_degrees = ArrayField(
            models.FloatField(null=True, blank=True), null=True, blank=True, default=list)
    temperature_celsius = ArrayField(
            models.FloatField(null=True, blank=True), null=True, blank=True, default=list)
    pressure_atmospheres = ArrayField(
            models.FloatField(null=True, blank=True), null=True, blank=True, default=list)
    min_kw = models.FloatField(null=True, blank=True)
    max_kw = models.FloatField(null=True, blank=True)
    installed_cost_us_dollars_per_kw = models.FloatField(null=True, blank=True)
    om_cost_us_dollars_per_kw = models.FloatField(null=True, blank=True)
    macrs_option_years = models.IntegerField(null=True, blank=True)
    macrs_bonus_pct = models.FloatField(null=True, blank=True)
    macrs_itc_reduction = models.FloatField(null=True, blank=True)
    federal_itc_pct = models.FloatField(null=True, blank=True)
    state_ibi_pct = models.FloatField(null=True, blank=True)
    state_ibi_max_us_dollars = models.FloatField(null=True, blank=True)
    utility_ibi_pct = models.FloatField(null=True, blank=True)
    utility_ibi_max_us_dollars = models.FloatField(null=True, blank=True)
    federal_rebate_us_dollars_per_kw = models.FloatField(null=True, blank=True)
    state_rebate_us_dollars_per_kw = models.FloatField(null=True, blank=True)
    state_rebate_max_us_dollars = models.FloatField(null=True, blank=True)
    utility_rebate_us_dollars_per_kw = models.FloatField(null=True, blank=True)
    utility_rebate_max_us_dollars = models.FloatField(null=True, blank=True)
    pbi_us_dollars_per_kwh = models.FloatField(null=True, blank=True)
    pbi_max_us_dollars = models.FloatField(null=True, blank=True)
    pbi_years = models.FloatField(null=True, blank=True)
    pbi_system_max_kw = models.FloatField(null=True, blank=True)
    prod_factor_series_kw = ArrayField(
            models.FloatField(blank=True), default=list, null=True)
    can_net_meter = models.BooleanField(null=True, blank=True)
    can_wholesale = models.BooleanField(null=True, blank=True)
    can_export_beyond_site_load = models.BooleanField(null=True, blank=True)
    can_curtail = models.BooleanField(null=True, blank=True)

    # Outputs
    size_kw = models.FloatField(null=True, blank=True)
    average_yearly_energy_produced_kwh = models.FloatField(null=True, blank=True)
    average_yearly_energy_exported_kwh = models.FloatField(null=True, blank=True)
    year_one_energy_produced_kwh = models.FloatField(null=True, blank=True)
    year_one_power_production_series_kw = ArrayField(
            models.FloatField(null=True, blank=True), null=True, blank=True, default=list)
    year_one_to_battery_series_kw = ArrayField(
            models.FloatField(null=True, blank=True), null=True, blank=True, default=list)
    year_one_to_load_series_kw = ArrayField(
            models.FloatField(null=True, blank=True), null=True, blank=True, default=list)
    year_one_to_grid_series_kw = ArrayField(
            models.FloatField(null=True, blank=True), null=True, blank=True, default=list)
    lcoe_us_dollars_per_kwh = models.FloatField(null=True, blank=True)
    year_one_curtailed_production_series_kw = ArrayField(
            models.FloatField(null=True, blank=True), null=True, blank=True, default=list)

    @classmethod
    def create(cls, **kwargs):
        obj = cls(**kwargs)
        obj.save()

        return obj


class StorageModel(models.Model):
    # Inputs
    run_uuid = models.UUIDField(unique=True)
    min_kw = models.FloatField(null=True, blank=True)
    max_kw = models.FloatField(null=True, blank=True)
    min_kwh = models.FloatField(null=True, blank=True)
    max_kwh = models.FloatField(null=True, blank=True)
    internal_efficiency_pct = models.FloatField(null=True, blank=True)
    inverter_efficiency_pct = models.FloatField(null=True, blank=True)
    rectifier_efficiency_pct = models.FloatField(null=True, blank=True)
    soc_min_pct = models.FloatField(null=True, blank=True)
    soc_init_pct = models.FloatField(null=True, blank=True)
    canGridCharge = models.BooleanField(null=True, blank=True)
    installed_cost_us_dollars_per_kw = models.FloatField(null=True, blank=True)
    installed_cost_us_dollars_per_kwh = models.FloatField(null=True, blank=True)
    replace_cost_us_dollars_per_kw = models.FloatField(null=True, blank=True)
    replace_cost_us_dollars_per_kwh = models.FloatField(null=True, blank=True)
    inverter_replacement_year = models.IntegerField(null=True, blank=True)
    battery_replacement_year = models.IntegerField(null=True, blank=True)
    macrs_option_years = models.IntegerField(null=True, blank=True)
    macrs_bonus_pct = models.FloatField(null=True, blank=True)
    macrs_itc_reduction = models.FloatField(null=True, blank=True)
    total_itc_pct = models.FloatField(null=True, blank=True)
    total_rebate_us_dollars_per_kw = models.IntegerField(null=True, blank=True)
    total_rebate_us_dollars_per_kwh = models.IntegerField(null=True, blank=True)

    # Outputs
    size_kw = models.FloatField(null=True, blank=True)
    size_kwh = models.FloatField(null=True, blank=True)
    year_one_to_load_series_kw = ArrayField(
            models.FloatField(null=True, blank=True), null=True, blank=True, default=list)
    year_one_to_grid_series_kw = ArrayField(
            models.FloatField(null=True, blank=True), null=True, blank=True, default=list)
    year_one_soc_series_pct = ArrayField(
            models.FloatField(null=True, blank=True), null=True, blank=True, default=list)

    @classmethod
    def create(cls, **kwargs):
        obj = cls(**kwargs)
        obj.save()

        return obj


class GeneratorModel(models.Model):
    # Inputs
    run_uuid = models.UUIDField(unique=True)
    existing_kw = models.FloatField(null=True, blank=True)
    min_kw = models.FloatField(null=True, blank=True)
    max_kw = models.FloatField(null=True, blank=True)
    installed_cost_us_dollars_per_kw = models.FloatField(null=True, blank=True,)
    om_cost_us_dollars_per_kw = models.FloatField(null=True, blank=True)
    om_cost_us_dollars_per_kwh = models.FloatField(null=True, blank=True)
    diesel_fuel_cost_us_dollars_per_gallon = models.FloatField(null=True, blank=True)
    fuel_slope_gal_per_kwh = models.FloatField(null=True, blank=True)
    fuel_intercept_gal_per_hr = models.FloatField(null=True, blank=True)
    fuel_avail_gal = models.FloatField(null=True, blank=True)
    min_turn_down_pct = models.FloatField(null=True, blank=True)
    generator_only_runs_during_grid_outage = models.BooleanField(null=True, blank=True)
    generator_sells_energy_back_to_grid = models.BooleanField(null=True, blank=True)
    macrs_option_years = models.IntegerField(null=True, blank=True)
    macrs_bonus_pct = models.FloatField(null=True, blank=True)
    macrs_itc_reduction = models.FloatField(null=True, blank=True)
    federal_itc_pct = models.FloatField(null=True, blank=True)
    state_ibi_pct = models.FloatField(null=True, blank=True)
    state_ibi_max_us_dollars = models.FloatField(null=True, blank=True)
    utility_ibi_pct = models.FloatField(null=True, blank=True)
    utility_ibi_max_us_dollars = models.FloatField(null=True, blank=True)
    federal_rebate_us_dollars_per_kw = models.FloatField(null=True, blank=True)
    state_rebate_us_dollars_per_kw = models.FloatField(null=True, blank=True)
    state_rebate_max_us_dollars = models.FloatField(null=True, blank=True)
    utility_rebate_us_dollars_per_kw = models.FloatField(null=True, blank=True)
    utility_rebate_max_us_dollars = models.FloatField(null=True, blank=True)
    pbi_us_dollars_per_kwh = models.FloatField(null=True, blank=True)
    pbi_max_us_dollars = models.FloatField(null=True, blank=True)
    pbi_years = models.FloatField(null=True, blank=True)
    pbi_system_max_kw = models.FloatField(null=True, blank=True)
    emissions_factor_lb_CO2_per_gal = models.FloatField(null=True, blank=True)
    can_net_meter = models.BooleanField(null=True, blank=True)
    can_wholesale = models.BooleanField(null=True, blank=True)
    can_export_beyond_site_load = models.BooleanField(null=True, blank=True)
    can_curtail = models.BooleanField(null=True, blank=True)

    # Outputs
    fuel_used_gal = models.FloatField(null=True, blank=True)
    fuel_used_gal_bau = models.FloatField(null=True, blank=True)
    size_kw = models.FloatField(null=True, blank=True)
    average_yearly_energy_produced_kwh = models.FloatField(null=True, blank=True)
    average_yearly_energy_exported_kwh = models.FloatField(null=True, blank=True)
    year_one_energy_produced_kwh = models.FloatField(null=True, blank=True)
    year_one_power_production_series_kw = ArrayField(
            models.FloatField(null=True, blank=True), null=True, blank=True, default=list)
    year_one_to_battery_series_kw = ArrayField(
            models.FloatField(null=True, blank=True), null=True, blank=True)
    year_one_to_load_series_kw = ArrayField(
            models.FloatField(null=True, blank=True), null=True, blank=True, default=list)
    year_one_to_grid_series_kw = ArrayField(
            models.FloatField(null=True, blank=True), null=True, blank=True, default=list)
    year_one_variable_om_cost_us_dollars = models.FloatField(null=True, blank=True)
    year_one_fuel_cost_us_dollars = models.FloatField(null=True, blank=True)
    year_one_fixed_om_cost_us_dollars = models.FloatField(null=True, blank=True)
    total_variable_om_cost_us_dollars = models.FloatField(null=True, blank=True)
    total_fuel_cost_us_dollars = models.FloatField(null=True, blank=True)
    total_fixed_om_cost_us_dollars = models.FloatField(null=True, blank=True)
    existing_gen_year_one_variable_om_cost_us_dollars = models.FloatField(null=True, blank=True)
    existing_gen_year_one_fuel_cost_us_dollars = models.FloatField(null=True, blank=True)
    existing_gen_total_variable_om_cost_us_dollars = models.FloatField(null=True, blank=True)
    existing_gen_total_fuel_cost_us_dollars = models.FloatField(null=True, blank=True)
    existing_gen_total_fixed_om_cost_us_dollars = models.FloatField(null=True, blank=True)
    year_one_emissions_lb_C02 = models.FloatField(null=True, blank=True)
    year_one_emissions_bau_lb_C02 = models.FloatField(null=True, blank=True)

    @classmethod
    def create(cls, **kwargs):
        obj = cls(**kwargs)
        obj.save()
        return obj


class CHPModel(models.Model):
    # Inputs
    run_uuid = models.UUIDField(unique=True)
    prime_mover = models.TextField(null=True, blank=True)
    size_class = models.IntegerField(null=True, blank=True)
    min_kw = models.FloatField(null=True, blank=True)
    max_kw = models.FloatField(null=True, blank=True)
    min_allowable_kw = models.FloatField(null=True, blank=True)
    installed_cost_us_dollars_per_kw = ArrayField(
            models.FloatField(null=True, blank=True), default=list, null=True)
    tech_size_for_cost_curve = ArrayField(
            models.FloatField(null=True, blank=True), default=list, null=True)
    om_cost_us_dollars_per_kw = models.FloatField(null=True, blank=True)
    om_cost_us_dollars_per_kwh = models.FloatField(null=True, blank=True)
    om_cost_us_dollars_per_hr_per_kw_rated = models.FloatField(null=True, blank=True)
    elec_effic_full_load = models.FloatField(null=True, blank=True)
    elec_effic_half_load = models.FloatField(null=True, blank=True)
    min_turn_down_pct = models.FloatField(null=True, blank=True)
    thermal_effic_full_load = models.FloatField(null=True, blank=True)
    thermal_effic_half_load = models.FloatField(null=True, blank=True)
    macrs_option_years = models.IntegerField(null=True, blank=True)
    macrs_bonus_pct = models.FloatField(null=True, blank=True)
    macrs_itc_reduction = models.FloatField(null=True, blank=True)
    federal_itc_pct = models.FloatField(null=True, blank=True)
    state_ibi_pct = models.FloatField(null=True, blank=True)
    state_ibi_max_us_dollars = models.FloatField(null=True, blank=True)
    utility_ibi_pct = models.FloatField(null=True, blank=True)
    utility_ibi_max_us_dollars = models.FloatField(null=True, blank=True)
    federal_rebate_us_dollars_per_kw = models.FloatField(null=True, blank=True)
    state_rebate_us_dollars_per_kw = models.FloatField(null=True, blank=True)
    state_rebate_max_us_dollars = models.FloatField(null=True, blank=True)
    utility_rebate_us_dollars_per_kw = models.FloatField(null=True, blank=True)
    utility_rebate_max_us_dollars = models.FloatField(null=True, blank=True)
    pbi_us_dollars_per_kwh = models.FloatField(null=True, blank=True)
    pbi_max_us_dollars = models.FloatField(null=True, blank=True)
    pbi_years = models.FloatField(null=True, blank=True)
    pbi_system_max_kw = models.FloatField(null=True, blank=True)
    emissions_factor_lb_CO2_per_mmbtu = models.FloatField(null=True, blank=True)
    use_default_derate = models.BooleanField(null=True, blank=True)
    max_derate_factor = models.FloatField(null=True, blank=True)
    derate_start_temp_degF = models.FloatField(null=True, blank=True)
    derate_slope_pct_per_degF = models.FloatField(null=True, blank=True)
    chp_unavailability_periods = ArrayField(
            PickledObjectField(null=True, editable=True), null=True)
    can_net_meter = models.BooleanField(null=True, blank=True)
    can_wholesale = models.BooleanField(null=True, blank=True)
    can_export_beyond_site_load = models.BooleanField(null=True, blank=True)
    can_curtail = models.BooleanField(null=True, blank=True)
    cooling_thermal_factor = models.FloatField(null=True, blank=True)

    # Outputs
    size_kw = models.FloatField(null=True, blank=True)
    year_one_fuel_used_mmbtu = models.FloatField(null=True, blank=True)
    year_one_electric_energy_produced_kwh = models.FloatField(null=True, blank=True)
    year_one_thermal_energy_produced_mmbtu = models.FloatField(null=True, blank=True)

    year_one_electric_production_series_kw = ArrayField(
            models.FloatField(null=True, blank=True), default=list, null=True, blank=True)
    year_one_to_battery_series_kw = ArrayField(
            models.FloatField(null=True, blank=True), default=list, null=True, blank=True)
    year_one_to_load_series_kw = ArrayField(
            models.FloatField(null=True, blank=True), default=list, null=True, blank=True)
    year_one_to_grid_series_kw = ArrayField(
            models.FloatField(null=True, blank=True), default=list, null=True, blank=True)
    year_one_thermal_to_load_series_mmbtu_per_hour = ArrayField(
            models.FloatField(null=True, blank=True), default=list, null=True, blank=True)
    year_one_thermal_to_tes_series_mmbtu_per_hour = ArrayField(
        models.FloatField(null=True, blank=True), default=list, null=True, blank=True)
    year_one_thermal_to_waste_series_mmbtu_per_hour = ArrayField(
            models.FloatField(null=True, blank=True), default=list, null=True, blank=True)
    year_one_emissions_lb_C02 = models.FloatField(null=True, blank=True)
    year_one_emissions_bau_lb_C02 = models.FloatField(null=True, blank=True)

    @classmethod
    def create(cls, **kwargs):
        obj = cls(**kwargs)
        obj.save()

        return obj


class AbsorptionChillerModel(models.Model):
    # Inputs
    run_uuid = models.UUIDField(unique=True)
    min_ton = models.FloatField(null=True, blank=True)
    max_ton = models.FloatField(null=True, blank=True)
    chiller_cop = models.FloatField(null=True, blank=True)
    chiller_elec_cop = models.FloatField(null=True, blank=True)
    installed_cost_us_dollars_per_ton = models.FloatField(null=True, blank=True)
    om_cost_us_dollars_per_ton = models.FloatField(null=True, blank=True)
    macrs_option_years = models.IntegerField(null=True, blank=True)
    macrs_bonus_pct = models.FloatField(null=True, blank=True)

    # Outputs
    size_ton = models.FloatField(null=True, blank=True)
    year_one_absorp_chl_thermal_to_load_series_ton = ArrayField(
            models.FloatField(null=True, blank=True), default=list, null=True, blank=True)
    year_one_absorp_chl_thermal_to_tes_series_ton = ArrayField(
            models.FloatField(null=True, blank=True), default=list, null=True, blank=True)
    year_one_absorp_chl_thermal_consumption_series_mmbtu_per_hr = ArrayField(
            models.FloatField(null=True, default=list, blank=True), null=True, blank=True)
    year_one_absorp_chl_thermal_consumption_mmbtu = models.FloatField(null=True, blank=True)
    year_one_absorp_chl_thermal_production_tonhr = models.FloatField(null=True, blank=True)
    year_one_absorp_chl_electric_consumption_series_kw = ArrayField(
            models.FloatField(null=True, blank=True), default=list, null=True, blank=True)
    year_one_absorp_chl_electric_consumption_kwh = models.FloatField(null=True, blank=True)

    @classmethod
    def create(cls, **kwargs):
        obj = cls(**kwargs)
        obj.save()

        return obj


class BoilerModel(models.Model):
    # Inputs
    run_uuid = models.UUIDField(unique=True)
    max_thermal_factor_on_peak_load = models.FloatField(null=True, blank=True)
    existing_boiler_production_type_steam_or_hw = models.TextField(null=True, blank=True)
    boiler_efficiency = models.FloatField(blank=True, default=0, null=True)
    emissions_factor_lb_CO2_per_mmbtu = models.FloatField(null=True, blank=True)

    # Outputs
    year_one_boiler_fuel_consumption_series_mmbtu_per_hr = ArrayField(
            models.FloatField(null=True, blank=True), default=list, null=True, blank=True)
    year_one_boiler_thermal_production_series_mmbtu_per_hr = ArrayField(
            models.FloatField(null=True, blank=True), default=list, null=True, blank=True)
    year_one_thermal_to_load_series_mmbtu_per_hour = ArrayField(
            models.FloatField(null=True, blank=True), default=list, null=True, blank=True)
    year_one_thermal_to_tes_series_mmbtu_per_hour = ArrayField(
            models.FloatField(null=True, blank=True), default=list, null=True, blank=True)
    year_one_boiler_fuel_consumption_mmbtu = models.FloatField(null=True, blank=True)
    year_one_boiler_thermal_production_mmbtu = models.FloatField(null=True, blank=True)
    year_one_emissions_lb_C02 = models.FloatField(null=True, blank=True)
    year_one_emissions_bau_lb_C02 = models.FloatField(null=True, blank=True)

    @classmethod
    def create(cls, **kwargs):
        obj = cls(**kwargs)
        obj.save()

        return obj


class ElectricChillerModel(models.Model):
    # Inputs
    run_uuid = models.UUIDField(unique=True)
    max_thermal_factor_on_peak_load = models.FloatField(null=True, blank=True)

    # Outputs
    year_one_electric_chiller_thermal_to_load_series_ton = ArrayField(
            models.FloatField(null=True, blank=True), default=list, null=True, blank=True)
    year_one_electric_chiller_thermal_to_tes_series_ton = ArrayField(
            models.FloatField(null=True, blank=True), default=list, null=True, blank=True)
    year_one_electric_chiller_electric_consumption_series_kw = ArrayField(
            models.FloatField(null=True, blank=True), default=list, null=True, blank=True)
    year_one_electric_chiller_electric_consumption_kwh = models.FloatField(null=True, blank=True)
    year_one_electric_chiller_thermal_production_tonhr = models.FloatField(null=True, blank=True)

    @classmethod
    def create(cls, **kwargs):
        obj = cls(**kwargs)
        obj.save()

        return obj


class ColdTESModel(models.Model):
    # Inputs
    run_uuid = models.UUIDField(unique=True)
    min_gal = models.FloatField(null=True, blank=True)
    max_gal = models.FloatField(null=True, blank=True)
    internal_efficiency_pct = models.FloatField(null=True, blank=True)
    soc_min_pct = models.FloatField(null=True, blank=True)
    soc_init_pct = models.FloatField(null=True, blank=True)
    installed_cost_us_dollars_per_gal = models.FloatField(null=True, blank=True)
    thermal_decay_rate_fraction = models.FloatField(null=True, blank=True)
    om_cost_us_dollars_per_gal = models.FloatField(null=True, blank=True)
    macrs_option_years = models.IntegerField(null=True, blank=True)
    macrs_bonus_pct = models.FloatField(null=True, blank=True)

    # Outputs
    size_gal = models.FloatField(null=True, blank=True)
    year_one_thermal_from_cold_tes_series_ton = ArrayField(
            models.FloatField(null=True, blank=True), default=list, null=True, blank=True)
    year_one_cold_tes_soc_series_pct = ArrayField(
            models.FloatField(null=True, blank=True), default=list, null=True, blank=True)

    @classmethod
    def create(cls, **kwargs):
        obj = cls(**kwargs)
        obj.save()

        return obj


class HotTESModel(models.Model):
    # Inputs
    run_uuid = models.UUIDField(unique=True)
    min_gal = models.FloatField(null=True, blank=True)
    max_gal = models.FloatField(null=True, blank=True)
    internal_efficiency_pct = models.FloatField(null=True, blank=True)
    soc_min_pct = models.FloatField(null=True, blank=True)
    soc_init_pct = models.FloatField(null=True, blank=True)
    installed_cost_us_dollars_per_gal = models.FloatField(null=True, blank=True)
    thermal_decay_rate_fraction = models.FloatField(null=True, blank=True)
    om_cost_us_dollars_per_gal = models.FloatField(null=True, blank=True)
    macrs_option_years = models.IntegerField(null=True, blank=True)
    macrs_bonus_pct = models.FloatField(null=True, blank=True)

    # Outputs
    size_gal = models.FloatField(null=True, blank=True)
    year_one_thermal_from_hot_tes_series_mmbtu_per_hr = ArrayField(
            models.FloatField(null=True, blank=True), default=list, null=True, blank=True)
    year_one_hot_tes_soc_series_pct = ArrayField(
            models.FloatField(null=True, blank=True), default=list, null=True, blank=True)

    @classmethod
    def create(cls, **kwargs):
        obj = cls(**kwargs)
        obj.save()

        return obj


class RCModel(models.Model):
    # Inputs
    run_uuid = models.UUIDField(unique=True)
    use_flexloads_model = models.BooleanField(default=False)
    a_matrix = ArrayField(models.FloatField(null=True, blank=True), null=True, blank=True)
    b_matrix = ArrayField(models.FloatField(null=True, blank=True), null=True, blank=True)
    u_inputs = ArrayField(models.FloatField(null=True, blank=True), null=True, blank=True)
    init_temperatures = ArrayField(models.FloatField(null=True, blank=True), null=True, blank=True)
    n_temp_nodes = models.IntegerField(null=True, blank=True)
    n_input_nodes = models.IntegerField(null=True, blank=True)
    injection_node = models.IntegerField(null=True, blank=True)
    space_node = models.IntegerField(null=True, blank=True)
    temperature_lower_bound = models.FloatField(null=True, blank=True)
    temperature_upper_bound = models.FloatField(null=True, blank=True)
    comfort_temp_lower_bound_degC = models.FloatField(null=True, blank=True)
    comfort_temp_upper_bound_degC = models.FloatField(null=True, blank=True)
    comfort_HVAC_value_usd_per_degC = models.FloatField(null=True, blank=True)

    # Outputs
    temperatures_degree_C = ArrayField(models.FloatField(null=True, blank=True), null=True, blank=True)
    comfort_penalty_degC = ArrayField(models.FloatField(null=True, blank=True), null=True, blank=True)

    @classmethod
    def create(cls, **kwargs):
        obj = cls(**kwargs)
        obj.save()

        return obj


class FlexTechACModel(models.Model):
    # Inputs
    run_uuid = models.UUIDField(unique=True)
    existing_kw = models.FloatField(null=True, blank=True, default=0)
    min_kw = models.FloatField(null=True, blank=True, default=0)
    max_kw = models.FloatField(null=True, blank=True, default=0)
    installed_cost_us_dollars_per_kw = models.FloatField(null=True, blank=True)
    om_cost_us_dollars_per_kw = models.FloatField(null=True, blank=True)
    prod_factor_series_kw = ArrayField(models.FloatField(null=True, blank=True), null=True, blank=True)
    cop = ArrayField(models.FloatField(null=True, blank=True), null=True, blank=True)
    shr = ArrayField(models.FloatField(null=True, blank=True), null=True, blank=True)
    fan_power_ratio = models.FloatField(null=True, blank=True)
    dse = models.FloatField(null=True, blank=True)

    # Outputs
    size_kw = models.FloatField(null=True, blank=True)
    year_one_power_production_series_kw = ArrayField(models.FloatField(null=True, blank=True), null=True, blank=True)
    year_one_power_consumption_series_kw = ArrayField(models.FloatField(null=True, blank=True), null=True, blank=True)

    @classmethod
    def create(cls, **kwargs):
        obj = cls(**kwargs)
        obj.save()

        return obj


class FlexTechHPModel(models.Model):
    # Inputs
    run_uuid = models.UUIDField(unique=True)
    existing_kw = models.FloatField(null=True, blank=True, default=0)
    min_kw = models.FloatField(null=True, blank=True, default=0)
    max_kw = models.FloatField(null=True, blank=True, default=0)
    installed_cost_us_dollars_per_kw = models.FloatField(null=True, blank=True)
    om_cost_us_dollars_per_kw = models.FloatField(null=True, blank=True)
    prod_factor_series_kw = ArrayField(models.FloatField(null=True, blank=True), null=True, blank=True)
    cop = ArrayField(models.FloatField(null=True, blank=True), null=True, blank=True)
    fan_power_ratio = models.FloatField(null=True, blank=True)
    dse = models.FloatField(null=True, blank=True)

    # Outputs
    size_kw = models.FloatField(null=True, blank=True)
    year_one_power_production_series_kw = ArrayField(models.FloatField(null=True, blank=True), null=True, blank=True)
    year_one_power_consumption_series_kw = ArrayField(models.FloatField(null=True, blank=True), null=True, blank=True)

    @classmethod
    def create(cls, **kwargs):
        obj = cls(**kwargs)
        obj.save()

        return obj


class HotWaterTankModel(models.Model):
    # Inputs
    run_uuid = models.UUIDField(unique=True)
    a_matrix = ArrayField(models.FloatField(null=True, blank=True), null=True, blank=True)
    b_matrix = ArrayField(models.FloatField(null=True, blank=True), null=True, blank=True)
    u_inputs = ArrayField(models.FloatField(null=True, blank=True), null=True, blank=True)
    init_temperatures_degC = ArrayField(models.FloatField(null=True, blank=True), null=True, blank=True)
    n_temp_nodes = models.IntegerField(null=True, blank=True)
    n_input_nodes = models.IntegerField(null=True, blank=True)
    injection_node = models.IntegerField(null=True, blank=True)
    water_node = models.IntegerField(null=True, blank=True)
    temperature_lower_bound_degC = models.FloatField(null=True, blank=True)
    temperature_upper_bound_degC = models.FloatField(null=True, blank=True)
    installed_cost_us_dollars_per_kw = models.FloatField(null=True, blank=True)
    comfort_temp_limit_degC = models.FloatField(null=True, blank=True)
    comfort_WH_value_usd_per_degC = models.FloatField(null=True, blank=True)
    
    # Output
    year_one_temperature_series_degC = ArrayField(models.FloatField(null=True, blank=True), null=True, blank=True)
    comfort_penalty_degC = ArrayField(models.FloatField(null=True, blank=True), null=True, blank=True)

    @classmethod
    def create(cls, **kwargs):
        obj = cls(**kwargs)
        obj.save()

        return obj


class FlexTechERWHModel(models.Model):
    # Inputs
    run_uuid = models.UUIDField(unique=True)
    size_kw = models.FloatField(null=True, blank=True, default=0)
    installed_cost_us_dollars_per_kw = models.FloatField(null=True, blank=True)

    # Output
    year_one_power_production_series_kw = ArrayField(models.FloatField(null=True, blank=True), null=True, blank=True)
    year_one_power_consumption_series_kw = ArrayField(models.FloatField(null=True, blank=True), null=True, blank=True)
    fraction_on = ArrayField(models.FloatField(null=True, blank=True), null=True, blank=True)

    @classmethod
    def create(cls, **kwargs):
        obj = cls(**kwargs)
        obj.save()

        return obj


class FlexTechHPWHModel(models.Model):
    # Inputs
    run_uuid = models.UUIDField(unique=True)
    size_kw = models.FloatField(null=True, blank=True, default=0)
    installed_cost_us_dollars_per_kw = models.FloatField(null=True, blank=True)
    prod_factor_series_kw = ArrayField(models.FloatField(null=True, blank=True), null=True, blank=True)
    cop = ArrayField(models.FloatField(null=True, blank=True), null=True, blank=True)

    # Output
    year_one_power_production_series_kw = ArrayField(models.FloatField(null=True, blank=True), null=True, blank=True)
    year_one_power_consumption_series_kw = ArrayField(models.FloatField(null=True, blank=True), null=True, blank=True)
    fraction_on = ArrayField(models.FloatField(null=True, blank=True), null=True, blank=True)

    @classmethod
    def create(cls, **kwargs):
        obj = cls(**kwargs)
        obj.save()

        return obj

class MessageModel(models.Model):
    """
    For Example:
    {"messages":{
                "warnings": "This is a warning message.",
                "error": "REopt had an error."
                }
    }
    """
    message_type = models.TextField(null=True, blank=True, default='')
    message = models.TextField(null=True, blank=True, default='')
    run_uuid = models.UUIDField(unique=False)
    description = models.TextField(null=True, blank=True, default='')

    @classmethod
    def create(cls, **kwargs):
        obj = cls(**kwargs)
        obj.save()

        return obj


class BadPost(models.Model):
    run_uuid = models.UUIDField(unique=True)
    post = models.TextField(null=True, blank=True)
    errors = models.TextField(null=True, blank=True)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        try:
            super(BadPost, self).save()
        except Exception as e:
            log.info("Database saving error: {}".format(e.args[0]))


def attribute_inputs(inputs):
    return {k: v for k, v in inputs.items() if k[0] == k[0].lower() and v is not None}


class ErrorModel(models.Model):
    task = models.TextField(null=True, blank=True, default='')
    name = models.TextField(null=True, blank=True, default='')
    run_uuid = models.TextField(null=True, blank=True, default='')
    user_uuid = models.TextField(null=True, blank=True, default='')
    message = models.TextField(null=True, blank=True, default='')
    traceback = models.TextField(null=True, blank=True, default='')
    created = models.DateTimeField(auto_now_add=True)


class ModelManager(object):

    def __init__(self):
        self.scenarioM = None
        self.siteM = None
        self.financialM = None
        self.load_profileM = None
        self.load_profile_boiler_fuelM = None
        self.load_profile_chiller_electricM = None
        self.electric_tariffM = None
        self.fuel_tariffM = None
        self.pvM = None
        self.windM = None
        self.storageM = None
        self.generatorM = None
        self.chpM = None
        self.boilerM = None
        self.electric_chillerM = None
        self.absorption_chillerM = None
        self.hot_tesM = None
        self.cold_tesM = None
        self.rcM = None
        self.flex_tech_acM = None
        self.flex_tech_hpM = None
        self.hot_water_tankM = None
        self.flex_tech_erwhM = None
        self.flex_tech_hpwhM = None
        self.profileM = None
        self.messagesM = None

    def create_and_save(self, data):
        """
        create and save models
        saves input json to db tables
        :param data: dict, constructed in api.py, mirrors reopt api response structure
        """
        d = data["inputs"]['Scenario']
        scenario_dict = data["outputs"]['Scenario'].copy()
        scenario_dict.update(d)

        self.scenarioM = ScenarioModel.create(**attribute_inputs(scenario_dict))
        self.profileM = ProfileModel.create(run_uuid=self.scenarioM.run_uuid,
                                            **attribute_inputs(scenario_dict['Profile']))
        self.siteM = SiteModel.create(run_uuid=self.scenarioM.run_uuid, **attribute_inputs(d['Site']))
        self.financialM = FinancialModel.create(run_uuid=self.scenarioM.run_uuid,
                                                **attribute_inputs(d['Site']['Financial']))
        self.load_profileM = LoadProfileModel.create(run_uuid=self.scenarioM.run_uuid,
                                                     **attribute_inputs(d['Site']['LoadProfile']))
        self.load_profile_boiler_fuelM = LoadProfileBoilerFuelModel.create(run_uuid=self.scenarioM.run_uuid,
                                                     **attribute_inputs(d['Site']['LoadProfileBoilerFuel']))
        self.load_profile_chiller_electricM = LoadProfileChillerThermalModel.create(run_uuid=self.scenarioM.run_uuid,
                                                     **attribute_inputs(d['Site']['LoadProfileChillerThermal']))
        self.electric_tariffM = ElectricTariffModel.create(run_uuid=self.scenarioM.run_uuid,
                                                           **attribute_inputs(d['Site']['ElectricTariff']))
        self.fuel_tariffM = FuelTariffModel.create(run_uuid=self.scenarioM.run_uuid,
                                                           **attribute_inputs(d['Site']['FuelTariff']))
        if type(d['Site']['PV'])==list:
            self.pvM = [PVModel.create(run_uuid=self.scenarioM.run_uuid, **attribute_inputs(d['Site']['PV'][0]))]
            for pv in d['Site']['PV'][1:]:
                self.pvM.append(PVModel.create(run_uuid=self.scenarioM.run_uuid, **attribute_inputs(pv)))
        if type(d['Site']['PV'])==dict:
            self.pvM = PVModel.create(run_uuid=self.scenarioM.run_uuid, **attribute_inputs(d['Site']['PV']))
        self.windM = WindModel.create(run_uuid=self.scenarioM.run_uuid, **attribute_inputs(d['Site']['Wind']))
        self.storageM = StorageModel.create(run_uuid=self.scenarioM.run_uuid, **attribute_inputs(d['Site']['Storage']))
        self.generatorM = GeneratorModel.create(run_uuid=self.scenarioM.run_uuid, **attribute_inputs(d['Site']['Generator']))
        self.chpM = CHPModel.create(run_uuid=self.scenarioM.run_uuid, **attribute_inputs(d['Site']['CHP']))
        self.boilerM = BoilerModel.create(run_uuid=self.scenarioM.run_uuid, **attribute_inputs(d['Site']['Boiler']))
        self.electric_chillerM = ElectricChillerModel.create(run_uuid=self.scenarioM.run_uuid,
                                                             **attribute_inputs(d['Site']['ElectricChiller']))
        self.absorption_chillerM = AbsorptionChillerModel.create(run_uuid=self.scenarioM.run_uuid,
                                                             **attribute_inputs(d['Site']['AbsorptionChiller']))
        self.hot_tesM = HotTESModel.create(run_uuid=self.scenarioM.run_uuid,
                                                             **attribute_inputs(d['Site']['HotTES']))
        self.cold_tesM = ColdTESModel.create(run_uuid=self.scenarioM.run_uuid,
                                           **attribute_inputs(d['Site']['ColdTES']))
        self.rcM = RCModel.create(run_uuid=self.scenarioM.run_uuid,
                                           **attribute_inputs(d['Site']['RC']))
        self.flex_tech_acM = FlexTechACModel.create(run_uuid=self.scenarioM.run_uuid,
                                           **attribute_inputs(d['Site']['FlexTechAC']))
        self.flex_tech_hpM = FlexTechHPModel.create(run_uuid=self.scenarioM.run_uuid,
                                           **attribute_inputs(d['Site']['FlexTechHP']))
        self.hot_water_tankM = HotWaterTankModel.create(run_uuid=self.scenarioM.run_uuid,
                                           **attribute_inputs(d['Site']['HotWaterTank']))
        self.flex_tech_erwhM = FlexTechERWHModel.create(run_uuid=self.scenarioM.run_uuid,
                                           **attribute_inputs(d['Site']['FlexTechERWH']))
        self.flex_tech_hpwhM = FlexTechHPWHModel.create(run_uuid=self.scenarioM.run_uuid,
                                           **attribute_inputs(d['Site']['FlexTechHPWH']))
        for message_type, message in data['messages'].items():
            MessageModel.create(run_uuid=self.scenarioM.run_uuid, message_type=message_type, message=message)

    @staticmethod
    def updateModel(modelName, modelData, run_uuid, number=None):
        if number==None:
            eval(modelName).objects.filter(run_uuid=run_uuid).update(**attribute_inputs(modelData))
        else:
            if 'PV' in modelName:
                eval(modelName).objects.filter(run_uuid=run_uuid, pv_number=number).update(**attribute_inputs(modelData))


    @staticmethod
    def remove(run_uuid):
        """
        remove Scenario from database
        :param run_uuid: id of Scenario
        :return: None
        """
        ScenarioModel.objects.filter(run_uuid=run_uuid).delete()
        ProfileModel.objects.filter(run_uuid=run_uuid).delete()
        SiteModel.objects.filter(run_uuid=run_uuid).delete()
        FinancialModel.objects.filter(run_uuid=run_uuid).delete()
        LoadProfileModel.objects.filter(run_uuid=run_uuid).delete()
        LoadProfileBoilerFuelModel.objects.filter(run_uuid=run_uuid).delete()
        LoadProfileChillerThermalModel.objects.filter(run_uuid=run_uuid).delete()
        ElectricTariffModel.objects.filter(run_uuid=run_uuid).delete()
        PVModel.objects.filter(run_uuid=run_uuid).delete()
        WindModel.objects.filter(run_uuid=run_uuid).delete()
        StorageModel.objects.filter(run_uuid=run_uuid).delete()
        GeneratorModel.objects.filter(run_uuid=run_uuid).delete()
        CHPModel.objects.filter(run_uuid=run_uuid).delete()
        BoilerModel.objects.filter(run_uuid=run_uuid).delete()
        ElectricChillerModel.objects.filter(run_uuid=run_uuid).delete()
        AbsorptionChillerModel.objects.filter(run_uuid=run_uuid).delete()
        HotTESModel.objects.filter(run_uuid=run_uuid).delete()
        ColdTESModel.objects.filter(run_uuid=run_uuid).delete()
        RCModel.objects.filter(run_uuid=run_uuid).delete()
        FlexTechACModel.objects.filter(run_uuid=run_uuid).delete()
        FlexTechHPModel.objects.filter(run_uuid=run_uuid).delete()
        HotWaterTankModel.objects.filter(run_uuid=run_uuid).delete()
        FlexTechERWHModel.objects.filter(run_uuid=run_uuid).delete()
        FlexTechHPWHModel.objects.filter(run_uuid=run_uuid).delete()
        MessageModel.objects.filter(run_uuid=run_uuid).delete()
        ErrorModel.objects.filter(run_uuid=run_uuid).delete()

    @staticmethod
    def update(data, run_uuid):
        """
        save Scenario results in database
        :param data: dict, constructed in api.py, mirrors reopt api response structure
        :param model_ids: dict, optional, for use when updating existing models that have not been created in memory
        :return: None
        """
        d = data["outputs"]["Scenario"]
        ProfileModel.objects.filter(run_uuid=run_uuid).update(**attribute_inputs(d['Profile']))
        SiteModel.objects.filter(run_uuid=run_uuid).update(**attribute_inputs(d['Site']))
        FinancialModel.objects.filter(run_uuid=run_uuid).update(**attribute_inputs(d['Site']['Financial']))
        LoadProfileModel.objects.filter(run_uuid=run_uuid).update(**attribute_inputs(d['Site']['LoadProfile']))
        LoadProfileBoilerFuelModel.objects.filter(run_uuid=run_uuid).update(
            **attribute_inputs(d['Site']['LoadProfileBoilerFuel']))
        LoadProfileChillerThermalModel.objects.filter(run_uuid=run_uuid).update(
            **attribute_inputs(d['Site']['LoadProfileChillerThermal']))
        ElectricTariffModel.objects.filter(run_uuid=run_uuid).update(**attribute_inputs(d['Site']['ElectricTariff']))
        FuelTariffModel.objects.filter(run_uuid=run_uuid).update(**attribute_inputs(d['Site']['FuelTariff']))
        if type(d['Site']['PV'])==dict:
            PVModel.objects.filter(run_uuid=run_uuid).update(**attribute_inputs(d['Site']['PV']))
        if type(d['Site']['PV']) == list:
            for pv in d['Site']['PV']:
                PVModel.objects.filter(run_uuid=run_uuid, pv_number=pv['pv_number']).update(**attribute_inputs(pv))
        WindModel.objects.filter(run_uuid=run_uuid).update(**attribute_inputs(d['Site']['Wind']))
        StorageModel.objects.filter(run_uuid=run_uuid).update(**attribute_inputs(d['Site']['Storage']))
        GeneratorModel.objects.filter(run_uuid=run_uuid).update(**attribute_inputs(d['Site']['Generator']))
        CHPModel.objects.filter(run_uuid=run_uuid).update(**attribute_inputs(d['Site']['CHP']))
        BoilerModel.objects.filter(run_uuid=run_uuid).update(**attribute_inputs(d['Site']['Boiler']))
        ElectricChillerModel.objects.filter(run_uuid=run_uuid).update(**attribute_inputs(d['Site']['ElectricChiller']))
        AbsorptionChillerModel.objects.filter(run_uuid=run_uuid).update(
            **attribute_inputs(d['Site']['AbsorptionChiller']))
        HotTESModel.objects.filter(run_uuid=run_uuid).update(**attribute_inputs(d['Site']['HotTES']))
        ColdTESModel.objects.filter(run_uuid=run_uuid).update(**attribute_inputs(d['Site']['ColdTES']))
        RCModel.objects.filter(run_uuid=run_uuid).update(**attribute_inputs(d['Site']['RC']))
        FlexTechACModel.objects.filter(run_uuid=run_uuid).update(**attribute_inputs(d['Site']['FlexTechAC']))
        FlexTechHPModel.objects.filter(run_uuid=run_uuid).update(**attribute_inputs(d['Site']['FlexTechHP']))
        HotWaterTankModel.objects.filter(run_uuid=run_uuid).update(**attribute_inputs(d['Site']['HotWaterTank']))
        FlexTechERWHModel.objects.filter(run_uuid=run_uuid).update(**attribute_inputs(d['Site']['FlexTechERWH']))
        FlexTechHPWHModel.objects.filter(run_uuid=run_uuid).update(**attribute_inputs(d['Site']['FlexTechHPWH']))

        for message_type, message in data['messages'].items():
            if len(MessageModel.objects.filter(run_uuid=run_uuid, message=message)) > 0:
                # message already saved
                pass
            else:
                MessageModel.create(run_uuid=run_uuid, message_type=message_type, message=message)
        # Do this last so that the status does not change to optimal before the rest of the results are filled in
        ScenarioModel.objects.filter(run_uuid=run_uuid).update(**attribute_inputs(d))  # force_update=True

    @staticmethod
    def update_scenario_and_messages(data, run_uuid):
        """
        save Scenario results in database
        :param data: dict, constructed in api.py, mirrors reopt api response structure
        :return: None
        """
        d = data["outputs"]["Scenario"]
        ScenarioModel.objects.filter(run_uuid=run_uuid).update(**attribute_inputs(d))
        for message_type, message in data['messages'].items():
            if len(MessageModel.objects.filter(run_uuid=run_uuid, message=message)) > 0:
                # message already saved
                pass
            else:
                MessageModel.create(run_uuid=run_uuid, message_type=message_type, message=message)

    @staticmethod
    def add_user_uuid(user_uuid, run_uuid):
        """
        update the user_uuid associated with a Scenario
        :param user_uuid: string
        :param run_uuid: string
        :return: None
        """
        d = {"user_uuid": user_uuid}
        ScenarioModel.objects.filter(run_uuid=run_uuid).update(**d)
        ErrorModel.objects.filter(run_uuid=run_uuid).update(**d)

    @staticmethod
    def make_response(run_uuid):
        """
        Reconstruct response dictionary from postgres tables (django models).
        NOTE: postgres column type UUID is not JSON serializable. Work-around is removing those columns and then
              adding back into outputs->Scenario as string.
        :param run_uuid:
        :return: nested dictionary matching nested_output_definitions
        """
        def remove_number(k, d):
            if k in d.keys():
                del d[k]
            return d

        def remove_ids(d):
            del d['run_uuid']
            del d['id']
            return d

        def move_outs_to_ins(site_key, resp):
            if not (resp['outputs']['Scenario']['Site'].get(site_key) or None) in [None, [], {}]:
                resp['inputs']['Scenario']['Site'][site_key] = dict()

                for k in nested_input_definitions['Scenario']['Site'][site_key].keys():
                    try:
                        if site_key == "PV":
                            if type(resp['outputs']['Scenario']['Site'][site_key])==dict:
                                resp['inputs']['Scenario']['Site'][site_key][k] = resp['outputs']['Scenario']['Site'][site_key][k]
                                del resp['outputs']['Scenario']['Site'][site_key][k]

                            elif type(resp['outputs']['Scenario']['Site'][site_key])==list:
                                max_order = max([p.get('pv_number') for p in resp['outputs']['Scenario']['Site'][site_key]])
                                if resp['inputs']['Scenario']['Site'].get(site_key) == {}:
                                    resp['inputs']['Scenario']['Site'][site_key] = []
                                if len(resp['inputs']['Scenario']['Site'][site_key]) == 0 :
                                    for _ in range(max_order):
                                        resp['inputs']['Scenario']['Site'][site_key].append({})
                                for i in range(max_order):
                                    resp['inputs']['Scenario']['Site'][site_key][i][k] = resp['outputs']['Scenario']['Site'][site_key][i][k]
                                    if isinstance(resp['inputs']['Scenario']['Site'][site_key][i][k], list):
                                        if len(resp['inputs']['Scenario']['Site'][site_key][i][k]) == 1:
                                            resp['inputs']['Scenario']['Site'][site_key][i][k] = \
                                                resp['inputs']['Scenario']['Site'][site_key][i][k][0]
                                    if k not in ['pv_name']:
                                        del resp['outputs']['Scenario']['Site'][site_key][i][k]

                        # special handling for inputs that can be scalar or array,
                        # (which we have to make an array in database)
                        else:
                            resp['inputs']['Scenario']['Site'][site_key][k] = resp['outputs']['Scenario']['Site'][site_key][k]
                            if isinstance(resp['inputs']['Scenario']['Site'][site_key][k], list):
                                if len(resp['inputs']['Scenario']['Site'][site_key][k]) == 1:
                                    resp['inputs']['Scenario']['Site'][site_key][k] = \
                                        resp['inputs']['Scenario']['Site'][site_key][k][0]
                                elif len(resp['inputs']['Scenario']['Site'][site_key][k]) == 0:
                                    del resp['inputs']['Scenario']['Site'][site_key][k]
                            del resp['outputs']['Scenario']['Site'][site_key][k]
                    except KeyError:  # known exception for k = urdb_response (user provided blended rates)
                        resp['inputs']['Scenario']['Site'][site_key][k] = None

        # add try/except for get fail / bad run_uuid
        site_keys = ['PV', 'Storage', 'Financial', 'LoadProfile', 'LoadProfileBoilerFuel', 'LoadProfileChillerThermal',
                     'ElectricTariff', 'FuelTariff', 'Generator', 'Wind', 'CHP', 'Boiler', 'ElectricChiller',
                     'AbsorptionChiller', 'HotTES', 'ColdTES', 'RC', 'FlexTechAC', 'FlexTechHP', 'HotWaterTank',
                     'FlexTechERWH', 'FlexTechHPWH']

        resp = dict()
        resp['outputs'] = dict()
        resp['outputs']['Scenario'] = dict()
        resp['outputs']['Scenario']['Profile'] = dict()
        resp['inputs'] = dict()
        resp['inputs']['Scenario'] = dict()
        resp['inputs']['Scenario']['Site'] = dict()
        resp['messages'] = dict()

        try:
            scenario_model = ScenarioModel.objects.get(run_uuid=run_uuid)
        except Exception as e:
            if isinstance(e, models.ObjectDoesNotExist):
                resp['messages']['error'] = (
                    "run_uuid {} not in database. "
                    "You may have hit the results endpoint too quickly after POST'ing scenario, "
                    "you may have a typo in your run_uuid, or the scenario was deleted.").format(run_uuid)
                resp['outputs']['Scenario']['status'] = 'error'
                return resp
            else:
                raise Exception
        scenario_data = remove_ids(model_to_dict(scenario_model))
        del scenario_data['job_type']
        resp['outputs']['Scenario'] = scenario_data
        resp['outputs']['Scenario']['run_uuid'] = str(run_uuid)
        resp['outputs']['Scenario']['Site'] = remove_ids(model_to_dict(SiteModel.objects.get(run_uuid=run_uuid)))

        financial_record = FinancialModel.objects.filter(run_uuid=run_uuid) or {}
        if financial_record is not {}:
            resp['outputs']['Scenario']['Site']['Financial'] = remove_ids(model_to_dict(financial_record[0]))

        loadprofile_record = LoadProfileModel.objects.filter(run_uuid=run_uuid) or {}
        if loadprofile_record is not {}:
            resp['outputs']['Scenario']['Site']['LoadProfile'] = remove_ids(model_to_dict(loadprofile_record[0]))

        lpbf_record = LoadProfileBoilerFuelModel.objects.filter(run_uuid=run_uuid) or {}
        if not lpbf_record == {}:
            resp['outputs']['Scenario']['Site']['LoadProfileBoilerFuel'] = remove_ids(model_to_dict(lpbf_record[0]))

        lpct_record = LoadProfileChillerThermalModel.objects.filter(run_uuid=run_uuid) or {}
        if not lpct_record  == {}:
            resp['outputs']['Scenario']['Site']['LoadProfileChillerThermal'] = remove_ids(model_to_dict(lpct_record[0]))

        etariff_record = ElectricTariffModel.objects.filter(run_uuid=run_uuid) or {}
        if not etariff_record == {}:
            resp['outputs']['Scenario']['Site']['ElectricTariff'] = remove_ids(model_to_dict(etariff_record[0]))

        fueltariff_record = FuelTariffModel.objects.filter(run_uuid=run_uuid) or {}
        if not fueltariff_record == {}:
            resp['outputs']['Scenario']['Site']['FuelTariff'] = remove_ids(model_to_dict(fueltariff_record[0]))

        storage_record = StorageModel.objects.filter(run_uuid=run_uuid) or {}
        if not storage_record == {}:
            resp['outputs']['Scenario']['Site']['Storage'] = remove_ids(model_to_dict(storage_record[0]))

        generator_record = GeneratorModel.objects.filter(run_uuid=run_uuid) or {}
        if not generator_record == {}:
            resp['outputs']['Scenario']['Site']['Generator'] = remove_ids(model_to_dict(generator_record[0]))

        wind_record = WindModel.objects.filter(run_uuid=run_uuid) or {}
        if not wind_record == {}:
            resp['outputs']['Scenario']['Site']['Wind'] = remove_ids(model_to_dict(wind_record[0]))

        chp_record = CHPModel.objects.filter(run_uuid=run_uuid) or {}
        if not chp_record == {}:
            resp['outputs']['Scenario']['Site']['CHP'] = remove_ids(model_to_dict(chp_record[0]))

        boiler_record = BoilerModel.objects.filter(run_uuid=run_uuid) or {}
        if not boiler_record == {}:
            resp['outputs']['Scenario']['Site']['Boiler'] = remove_ids(model_to_dict(boiler_record[0]))

        echiller_record = ElectricChillerModel.objects.filter(run_uuid=run_uuid) or {}
        if not echiller_record == {}:
            resp['outputs']['Scenario']['Site']['ElectricChiller'] = remove_ids(model_to_dict(echiller_record[0]))

        achiller_record = AbsorptionChillerModel.objects.filter(run_uuid=run_uuid) or {}
        if not achiller_record == {}:
            resp['outputs']['Scenario']['Site']['AbsorptionChiller'] = remove_ids(model_to_dict(achiller_record[0]))

        hottes_record = HotTESModel.objects.filter(run_uuid=run_uuid) or {}
        if not hottes_record == {}:
            resp['outputs']['Scenario']['Site']['HotTES'] = remove_ids(model_to_dict(hottes_record[0]))

        coldtes_record = ColdTESModel.objects.filter(run_uuid=run_uuid) or {}
        if not coldtes_record == {}:
            resp['outputs']['Scenario']['Site']['ColdTES'] = remove_ids(model_to_dict(coldtes_record[0]))

        rc_record = RCModel.objects.filter(run_uuid=run_uuid) or {}
        if not rc_record == {}:
            resp['outputs']['Scenario']['Site']['RC'] = remove_ids(model_to_dict(rc_record[0]))

        flextechac_record = FlexTechACModel.objects.filter(run_uuid=run_uuid) or {}
        if not flextechac_record == {}:
            resp['outputs']['Scenario']['Site']['FlexTechAC'] = remove_ids(model_to_dict(flextechac_record[0]))

        flextechhp_record = FlexTechHPModel.objects.filter(run_uuid=run_uuid) or {}
        if not flextechhp_record == {}:
            resp['outputs']['Scenario']['Site']['FlexTechHP'] = remove_ids(model_to_dict(flextechhp_record[0]))

        hotwatertank_record = HotWaterTankModel.objects.filter(run_uuid=run_uuid) or {}
        if not hotwatertank_record == {}:
            resp['outputs']['Scenario']['Site']['HotWaterTank'] = remove_ids(model_to_dict(hotwatertank_record[0]))

        flextecherwh_record = FlexTechERWHModel.objects.filter(run_uuid=run_uuid) or {}
        if not flextecherwh_record == {}:
            resp['outputs']['Scenario']['Site']['FlexTechERWH'] = remove_ids(model_to_dict(flextecherwh_record[0]))

        flextechhpwh_record = FlexTechHPWHModel.objects.filter(run_uuid=run_uuid) or {}
        if not flextechhpwh_record == {}:
            resp['outputs']['Scenario']['Site']['FlexTechHPWH'] = remove_ids(model_to_dict(flextechhpwh_record[0]))

        resp['outputs']['Scenario']['Site']['PV'] = []
        for x in PVModel.objects.filter(run_uuid=run_uuid).order_by('pv_number'):
            resp['outputs']['Scenario']['Site']['PV'].append(remove_ids(model_to_dict(x)))

        profile_data = ProfileModel.objects.filter(run_uuid=run_uuid)
        if len(profile_data) > 0:
            resp['outputs']['Scenario']['Profile'] = remove_ids(model_to_dict(profile_data[0]))

        for m in MessageModel.objects.filter(run_uuid=run_uuid).values('message_type', 'message'):
            resp['messages'][m['message_type']] = m['message']

        for scenario_key in nested_input_definitions['Scenario'].keys():
            if scenario_key.islower():
                resp['inputs']['Scenario'][scenario_key] = resp['outputs']['Scenario'][scenario_key]
                del resp['outputs']['Scenario'][scenario_key]

        for site_key in nested_input_definitions['Scenario']['Site'].keys():
            if site_key.islower():
                resp['inputs']['Scenario']['Site'][site_key] = resp['outputs']['Scenario']['Site'][site_key]
                del resp['outputs']['Scenario']['Site'][site_key]

            elif site_key in site_keys:
                move_outs_to_ins(site_key, resp=resp)

        if len(resp['inputs']['Scenario']['Site']['PV']) == 1:
            resp['inputs']['Scenario']['Site']['PV'] = resp['inputs']['Scenario']['Site']['PV'][0]
        resp['outputs']['Scenario']['Site']['PV'] = [remove_number('pv_number', x) for x in resp['outputs']['Scenario']['Site']['PV']]
        if len(resp['outputs']['Scenario']['Site']['PV']) == 1:
            resp['outputs']['Scenario']['Site']['PV'] = resp['outputs']['Scenario']['Site']['PV'][0]

        if resp['inputs']['Scenario']['Site']['LoadProfile'].get('doe_reference_name') == '':
            del resp['inputs']['Scenario']['Site']['LoadProfile']['doe_reference_name']

        #Preserving Backwards Compatability
        resp['inputs']['Scenario']['Site']['LoadProfile']['outage_start_hour'] = resp['inputs']['Scenario']['Site']['LoadProfile'].get('outage_start_time_step')
        if resp['inputs']['Scenario']['Site']['LoadProfile']['outage_start_hour'] is not None:
            resp['inputs']['Scenario']['Site']['LoadProfile']['outage_start_hour'] -= 1
        resp['inputs']['Scenario']['Site']['LoadProfile']['outage_end_hour'] = resp['inputs']['Scenario']['Site']['LoadProfile'].get('outage_end_time_step')
        if resp['inputs']['Scenario']['Site']['LoadProfile']['outage_end_hour'] is not None:
            resp['inputs']['Scenario']['Site']['LoadProfile']['outage_end_hour'] -= 1
        return resp
