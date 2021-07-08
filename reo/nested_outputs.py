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
from .nested_inputs import nested_input_definitions, list_of_float


def list_of_string(inpt):
    return [str(i) for i in inpt]

nested_output_definitions = {

    "inputs": nested_input_definitions,

    "outputs": {

          "Scenario": {
            "run_uuid": {
              "type": "str",
              "description": "Unique id",
              "units": "none"
            },
            "api_version": {
              "type": "str"
            },
            "status": {
              "type": "str",
              "description": "Problem Status",
              "units": "none"
            },
            "lower_bound": {
              "type": float,
              "description": "Lower bound of optimal case",
            },
            "optimality_gap": {
              "type": float,
              "description": "Final optimization gap achieved in the optimal case",
            },
            "Profile": {
                "pre_setup_scenario_seconds": {
                  "type": "float",
                  "description": "Time spent before setting up scenario",
                  "units": "seconds"
                },
                "setup_scenario_seconds": {
                  "type": "float",
                  "description": "Time spent setting up scenario",
                  "units": "seconds"
                },
                "reopt_seconds":{
                  "type": "float",
                  "description": "Time spent solving scenario",
                  "units": "seconds"
                },
                "reopt_bau_seconds": {
                  "type": "float",
                  "description": "Time spent solving base-case scenario",
                  "units": "seconds"
                },
                "parse_run_outputs_seconds": {
                  "type": "float",
                  "description": "Time spent parsing outputs",
                  "units": "seconds"
                }
            },

            "Site": {
              "year_one_emissions_lb_C02": {
                  "type": "int",
                  "description": "Total equivalent pounds of carbon dioxide emitted from the site in the first year.",
                  "units": "lb CO2"
                },
              "year_one_emissions_bau_lb_C02": {
                  "type": "int",
                  "description": "Total equivalent pounds of carbon dioxide emitted from the site use in the first year in the BAU case.",
                  "units": "lb CO2"
                },
              "renewable_electricity_energy_pct": {
                "type": float,
                "description": (
                  "Portion of electrictrity use that is derived from on-site renewable resource generation in year one."
                  "Calculated as total PV and Wind generation in year one (including exports), "
                  "divided by the total annual load in year one."
                  ),
                "units": "%"
              },

              "LoadProfile": {
                "year_one_electric_load_series_kw": {
                  "type": "list_of_float",
                  "description": "Year one hourly time series of electric load",
                  "units": "kW"
                },
                "critical_load_series_kw": {
                  "type": "list_of_float",
                  "description": "Hourly critical load for outage simulator. Values are either uploaded by user, or determined from typical load (either uploaded or simulated) and critical_load_pct.",
                  "units": "kW"
                },
                "annual_calculated_kwh": {
                  "type": "float",
                  "description": "Annual energy consumption calculated by summing up 8760 load profile",
                  "units": "kWh"
                },
                "resilience_check_flag": {
                  "type": "boolean",
                  "description": "BAU resilience check status for existing system"
                },
                "sustain_hours": {
                  "type": "int",
                  "description": "Number of hours the existing system can sustain with resilience check",
                  "units": "hours"
                },
                "bau_sustained_time_steps": {
                  "type": "int",
                  "description": "Number of time steps the existing system can sustain the critical load",
                  "units": "time steps"
                }
              },

              "LoadProfileBoilerFuel": {
                "year_one_boiler_fuel_load_series_mmbtu_per_hr": {
                  "type": list_of_float,
                  "description": "Year one hourly time series of boiler fuel load",
                  "units": "mmbtu_per_hr"
                },
                "year_one_boiler_thermal_load_series_mmbtu_per_hr": {
                  "type": list_of_float,
                  "description": "Year one hourly time series of boiler thermal load",
                  "units": "mmbtu_per_hr"
                },
                "annual_calculated_boiler_fuel_load_mmbtu_bau": {
                  "type": float,
                  "description": "Annual boiler fuel consumption calculated by summing up 8760 boiler fuel "
                                 "load profile in business-as-usual case.",
                  "units": "mmbtu"
                }
              },

              "LoadProfileChillerThermal": {
                "year_one_chiller_electric_load_series_kw": {
                  "type": list_of_float,
                  "description": "Year one hourly time series of chiller electric load",
                  "units": "kW"
                },
                "year_one_chiller_thermal_load_series_ton": {
                  "type": list_of_float,
                  "description": "Year one hourly time series of electric chiller thermal load",
                  "units": "Ton"
                },
                "year_one_chiller_electric_load_series_kw_bau": {
                  "type": list_of_float,
                  "description": "Year one hourly time series of chiller electric load in business-as-usual case.",
                  "units": "kW"
                },
                "annual_calculated_kwh_bau": {
                  "type": float,
                  "description": "Annual chiller electric consumption calculated by summing up 8760 electric load "
                                 "profile in business-as-usual case.",
                  "units": "kWh"
                }
              },

              "Financial": {
                "lcc_us_dollars": {
                  "type": "float",
                  "description": "Optimal lifecycle cost",
                  "units": "dollars"
                },
                "lcc_bau_us_dollars": {
                  "type": "float",
                  "description": "Business as usual lifecycle cost",
                  "units": "dollars"
                },
                "npv_us_dollars": {
                  "type": "float",
                  "description": "Net present value of savings realized by the project",
                  "units": "dollars"
                },
                "net_capital_costs_plus_om_us_dollars": {
                  "type": "float",
                  "description": "Capital cost for all technologies plus present value of operations and maintenance over anlaysis period",
                  "units": "$"
                },
                "net_om_us_dollars_bau": {
                  "type": "float",
                  "description": "Business-as-usual present value of operations and maintenance over anlaysis period",
                  "units": "$"
                },
                "net_capital_costs": {
                  "type": "float",
                  "description": "Net capital costs for all technologies, in present value, including replacement costs and incentives.",
                  "units": "$"
                },
                "microgrid_upgrade_cost_us_dollars": {
                  "type": "float",
                  "description": "Cost in US dollars to make a distributed energy system islandable from the grid. Determined by multiplying the total capital costs of resultant energy systems from REopt (such as PV and Storage system) with the input value for microgrid_upgrade_cost_pct (which defaults to 0.30)."
                },
                "initial_capital_costs": {
                  "type": "float",
                  "description": "Up-front capital costs for all technologies, in present value, excluding replacement costs and incentives.",
                  "units": "$"
                },
                "initial_capital_costs_after_incentives": {
                  "type": "float",
                  "description": "Up-front capital costs for all technologies, in present value, excluding replacement costs, including incentives.",
                  "units": "$"
                },
                "replacement_costs": {
                  "type": "float",
                  "description": "Net replacement costs for all technologies, in future value, excluding incentives.",
                  "units": "$"
                },
                "om_and_replacement_present_cost_after_tax_us_dollars": {
                  "type": "float",
                  "description": "Net O&M and replacement costs in present value, after-tax.",
                  "units": "$"
                },
                "total_om_costs_us_dollars": {
                  "type": "float",
                  "description": "Total operations and maintenance cost over analysis period.",
                  "units": "$"
                },
                "year_one_om_costs_us_dollars": {
                  "type": "float",
                  "description": "Year one operations and maintenance cost after tax.",
                  "units": "$"
                },
                "year_one_om_costs_before_tax_us_dollars": {
                  "type": "float",
                  "description": "Year one operations and maintenance cost before tax.",
                  "units": "$"
                },
                "simple_payback_years": {
                  "type": "float",
                  "description": ("Number of years until the cumulative annual cashflow turns positive. "
                                  "If the cashflow becomes negative again after becoming positive (i.e. due to battery repalcement costs)"
                                  " then simple payback is increased by the number of years that the cash flow "
                                  "is negative beyond the break-even year."),
                  "units": "$"
                },
                "irr_pct": {
                  "type": "float",
                  "description": ("internal Rate of Return of the cost-optimal system. In two-party cases the "
                                  "developer discount rate is used in place of the offtaker discount rate."),
                  "units": "%"
                 },
                 "net_present_cost_us_dollars": {
                  "type": "float",
                  "description": ("Present value of the total costs incurred by the third-party owning and operating the "
                                  "distributed energy resource assets."),
                  "units": "$"
                 },
                 "annualized_payment_to_third_party_us_dollars": {
                  "type": "float",
                  "description": ("The annualized amount the host will pay to the third-party owner over the life of the project."),
                  "units": "$"
                 },
                 "offtaker_annual_free_cashflow_series_us_dollars": {
                  "type": "float",
                  "description": ("Annual free cashflow for the host in the optimal case for all analysis years, including year 0. Future years have not been discounted to account for the time value of money."),
                  "units": "$"
                 },
                 "offtaker_discounted_annual_free_cashflow_series_us_dollars": {
                  "type": "float",
                  "description": ("Annual discounted free cashflow for the host in the optimal case for all analysis years, including year 0. Future years have been discounted to account for the time value of money."),
                  "units": "$"
                 },
                 "offtaker_annual_free_cashflow_series_bau_us_dollars": {
                  "type": "float",
                  "description": ("Annual free cashflow for the host in the business-as-usual case for all analysis years, including year 0. Future years have not been discounted to account for the time value of money. Only calculated in the non-third-party case."),
                  "units": "$"
                 },
                 "offtaker_discounted_annual_free_cashflow_series_bau_us_dollars": {
                  "type": "float",
                  "description": ("Annual discounted free cashflow for the host in the business-as-usual case for all analysis years, including year 0. Future years have been discounted to account for the time value of money. Only calculated in the non-third-party case."),
                  "units": "$"
                 },
                 "developer_annual_free_cashflow_series_bau_us_dollars": {
                  "type": "float",
                  "description": ("Annual free cashflow for the developer in the business-as-usual third party case for all analysis years, including year 0. Future years have not been discounted to account for the time value of money. Only calculated in the third-party case."),
                  "units": "$"
                 },
                "developer_om_and_replacement_present_cost_after_tax_us_dollars": {
                  "type": "float",
                  "description": ("Net O&M and replacement costs in present value, after-tax for the third-party "
                                  "developer. Only calculated in the third-party case."),
                  "units": "$"
                 }
              },

              "PV": {
                "pv_name": {
                  "type": "str",
                  "description": "Site name/description"
                },
                "size_kw": {
                  "type": "float",
                  "description": "Optimal PV system size",
                  "units": "kW"
                },
                "average_yearly_energy_produced_kwh": {
                  "type": "float",
                  "description": "Average annual energy produced by the PV system over one year",
                  "units": "kWh"
                },
                "average_yearly_energy_produced_bau_kwh": {
                  "type": "float",
                  "description": "Average annual energy produced by the existing PV system over one year",
                  "units": "kWh"
                },
                "average_yearly_energy_exported_kwh": {
                  "type": "float",
                  "description": "Average annual energy exported by the PV system",
                  "units": "kWh"
                },
                "year_one_energy_produced_kwh": {
                  "type": "float",
                  "description": "Year one energy produced by the PV system",
                  "units": "kWh"
                },
                "year_one_energy_produced_bau_kwh": {
                  "type": "float",
                  "description": "Year one energy produced by the PV system in the BAU case",
                  "units": "kWh"
                },
                "year_one_power_production_series_kw": {
                  "type": "list_of_float",
                  "description": "Year one PV power production time series",
                  "units": "kW"
                },
                "year_one_to_battery_series_kw": {
                  "type": "list_of_float",
                  "description": "Year one hourly time series of PV charging",
                  "units": "kW"
                },
                "year_one_to_load_series_kw": {
                  "type": "list_of_float",
                  "description": "Year one hourly time series of PV serving load",
                  "units": "kW"
                },
                "year_one_to_grid_series_kw": {
                  "type": "list_of_float",
                  "description": "Year one hourly time series of PV exporting to grid",
                  "units": "kW"
                },
                "existing_pv_om_cost_us_dollars": {
                  "type": "float",
                  "description": "Lifetime O&M cost for existing PV system.",
                  "units": "$"
                },
                "station_latitude": {
                  "type": "float",
                  "description": "The latitude of the station used for weather resource data",
                  "units": "degrees"
                },
                "station_longitude": {
                  "type": "float",
                  "description": "The longitude of the station used for weather resource data",
                  "units": "degrees"
                },
                "station_distance_km": {
                  "type": "float",
                  "description": "The distance from the weather resource station from the input site",
                  "units": "km"
                },
                "year_one_curtailed_production_series_kw": {
                  "type": "list_of_float",
                  "description": "Year one PV power curtailed during outage time series",
                  "units": "kW"
                },
              },

              "Wind": {
                "size_kw": {
                  "type": "float",
                  "description": "Recommended wind system size",
                  "units": "kW"
                },
                "average_yearly_energy_produced_kwh": {
                  "type": "float",
                  "description": "Average energy produced by the wind system over one year",
                  "units": "kWh"
                },
                "average_yearly_energy_exported_kwh": {
                  "type": "float",
                  "description": "Average annual energy exported by the wind system",
                  "units": "kWh"
                },
                "year_one_energy_produced_kwh": {
                  "type": "float",
                  "description": "Wind energy produced in year one",
                  "units": "kWh"
                },
                "year_one_power_production_series_kw": {
                  "type": "list_of_float",
                  "description": "Hourly wind resource",
                  "units": "kW"
                },
                "year_one_to_battery_series_kw": {
                  "type": "list_of_float",
                  "description": "Year one wind to battery time series",
                  "units": "kW"
                },
                "year_one_to_load_series_kw": {
                  "type": "list_of_float",
                  "description": "Year one wind to load time series",
                  "units": "kW"
                },
                "year_one_to_grid_series_kw": {
                  "type": "list_of_float",
                  "description": "Year one wind to grid time series",
                  "units": "kW"
                },
                "year_one_curtailed_production_series_kw": {
                  "type": "list_of_float",
                  "description": "Year one Wind power curtailed during outage time series",
                  "units": "kW"
                },
              },

              "Storage": {
                "size_kw": {
                  "type": "float",
                  "description": "Optimal battery power capacity",
                  "units": "kW"
                },
                "size_kwh": {
                  "type": "float",
                  "description": "Optimal battery energy capacity",
                  "units": "kWh"
                },
                "year_one_to_load_series_kw": {
                  "type": "list_of_float",
                  "description": "Year one hourly time series of battery serving load",
                  "units": "kW"
                },
                "year_one_to_grid_series_kw": {
                  "type": "list_of_float",
                  "description": "Year one hourly time series of battery exporting to grid",
                  "units": "kW"
                },
                "year_one_soc_series_pct": {
                  "type": "list_of_float",
                  "description": "Year one hourly time series of battery state of charge",
                  "units": "%"
                }
              },

              "ElectricTariff": {
                "year_one_energy_cost_us_dollars": {
                  "type": "float",
                  "description": "Optimal year one utility energy cost",
                  "units": "$"
                },
                "year_one_demand_cost_us_dollars": {
                  "type": "float",
                  "description": "Optimal year one utility demand cost",
                  "units": "$"
                },
                "year_one_fixed_cost_us_dollars": {
                  "type": "float",
                  "description": "Optimal year one utility fixed cost",
                  "units": "$"
                },
                "year_one_min_charge_adder_us_dollars": {
                  "type": "float",
                  "description": "Optimal year one utility minimum charge adder",
                  "units": "$"
                },
                "year_one_energy_cost_bau_us_dollars": {
                  "type": "float",
                  "description": "Business as usual year one utility energy cost",
                  "units": "$"
                },
                "year_one_demand_cost_bau_us_dollars": {
                  "type": "float",
                  "description": "Business as usual year one utility demand cost",
                  "units": "$"
                },
                "year_one_fixed_cost_bau_us_dollars": {
                  "type": "float",
                  "description": "Business as usual year one utility fixed cost",
                  "units": "$"
                },
                "year_one_min_charge_adder_bau_us_dollars": {
                  "type": "float",
                  "description": "Business as usual year one utility minimum charge adder",
                  "units": "$"
                },
                "total_energy_cost_us_dollars": {
                  "type": "float",
                  "description": "Total utility energy cost over the lifecycle, after-tax",
                  "units": "$"
                },
                "total_demand_cost_us_dollars": {
                  "type": "float",
                  "description": "Optimal total lifecycle utility demand cost over the analysis period, after-tax",
                  "units": "$"
                },
                "total_fixed_cost_us_dollars": {
                  "type": "float",
                  "description": "Total utility fixed cost over the lifecycle, after-tax",
                  "units": "$"
                },
                "total_min_charge_adder_us_dollars": {
                  "type": "float",
                  "description": "Total utility minimum charge adder",
                  "units": "$"
                },
                "total_energy_cost_bau_us_dollars": {
                  "type": "float",
                  "description": "Business as usual total utility energy cost over the lifecycle, after-tax",
                  "units": "$"
                },
                "total_demand_cost_bau_us_dollars": {
                  "type": "float",
                  "description": "Business as usual total lifecycle utility demand cost over the analysis period, after-tax",
                  "units": "$"
                },
                "total_fixed_cost_bau_us_dollars": {
                  "type": "float",
                  "description": "Business as usual total utility fixed cost over the lifecycle, after-tax",
                  "units": "$"
                },
                "total_export_benefit_us_dollars": {
                  "type": "float",
                  "description": "Total export benefit cost over the lifecycle, after-tax",
                  "units": "$"
                },
                "total_export_benefit_bau_us_dollars": {
                  "type": "float",
                  "description": "BAU export benefit cost over the lifecycle, after-tax",
                  "units": "$"
                },
                "total_min_charge_adder_bau_us_dollars": {
                  "type": "float",
                  "description": "Business as usual total utility minimum charge adder",
                  "units": "$"
                },
                "year_one_bill_us_dollars": {
                  "type": "float",
                  "description": "Optimal year one total utility bill",
                  "units": "$"
                },
                "year_one_bill_bau_us_dollars": {
                  "type": "float",
                  "description": "Business as usual year one total utility bill",
                  "units": "$"
                },
                "year_one_export_benefit_us_dollars": {
                  "type": "float",
                  "description": "Optimal year one value of exported energy",
                  "units": "$"
                },
                "year_one_export_benefit_bau_us_dollars": {
                  "type": "float",
                  "description": "BAU year one value of exported energy",
                  "units": "$"
                },
                "year_one_energy_cost_series_us_dollars_per_kwh": {
                  "type": "list_of_float",
                  "description": "Year one hourly energy costs",
                  "units": "$/kWh"
                },
                "year_one_demand_cost_series_us_dollars_per_kw": {
                  "type": "list_of_float",
                  "description": "Year one hourly demand costs",
                  "units": "$/kW"
                },
                "year_one_to_load_series_kw": {
                  "type": "list_of_float",
                  "description": "Year one grid to load time series",
                  "units": "kW"
                },
                "year_one_to_load_series_bau_kw": {
                  "type": "list_of_float",
                  "description": "Year one grid to load time series in the BAU case",
                  "units": "kW"
                },
                "year_one_to_battery_series_kw": {
                  "type": "list_of_float",
                  "description": "Year one hourly time series of power from grid to battery",
                  "units": "kW"
                },
                "year_one_energy_supplied_kwh": {
                  "type": "float",
                  "description": "Year one energy supplied from grid to load",
                  "units": "kWh"
                },
                "year_one_energy_supplied_kwh_bau": {
                  "type": "float",
                  "description": "Year one energy supplied from grid to load in the business-as-usual scenario",
                  "units": "kWh"
                },
                "year_one_emissions_lb_C02": {
                  "type": "int",
                  "description": ("Total equivalent pounds of carbon dioxide emitted from utility electricity use "
                                  "in the first year. Calculated from EPA AVERT region hourly grid emissions factor series for the continental US."
                                  "In AK and HI, the best available data are EPA eGRID annual averages."),
                  "units": "lb CO2"
                },
                "year_one_emissions_bau_lb_C02": {
                  "type": "int",
                  "description": "Total equivalent pounds of carbon dioxide emitted from BAU utility electricity use in the first year. Calculated by default from hourly emissions estimates except in AK and HI.",
                  "units": "lb CO2"
                },
                "year_one_coincident_peak_cost_us_dollars": {
                  "type": "float",
                  "description": "Optimal year one coincident peak charges",
                  "units": "$"
                },
                "year_one_coincident_peak_cost_bau_us_dollars": {
                  "type": "float",
                  "description": "Business as usual year one coincident peak charges",
                  "units": "$"
                },
                "total_coincident_peak_cost_us_dollars": {
                  "type": "float",
                  "description": "Optimal lifecycle coincident peak charges",
                  "units": "$"
                },
                "total_coincident_peak_cost_bau_us_dollars": {
                  "type": "float",
                  "description": "Business as usual lifecycle coincident peak charges",
                },
                "year_one_chp_standby_cost_us_dollars": {
                  "type": float,
                  "description": "Year 1 standby charge cost incurred by CHP",
                  "units": "$"
                },
                "total_chp_standby_cost_us_dollars": {
                  "type": float,
                  "description": "Total lifecycle standby charge cost incurred by CHP",
                  "units": "$"
                },
                "emissions_region": {
                  "type": "str",
                  "description": "Description of region for emissions_factor_series_lb_CO2_per_kwh. Filled by default with the EPA AVERT region of the site."
                },
              },

              "FuelTariff": {
                "total_boiler_fuel_cost_us_dollars": {
                  "type": float,
                  "description": "Total boiler fuel cost over the lifecycle, after-tax",
                  "units": "$"
                },
                "year_one_boiler_fuel_cost_us_dollars": {
                  "type": float,
                  "description": "Year one boiler fuel cost, before-tax",
                  "units": "$"
                },
                "year_one_boiler_fuel_cost_bau_us_dollars": {
                  "type": float,
                  "description": "Year one bau boiler fuel cost, before-tax",
                  "units": "$"
                },
                "total_chp_fuel_cost_us_dollars": {
                  "type": float,
                  "description": "Total chp fuel cost over the lifecycle, after-tax",
                  "units": "$"
                },
                "year_one_chp_fuel_cost_us_dollars": {
                  "type": float,
                  "description": "Year one chp fuel cost, before-tax",
                  "units": "$"
                },
                "total_boiler_fuel_cost_bau_us_dollars": {
                  "type": float,
                  "description": "Business as usual total boiler fuel cost over the lifecycle, after-tax",
                  "units": "$"
                }
              },

              "Generator": {
                "size_kw": {
                  "type": "float",
                  "description": "Optimal diesel generator system size",
                  "units": "kW"
                },
                "fuel_used_gal": {
                  "type": "float",
                  "description": "Generator fuel used to meet critical load during grid outage.",
                  "units": "US gallons"
                },
                "fuel_used_gal_bau": {
                  "type": "float",
                  "description": "Generator fuel used to meet critical load during grid outage in bau case.",
                  "units": "US gallons"
                },
                "average_yearly_energy_produced_kwh": {
                  "type": "float",
                  "description": "Average annual energy produced by the diesel generator over one year",
                  "units": "kWh"
                },
                "average_yearly_energy_exported_kwh": {
                  "type": "float",
                  "description": "Average annual energy exported by the diesel generator",
                  "units": "kWh"
                },
                "year_one_energy_produced_kwh": {
                  "type": "float",
                  "description": "Year one energy produced by the diesel generator",
                  "units": "kWh"
                },
                "year_one_power_production_series_kw": {
                  "type": "list_of_float",
                  "description": "Year one diesel generator power production time series",
                  "units": "kW"
                },
                "year_one_to_battery_series_kw": {
                  "type": "list_of_float",
                  "description": "Year one hourly time series of diesel generator charging",
                  "units": "kW"
                },
                "year_one_to_load_series_kw": {
                  "type": "list_of_float",
                  "description": "Year one generator to load time series.",
                  "units": "kW"
                },
                "year_one_to_grid_series_kw": {
                  "type": "list_of_float",
                  "description": "Year one hourly time series of diesel generator exporting to grid",
                  "units": "kW"
                },
                "existing_gen_total_fixed_om_cost_us_dollars": {
                  "type": "float",
                  "description": "Lifetime fixed O&M cost for existing diesel generator system in bau case.",
                  "units": "$"
                },
                "existing_gen_total_variable_om_cost_us_dollars": {
                  "type": "float",
                  "description": "Lifetime variable (based on kwh produced) O&M cost for existing diesel generator system.",
                  "units": "$"
                },
                "existing_gen_year_one_variable_om_cost_us_dollars": {
                  "type": "float",
                  "description": "Year one variable (based on kwh produced) O&M cost for existing diesel generator system.",
                  "units": "$"
                },
                "total_fixed_om_cost_us_dollars": {
                  "type": "float",
                  "description": "Total lifecycle fixed (based on kW capacity) O&M cost for existing + recommended diesel generator system.",
                  "units": "$"
                },
                "total_variable_om_cost_us_dollars": {
                  "type": "float",
                  "description": "Total lifecycle variable (based on kWh produced) O&M cost for existing + recommended diesel generator system",
                  "units": "$"
                },
                "year_one_variable_om_cost_us_dollars": {
                  "type": "float",
                  "description": "Year one variable (based on kwh produced) O&M cost for existing + recommended diesel generator system",
                  "units": "$"
                },
                "year_one_fixed_om_cost_us_dollars": {
                  "type": "float",
                  "description": "Year one fixed (based on kW capacity) O&M cost for existing + recommended diesel generator system.",
                  "units": "$"
                },
                "total_fuel_cost_us_dollars": {
                  "type": "float",
                  "description": "Total lifecycle fuel cost for existing + newly recommended diesel generator system",
                  "units": "$"
                },
                "year_one_fuel_cost_us_dollars": {
                  "type": "float",
                  "description": "Year one fuel cost for existing + newly recommended diesel generator system",
                  "units": "$"
                },
                "existing_gen_total_fuel_cost_us_dollars": {
                  "type": "float",
                  "description": "Total lifecycle fuel cost for existing diesel generator system",
                  "units": "$"
                },
                "existing_gen_year_one_fuel_cost_us_dollars": {
                  "type": "float",
                  "description": "Year one fuel cost for existing diesel generator system",
                  "units": "$"
                },
                "year_one_emissions_lb_C02": {
                  "type": "int",
                  "description": "Total equivalent pounds of carbon dioxide emitted from generator use in the first year.",
                  "units": "lb CO2"
                },
                "year_one_emissions_bau_lb_C02": {
                  "type": "int",
                  "description": "Total equivalent pounds of carbon dioxide emitted from BAU generator use in the first year.",
                  "units": "lb CO2"
                }
              },

              "CHP": {
                "size_kw": {
                  "type": float,
                  "description": "Optimal CHP prime-mover rated electric size",
                  "units": "kW"
                },
                "year_one_fuel_used_mmbtu": {
                  "type": float,
                  "description": "CHP fuel used over one year",
                  "units": "MMBtu"
                },
                "year_one_electric_energy_produced_kwh": {
                  "type": float,
                  "description": "Year one electric energy produced by CHP",
                  "units": "kWh"
                },
                "year_one_thermal_energy_produced_mmbtu": {
                  "type": float,
                  "description": "Year one thermal energy produced by CHP",
                  "units": "MMBtu/hr"
                },
                "year_one_electric_production_series_kw": {
                  "type": list_of_float,
                  "description": "Year one CHP electric production time series",
                  "units": "kW"
                },
                "year_one_to_battery_series_kw": {
                  "type": list_of_float,
                  "description": "Year one hourly time series of CHP charging battery",
                  "units": "kW"
                },
                "year_one_to_load_series_kw": {
                  "type": list_of_float,
                  "description": "Year one CHP to electric load time series.",
                  "units": "kW"
                },
                "year_one_to_grid_series_kw": {
                  "type": list_of_float,
                  "description": "Year one hourly time series of CHP exporting to grid",
                  "units": "kW"
                },
                "year_one_thermal_to_load_series_mmbtu_per_hour": {
                  "type": list_of_float,
                  "description": "Year one hourly time series of CHP thermal to hot thermal load",
                  "units": "MMBtu/hr"
                },
                "year_one_thermal_to_tes_series_mmbtu_per_hour": {
                  "type": list_of_float,
                  "description": "Year one hourly time series of CHP thermal to Hot TES",
                  "units": "MMBtu/hr"
                },
                "year_one_thermal_to_waste_series_mmbtu_per_hour": {
                  "type": list_of_float,
                  "description": "Year one hourly time series of CHP thermal to waste heat",
                  "units": "MMBtu/hr"
                },
                "year_one_emissions_lb_C02": {
                  "type": int,
                  "description": "Total equivalent pounds of carbon dioxide emitted from CHP fuels consumed on site use in the first year.",
                  "units": "hours"
                },
                "year_one_emissions_bau_lb_C02": {
                  "type": int,
                  "description": "Total equivalent pounds of carbon dioxide emitted from CHP fuels consumed on site use in the first year in the BAU case.",
                  "units": "hours"
                },
              },

              "Boiler": {
                "year_one_boiler_fuel_consumption_series_mmbtu_per_hr": {
                  "type": list_of_float,
                  "description": "Year one hourly time series of boiler fuel consumption",
                  "units": "MMBtu/hr"
                },
                "year_one_boiler_thermal_production_series_mmbtu_per_hr": {
                  "type": list_of_float,
                  "description": "Year one hourly time series of boiler thermal production",
                  "units": "MMBtu/hr"
                },
                "year_one_boiler_fuel_consumption_mmbtu": {
                  "type": float,
                  "description": "Annual average boiler fuel consumption",
                  "units": "MMBtu"
                },
                "year_one_boiler_thermal_production_mmbtu": {
                  "type": float,
                  "description": "Annual average boiler thermal production",
                  "units": "MMBtu"
                },
                "year_one_thermal_to_load_series_mmbtu_per_hour": {
                  "type": list_of_float,
                  "description": "Year one hourly time series of CHP thermal to hot thermal load",
                  "units": "MMBtu/hr"
                },
                "year_one_thermal_to_tes_series_mmbtu_per_hour": {
                  "type": list_of_float,
                  "description": "Year one hourly time series of CHP thermal to Hot TES",
                  "units": "MMBtu/hr"
                },
                "year_one_emissions_lb_C02": {
                  "type": int,
                  "description": "Total equivalent pounds of carbon dioxide emitted from boiler fuels consumed on site use in the first year.",
                  "units": "hours"
                },
                "year_one_emissions_bau_lb_C02": {
                  "type": int,
                  "description": "Total equivalent pounds of carbon dioxide emitted from boiler fuels consumed on site use in the first year in the BAU case.",
                  "units": "hours"
                }
              },

              "ElectricChiller": {
                "year_one_electric_chiller_thermal_to_load_series_ton": {
                  "type": list_of_float,
                  "description": "Year one hourly time series of electric chiller thermal to cooling load",
                  "units": "Ton"
                },
                "year_one_electric_chiller_thermal_to_tes_series_ton": {
                  "type": list_of_float,
                  "description": "Year one hourly time series of electric chiller thermal to cold TES",
                  "units": "Ton"
                },
                "year_one_electric_chiller_electric_consumption_series_kw": {
                  "type": list_of_float,
                  "description": "Year one hourly time series of chiller electric consumption",
                  "units": "kW"
                },
                "year_one_electric_chiller_electric_consumption_kwh": {
                  "type": float,
                  "description": "Year one chiller electric consumption",
                  "units": "kWh"
                },
                "year_one_electric_chiller_thermal_production_tonhr": {
                  "type": float,
                  "description": "Year one chiller thermal production",
                  "units": "TonHr"
                }
              },

              "AbsorptionChiller": {
                "size_ton": {
                  "type": float,
                  "description": "Optimal absorption chiller rated cooling power size",
                  "units": "Ton"
                },
                "year_one_absorp_chl_thermal_to_load_series_ton": {
                  "type": list_of_float,
                  "description": "Year one hourly time series of absorption chiller thermal production",
                  "units": "Ton"
                },
                "year_one_absorp_chl_thermal_to_tes_series_ton": {
                  "type": list_of_float,
                  "description": "Year one hourly time series of absorption chiller thermal production",
                  "units": "Ton"
                },
                "year_one_absorp_chl_thermal_consumption_series_mmbtu_per_hr": {
                  "type": list_of_float,
                  "description": "Year one hourly time series of absorption chiller thermal consumption",
                  "units": "MMBtu/hr"
                },
                "year_one_absorp_chl_thermal_consumption_mmbtu": {
                  "type": float,
                  "description": "Year one chiller thermal consumption",
                  "units": "MMBtu"
                },
                "year_one_absorp_chl_thermal_production_tonhr": {
                  "type": float,
                  "description": "Year one chiller thermal production",
                  "units": "TonHr"
                },
                "year_one_absorp_chl_electric_consumption_series_kw": {
                  "type": list_of_float,
                  "description": "Year one hourly time series of absorption chiller electric consumption",
                  "units": "kW"
                },
                "year_one_absorp_chl_electric_consumption_kwh": {
                  "type": float,
                  "description": "Year one chiller electric consumption (cooling tower heat rejection fans/pumps)",
                  "units": "kWh"
                }
              },

              "ColdTES": {
                "size_gal": {
                  "type": float,
                  "description": "Optimal cold TES power capacity",
                  "units": "Ton"
                },
                "year_one_thermal_from_cold_tes_series_ton": {
                  "type": list_of_float,
                  "description": "Year one hourly time series of TES serving cooling thermal load",
                  "units": "Ton"
                },
                "year_one_cold_tes_soc_series_pct": {
                  "type": list_of_float,
                  "description": "Year one hourly time series of cold TES state of charge",
                  "units": "%"
                }
              },

              "HotTES": {
                "size_gal": {
                  "type": float,
                  "description": "Optimal hot TES power capacity",
                  "units": "MMBtu/hr"
                },
                "year_one_thermal_from_hot_tes_series_mmbtu_per_hr": {
                  "type": list_of_float,
                  "description": "Year one hourly time series of TES serving hot thermal load",
                  "units": "MMBtu/hr"
                },
                "year_one_hot_tes_soc_series_pct": {
                  "type": list_of_float,
                  "description": "Year one hourly time series of hot TES state of charge",
                  "units": "%"
                }
              },
              "RC": {
                "temperatures_degree_C": {
                  "type": list_of_float,
                  "description": "Hourly time series of indoor temperature",
                  "units": "Celsius"
                },
                "comfort_penalty_degC": {
                  "type": list_of_float,
                  "description": "HVAC comfort penalty",
                  "units": "degrees"
                }
              },
              "FlexTechAC": {
                "size_kw": {
                  "type": float,
                  "description": "AC size",
                  "units": "kW"
                },
                "year_one_power_production_series_kw": {
                  "type": list_of_float,
                  "description": "Year one AC power production time series",
                  "units": "kW"
                },
                "year_one_power_consumption_series_kw": {
                  "type": list_of_float,
                  "description": "Year one AC power consumption time series",
                  "units": "kW"
                }
              },
              "FlexTechHP": {
                "size_kw": {
                  "type": float,
                  "description": "HP size",
                  "units": "kW"
                },
                "year_one_power_production_series_kw": {
                  "type": list_of_float,
                  "description": "Year one HP power production time series",
                  "units": "kW"
                },
                "year_one_power_consumption_series_kw": {
                  "type": list_of_float,
                  "description": "Year one HP power consumption time series",
                  "units": "kW"
                }
              },
              "HotWaterTank": {
                "year_one_temperature_series_degC": {
                  "type": list_of_float,
                  "description": "Hot water tank temperature series",
                  "units": "Celcius"
                },
                "comfort_penalty_degC": {
                  "type": list_of_float,
                  "description": "WH comfort penalty",
                  "units": "degrees"
                }
              },
              "FlexTechERWH": {
                "year_one_power_production_series_kw": {
                  "type": list_of_float,
                  "description": "Year one ERWH power production time series",
                  "units": "kW"
                },
                "year_one_power_consumption_series_kw": {
                  "type": list_of_float,
                  "description": "Year one ERWH power consumption time series",
                  "units": "kW"
                },
                "fraction_on": {
                  "type": list_of_float,
                  "description": "Fraction of each hour the ERWH is on for",
                  "units": "-"
                }
              },
              "FlexTechHPWH": {
                "year_one_power_production_series_kw": {
                  "type": list_of_float,
                  "description": "Year one HPWH power production time series",
                  "units": "kW"
                },
                "year_one_power_consumption_series_kw": {
                  "type": list_of_float,
                  "description": "Year one HPWH power consumption time series",
                  "units": "kW"
                },
                "fraction_on": {
                  "type": list_of_float,
                  "description": "Fraction of each hour the ERWH is on for",
                  "units": "-"
                }
              }
            }
        }
      },

    "messages": {
        "warnings": {'type': "list_of_string", "description": "Warnings generated by simulation"},
        "error": {'type': "str", "description": "Error generated by simulation"}
    }
}
