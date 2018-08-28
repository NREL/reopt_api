max_big_number = 1e8
max_incentive = 1e10
max_years = 75
macrs_schedules = [0, 5, 7]
analysis_years = 20
providers = ['federal', 'state', 'utility']
default_buildings = ['FastFoodRest',
                     'FullServiceRest',
                     'Hospital',
                     'LargeHotel',
                     'LargeOffice',
                     'MediumOffice',
                     'MidriseApartment',
                     'Outpatient',
                     'PrimarySchool',
                     'RetailStore',
                     'SecondarySchool',
                     'SmallHotel',
                     'SmallOffice',
                     'StripMall',
                     'Supermarket',
                     'Warehouse',
                     'FlatLoad'
                     ]

macrs_five_year = [0.2, 0.32, 0.192, 0.1152, 0.1152, 0.0576]  # IRS pub 946
macrs_seven_year = [0.1429, 0.2449, 0.1749, 0.1249, 0.0893, 0.0892, 0.0893, 0.0446]

#the user needs to supply valid data for all the attributes in at least on of these sets for load_profile_possible_sets and electric_tariff_possible_sets
load_profile_possible_sets = [["loads_kw"],
            ["doe_reference_name", "monthly_totals_kwh"],
            ["annual_kwh", "doe_reference_name"],
            ["doe_reference_name"]
            ]

electric_tariff_possible_sets = [["urdb_response"],
            ["blended_monthly_demand_charges_us_dollars_per_kw", "blended_monthly_rates_us_dollars_per_kwh"],
            ["urdb_label"],
            ["urdb_utility_name", "urdb_rate_name"]]


def list_of_float(input):
    return [float(i) for i in input]

nested_input_definitions = {

  "Scenario": {
    "timeout_seconds": {
      "type": "float",
      "min": 1,
      "max": 295,
      "default": 295,
      "description": "The number of seconds allowed before the optimization times out"
    },
    "user_uuid": {
      "type": "str",
      "description": "The assigned unique ID of a signed in REOpt user"
    },
    "description": {
      "type": "str",
      "description": "An optional user defined description to describe the scenario and run"
    },
    "time_steps_per_hour": {
      "type": "int",
      "min": 1,
      "max": 1,
      "default": 1,
      "description": "The number of time steps per hour in the REopt simulation"
    },

    "Site": {
      "latitude": {
        "type": "float",
        "min": -90,
        "max": 90,
        "required": True,
        "description": "The approximate latitude of the site in decimal degrees"
      },
      "longitude": {
        "type": "float",
        "min": -180,
        "max": 180,
        "required": True,
        "description": "The approximate longitude of the site in decimal degrees"
      },
      "address": {
        "type": "str",
        "description": "A user defined address as optional metadata (street address, city, state or zip code)"
      },
      "land_acres": {
        "type": "float",
        "min": 0,
        "max": 1e6,
        "description": "Land area in acres available for PV panel siting"
      },
      "roof_squarefeet": {
        "type": "float",
        "min": 0,
        "max": 1e9,
        "description": "Area of roof in square feet available for PV siting"
      },

      "Financial": {
        "om_cost_escalation_pct": {
          "type": "float",
          "min": -1,
          "max": 1,
          "default": 0.025,
          "description": "Annual nominal O&M cost escalation rate"
        },
        "escalation_pct": {
          "type": "float",
          "min": -1,
          "max": 1,
          "default": 0.026,
          "description": "Annual nominal utility electricity cost escalation rate"
        },
        "offtaker_tax_pct": {
          "type": "float",
          "min": 0,
          "max": 1,
          "default": 0.4,
          "description": "Host tax rate"
        },
        "offtaker_discount_pct": {
          "type": "float",
          "min": 0,
          "max": 1,
          "default": 0.081,
          "description": "Nominal host discount rate"
        },
        "analysis_years": {
          "type": "int",
          "min": 1,
          "max": max_years,
          "default": analysis_years,
          "description": "Analysis period"
        },
        "value_of_lost_load_us_dollars_per_kwh": {
          "type": "float",
          "min": 0,
          "max": 1e6,
          "default": 100,
          "description": "Value placed on unmet site load during grid outages. Units are US dollars per unmet kilowatt-hour. The value of lost load (VoLL) is used to determine the avoided outage costs by multiplying VoLL [$/kWh] with the average number of hours that the critical load can be met by the energy system (determined by simulating outages occuring at every hour of the year), and multiplying by the mean critical load."
        },
        "microgrid_upgrade_cost_pct": {
          "type": "float",
          "min": 0,
          "max": 1,
          "default": 0.3,
          "description": "Additional cost, in percent of non-islandable capital costs, to make a distributed energy system islandable from the grid and able to serve critical loads. Includes all upgrade costs such as additional laber and critical load panels."
        }
      },

      "LoadProfile": {
        "doe_reference_name": {
          "type": "str",
          "restrict_to": default_buildings,
          "replacement_sets": load_profile_possible_sets,
          "description": "Simulated load profile from DOE <a href='https: //energy.gov/eere/buildings/commercial-reference-buildings' target='blank'>Commercial Reference Buildings</a>"
        },
        "annual_kwh": {
          "type": "float",
          "min": 1,
          "max": 1e12,
          "replacement_sets": load_profile_possible_sets,
          "depends_on": ["doe_reference_name"],
          "description": "Annual energy consumption used to scale simulated building load profile, if <b><small>monthly_totals_kwh</b></small> is not provided."
        },
        "year": {
          "type": "int",
          "min": 1,
          "max": 9999,
          "default": 2018,
          "description": "Year of Custom Load Profile. If a custom load profile is uploaded via the loads_kw parameter, it is important that this year correlates with the load profile so that weekdays/weekends are determined correctly for the utility rate tariff. If a DOE Reference Building profile (aka 'simulated' profile) is used, the year is set to 2017 since the DOE profiles start on a Sunday."
        },
        "monthly_totals_kwh": {
          "type": "list_of_float",
          "replacement_sets": load_profile_possible_sets,
          "depends_on": ["doe_reference_name"],
          "description": "Array (length of 12) of total monthly energy consumption used to scale simulated building load profile."
        },
        "loads_kw": {
          "type": "list_of_float",
          "replacement_sets": load_profile_possible_sets,
          "description": "Typical load over all hours in one year. Must be hourly (8,760 samples), 30 minute (17,520 samples), or 15 minute (35,040 samples)."
        },
        "critical_loads_kw": {
          "type": "list_of_float",
          "description": "Critical load during an outage period. Must be hourly (8,760 samples), 30 minute (17,520 samples), or 15 minute (35,040 samples)."
        },
        "loads_kw_is_net": {
          "default": True,
          "type": "bool",
          "description": "If there is existing PV, must specify whether provided load is the net load after existing PV or not."
        },
        "critical_loads_kw_is_net": {
          "default": False,
          "type": "bool",
          "description": "If there is existing PV, must specify whether provided load is the net load after existing PV or not."
        },
        "outage_start_hour": {
          "type": "int",
          "min": 0,
          "max": 8759,
          "description": "Hour of year that grid outage starts. Must be less than outage_end."
        },
        "outage_end_hour": {
          "type": "int",
          "min": 0,
          "max": 8759,
          "description": "Hour of year that grid outage ends. Must be greater than outage_start."
        },
        "critical_load_pct": {
          "type": "float",
          "min": 0,
          "max": 1,
          "default": 0.5,
          "description": "Critical load factor is multiplied by the typical load to determine the critical load that must be met during an outage. Value must be between zero and one, inclusive."
        },
        "outage_is_major_event": {
          "type": "bool",
          "default": True,
          "description": "Boolean value for if outage is a major event, which affects the avoided_outage_costs_us_dollars. If True, the avoided outage costs are calculated for a single outage occurring in the first year of the analysis_years. If False, the outage event is assumed to be an average outage event that occurs every year of the analysis period. In the latter case, the avoided outage costs for one year are escalated and discounted using the escalation_pct and offtaker_discount_pct to account for an annually recurring outage. (Average outage durations for certain utility service areas can be estimated using statistics reported on EIA form 861.)"
        }
      },

      "ElectricTariff": {
        "urdb_utility_name": {
          "type": "str",
          "replacement_sets": electric_tariff_possible_sets,
          "depends_on": ["urdb_rate_name"],
          "description": "Name of Utility from  <a href='https: //openei.org/wiki/Utility_Rate_Database' target='blank'>Utility Rate Database</a>"
        },
        "urdb_rate_name": {
          "type": "str",
          "replacement_sets": electric_tariff_possible_sets,
          "depends_on": ["urdb_utility_name"],
          "description": "Name of utility rate from  <a href='https: //openei.org/wiki/Utility_Rate_Database' target='blank'>Utility Rate Database</a>"
        },
        "blended_monthly_rates_us_dollars_per_kwh": {
          "type": "list_of_float",
          "replacement_sets": electric_tariff_possible_sets,
          "depends_on": ["blended_monthly_demand_charges_us_dollars_per_kw"],
          "description": "Array (length of 12) of blended energy rates (total monthly energy in kWh divided by monthly cost in $)"
        },
        "blended_monthly_demand_charges_us_dollars_per_kw": {
          "type": "list_of_float",
          "replacement_sets": electric_tariff_possible_sets,
          "depends_on": ["blended_monthly_rates_us_dollars_per_kwh"],
          "description": "Array (length of 12) of blended demand charges (demand charge cost in $ divided by monthly peak demand in kW)"
        },
        "net_metering_limit_kw": {
          "type": "float",
          "min": 0,
          "max": 1e9,
          "default": 0,
          "description": "System size above which net metering is not allowed"
        },
        "interconnection_limit_kw": {
          "type": "float",
          "min": 0,
          "max": 1e9,
          "default": max_big_number,
          "description": "Limit on system capacity size that can be interconnected to the grid"
        },
        "wholesale_rate_us_dollars_per_kwh": {
          "type": "float",
          "min": 0,
          "default": 0,
          "description": "Price of electricity sold back to the grid in absence of net metering"
        },
        "urdb_response": {
          "type": "dict",
          "replacement_sets": electric_tariff_possible_sets,
          "description": "Utility rate structure from <a href='https: //openei.org/services/doc/rest/util_rates/?version=3' target='blank'>Utility Rate Database API</a>"
        },
        "urdb_label": {
          "type": "str",
          "replacement_sets": electric_tariff_possible_sets,
          "description": "Label attribute of utility rate structure from <a href='https: //openei.org/services/doc/rest/util_rates/?version=3' target='blank'>Utility Rate Database API</a>"
        }
      },

      "Wind": {
        "size_class": {
          "type": "str",
          "restrict_to": "['residential', 'commercial', 'medium', 'large']",
          "description": "Turbine size-class. One of [residential, commercial, medium, large]"
        },
        "wind_meters_per_sec": {
          "type": "list_of_float",
          "description": "Data downloaded from Wind ToolKit for modeling wind turbine."
        },
        "wind_direction_degrees": {
          "type": "list_of_float",
          "description": "Data downloaded from Wind ToolKit for modeling wind turbine."
        },
        "temperature_celsius": {
          "type": "list_of_float",
          "description": "Data downloaded from Wind ToolKit for modeling wind turbine."
        },
        "pressure_atmospheres": {
          "type": "list_of_float",
          "description": "Data downloaded from Wind ToolKit for modeling wind turbine."
        },
        "min_kw": {
          "type": "float",
          "min": 0,
          "max": 1e9,
          "default": 0,
          "description": "Minimum wind power capacity constraint for optimization"
        },
        "max_kw": {
          "type": "float",
          "min": 0,
          "max": 1e9,
          "default": 0,
          "description": "Maximum wind power capacity constraint for optimization. Set to zero to disable Wind. Disabled by default"
        },
        "installed_cost_us_dollars_per_kw": {
          "type": "float",
          "min": 0,
          "max": 1e5,
          "default": 1874,
          "description": "Total upfront installed costs in US dollars/kW. Determined by size_class. For the 'large' (>1MW) size_class the cost is $1,874/kW. For the 'medium' size_class the cost is $4,111/kW and for the 'commercial' size_class the cost is $4,989/kW."
        },
        "om_cost_us_dollars_per_kw": {
          "type": "float",
          "min": 0,
          "max": 1e3,
          "default": 35,
          "description": "Total annual operations and maintenance costs"
        },
        "macrs_option_years": {
          "type": "int",
          "restrict_to": macrs_schedules,
          "default": 5,
          "description": "MACRS schedule for financial analysis. Set to zero to disable"
        },
        "macrs_bonus_pct": {
          "type": "float",
          "min": 0,
          "max": 1,
          "default": 0.4,
          "description": "Percent of upfront project costs to depreciate under MACRS"
        },
        "macrs_itc_reduction": {
          "type": "float",
          "min": 0,
          "max": 1,
          "default": 0.5,
          "description": "Percent of the full ITC that depreciable basis is reduced by"
        },
        "federal_itc_pct": {
          "type": "float",
          "min": 0,
          "max": 1,
          "default": 0.3,
          "description": "Percent federal capital cost incentive"
        },
        "state_ibi_pct": {
          "type": "float",
          "min": 0,
          "max": 1,
          "default": 0,
          "description": "Percent of upfront project costs to discount under state investment based incentives"
        },
        "state_ibi_max_us_dollars": {
          "type": "float",
          "min": 0,
          "max": 1e10,
          "default": max_incentive,
          "description": "Maximum rebate allowed under state investment based incentives"
        },
        "utility_ibi_pct": {
          "type": "float",
          "min": 0,
          "max": 1,
          "default": 0,
          "description": "Percent of upfront project costs to discount under utility investment based incentives"
        },
        "utility_ibi_max_us_dollars": {
          "type": "float",
          "min": 0,
          "max": 1e10,
          "default": max_incentive,
          "description": "Maximum rebate allowed under utility investment based incentives"
        },
        "federal_rebate_us_dollars_per_kw": {
          "type": "float",
          "min": 0,
          "max": 1e9,
          "default": 0,
          "description": "Federal rebate based on installed capacity"
        },
        "state_rebate_us_dollars_per_kw": {
          "type": "float",
          "min": 0,
          "max": 1e9,
          "default": 0,
          "description": "State rebates based on installed capacity"
        },
        "state_rebate_max_us_dollars": {
          "type": "float",
          "min": 0,
          "max": 1e10,
          "default": max_incentive,
          "description": "Maximum rebate allowed under state rebates"
        },
        "utility_rebate_us_dollars_per_kw": {
          "type": "float",
          "min": 0,
          "max": 1e9,
          "default": 0,
          "description": "Utility rebates based on installed capacity"
        },
        "utility_rebate_max_us_dollars": {
          "type": "float",
          "min": 0,
          "max": 1e10,
          "default": max_incentive,
          "description": "Maximum rebate allowed under utility rebates"
        },
        "pbi_us_dollars_per_kwh": {
          "type": "float",
          "min": 0,
          "max": 1e9,
          "default": 0,
          "description": "Production-based incentive value"
        },
        "pbi_max_us_dollars": {
          "type": "float",
          "min": 0,
          "max": 1e9,
          "default": 1e9,
          "description": "Maximum rebate allowed under utility production-based incentives"
        },
        "pbi_years": {
          "type": "float",
          "min": 0,
          "max": 1e9,
          "default": 1,
          "description": "Duration of production-based incentives from installation date"
        },
        "pbi_system_max_kw": {
          "type": "float",
          "min": 0,
          "max": 1e9,
          "default": 1e9,
          "description": "Maximum system size for which production-based incentives apply"
        }
      },

      "PV": {
        "existing_kw": {
          "type": "float",
          "min": 0,
          "max": 1e5,
          "default": 0,
          "description": "Existing PV size"
        },
        "min_kw": {
          "type": "float",
          "min": 0,
          "max": 1e9,
          "default": 0,
          "description": "Minimum PV size constraint for optimization"
        },
        "max_kw": {
          "type": "float",
          "min": 0,
          "max": 1e9,
          "default": 1e9,
          "description": "Maximum PV size constraint for optimization. Set to zero to disable PV"
        },
        "installed_cost_us_dollars_per_kw": {
          "type": "float",
          "min": 0,
          "max": 1e5,
          "default": 2000,
          "description": "Installed PV cost in $/kW"
        },
        "om_cost_us_dollars_per_kw": {
          "type": "float",
          "min": 0,
          "max": 1e3,
          "default": 16,
          "description": "Annual PV operations and maintenance costs in $/kW"
        },
        "macrs_option_years": {
          "type": "int",
          "restrict_to": macrs_schedules,
          "default": 5,
          "description": "Duration over which accelerated depreciation will occur. Set to zero to disable"
        },
        "macrs_bonus_pct": {
          "type": "float",
          "min": 0,
          "max": 1,
          "default": 0.4,
          "description": "Percent of upfront project costs to depreciate in year one in addition to scheduled depreciation"
        },
        "macrs_itc_reduction": {
          "type": "float",
          "min": 0,
          "max": 1,
          "default": 0.5,
          "description": "Percent of the ITC value by which depreciable basis is reduced"
        },
        "federal_itc_pct": {
          "type": "float",
          "min": 0,
          "max": 1,
          "default": 0.3,
          "description": "Percentage of capital costs that are credited towards federal taxes"
        },
        "state_ibi_pct": {
          "type": "float",
          "min": 0,
          "max": 1,
          "default": 0,
          "description": "Percentage of capital costs offset by state incentives"
        },
        "state_ibi_max_us_dollars": {
          "type": "float",
          "min": 0,
          "max": 1e10,
          "default": max_incentive,
          "description": "Maximum dollar value of state percentage-based capital cost incentive"
        },
        "utility_ibi_pct": {
          "type": "float",
          "min": 0,
          "max": 1,
          "default": 0,
          "description": "Percentage of capital costs offset by utility incentives"
        },
        "utility_ibi_max_us_dollars": {
          "type": "float",
          "min": 0,
          "max": 1e10,
          "default": max_incentive,
          "description": "Maximum dollar value of utility percentage-based capital cost incentive"
        },
        "federal_rebate_us_dollars_per_kw": {
          "type": "float",
          "min": 0,
          "max": 1e9,
          "default": 0,
          "description": "Federal rebates based on installed capacity"
        },
        "state_rebate_us_dollars_per_kw": {
          "type": "float",
          "min": 0,
          "max": 1e9,
          "default": 0,
          "description": "State rebate based on installed capacity"
        },
        "state_rebate_max_us_dollars": {
          "type": "float",
          "min": 0,
          "max": 1e10,
          "default": max_incentive,
          "description": "Maximum state rebate"
        },
        "utility_rebate_us_dollars_per_kw": {
          "type": "float",
          "min": 0,
          "max": 1e9,
          "default": 0,
          "description": "Utility rebate based on installed capacity"
        },
        "utility_rebate_max_us_dollars": {
          "type": "float",
          "min": 0,
          "max": 1e10,
          "default": max_incentive,
          "description": "Maximum utility rebate"
        },
        "pbi_us_dollars_per_kwh": {
          "type": "float",
          "min": 0,
          "max": 1e9,
          "default": 0,
          "description": "Production-based incentive value"
        },
        "pbi_max_us_dollars": {
          "type": "float",
          "min": 0,
          "max": 1e9,
          "default": 1e9,
          "description": "Maximum annual value of production-based incentives"
        },
        "pbi_years": {
          "type": "float",
          "min": 0,
          "max": 100,
          "default": 1,
          "description": "Duration of production-based incentives from installation date"
        },
        "pbi_system_max_kw": {
          "type": "float",
          "min": 0,
          "max": 1e9,
          "default": 1e9,
          "description": "Maximum system size eligible for production-based incentive"
        },
        "degradation_pct": {
          "type": "float",
          "min": 0,
          "max": 1,
          "default": 0.005,
          "description": "Annual rate of degradation in PV energy production"
        },
        "azimuth": {
          "type": "float",
          "min": 0,
          "max": 360,
          "default": 180,
          "description": "PV azimuth angle"
        },
        "losses": {
          "type": "float",
          "min": 0,
          "max": 0.99,
          "default": 0.14,
          "description": "PV system performance losses"
        },
        "array_type": {
          "type": "int",
          "restrict_to": [0, 1, 2, 3, 4],
          "default": 0,
          "description": "PV Watts array type (0: Ground Mount Fixed (Open Rack); 1: Rooftop, Fixed; 2: Ground Mount 1-Axis Tracking; 3 : 1-Axis Backtracking; 4: Ground Mount, 2-Axis Tracking)"
        },
        "module_type": {
          "type": "int",
          "restrict_to": [0, 1, 2],
          "default": 0,
          "description": "PV module type (0: Standard; 1: Premium; 2: Thin Film)"
        },
        "gcr": {
          "type": "float",
          "min": 0.01,
          "max": 0.99,
          "default": 0.4,
          "description": "PV ground cover ratio (photovoltaic array area : total ground area)."
        },
        "dc_ac_ratio": {
          "type": "float",
          "min": 0,
          "max": 2,
          "default": 1.1,
          "description": "PV DC-AC ratio"
        },
        "inv_eff": {
          "type": "float",
          "min": 0.9,
          "max": 0.995,
          "default": 0.96,
          "description": "PV inverter efficiency"
        },
        "radius": {
          "type": "float",
          "min": 0,
          "default": 0,
          "description": "Radius to use when searching for the closest climate data station. Use zero to use the closest station regardless of the distance"
        },
        "tilt": {
          "type": "float",
          "min": 0,
          "max": 90,
          "default": "Site latitude",
          "description": "PV system tilt"
        }
      },

      "Storage": {
          "min_kw": {
            "type": "float", "min": 0, "max": 1e9, "default": 0,
            "description": "Minimum battery power capacity size constraint for optimization"
          },
          "max_kw": {
            "type": "float", "min": 0, "max": 1e9, "default": 1000000,
            "description": "Maximum battery power capacity size constraint for optimization. Set to zero to disable storage"
          },
          "min_kwh": {
            "type": "float", "min": 0, "default": 0,
            "description": "Minimum battery energy storage capacity constraint for optimization"
          },
          "max_kwh": {
            "type": "float", "min": 0, "default": 1000000,
            "description": "Maximum battery energy storage capacity constraint for optimization. Set to zero to disable Storage"
          },
          "internal_efficiency_pct": {
            "type": "float", "min": 0, "max": 1, "default": 0.975,
            "description": "Battery inherent efficiency independent of inverter and rectifier"
          },
          "inverter_efficiency_pct": {
            "type": "float", "min": 0, "max": 1, "default": 0.96,
            "description": "Battery inverter efficiency"
          },
          "rectifier_efficiency_pct": {
            "type": "float", "min": 0, "max": 1, "default": 0.96,
            "description": "Battery rectifier efficiency"
          },
          "soc_min_pct": {
            "type": "float", "min": 0, "max": 1, "default": 0.2,
            "description": "Minimum allowable battery state of charge"
          },
          "soc_init_pct": {
            "type": "float", "min": 0, "max": 1, "default": 0.5,
            "description": "Battery state of charge at first hour of optimization"
          },
          "canGridCharge": {
            "type": "bool", "default": True,
            "description": "Flag to set whether the battery can be charged from the grid, or just onsite generation"
          },
          "installed_cost_us_dollars_per_kw": {
            "type": "float", "min": 0, "max": 1e4, "default": 1000,
            "description": "Total upfront battery power capacity costs (e.g. inverter and balance of power systems)"
          },
          "installed_cost_us_dollars_per_kwh": {
            "type": "float", "min": 0, "max": 1e4, "default": 500,
            "description": "Total upfront battery costs"
          },
          "replace_cost_us_dollars_per_kw": {
            "type": "float", "min": 0, "max": 1e4, "default": 460,
            "description": "Battery power capacity replacement cost at time of replacement year"
          },
          "replace_cost_us_dollars_per_kwh": {
            "type": "float", "min": 0, "max": 1e4, "default": 230,
            "description": "Battery energy capacity replacement cost at time of replacement year"
          },
          "inverter_replacement_year": {
            "type": "float", "min": 0, "max": max_years, "default": 10,
            "description": "Number of years from start of analysis period to replace inverter"
          },
          "battery_replacement_year": {
            "type": "float", "min": 0, "max": max_years, "default": 10,
            "description": "Number of years from start of analysis period to replace battery"
          },
          "macrs_option_years": {
            "type": "int", "restrict_to": macrs_schedules, "default": 7,
            "description": "Duration over which accelerated depreciation will occur. Set to zero by default"
          },
          "macrs_bonus_pct": {
            "type": "float", "min": 0, "max": 1, "default": 0.4,
            "description": "Percent of upfront project costs to depreciate under MACRS in year one in addtion to scheduled depreciation"
          },
          "macrs_itc_reduction": {
            "type": "float", "min": 0, "max": 1, "default": 0.5,
            "description": "Percent of the ITC value by which depreciable basis is reduced"
          },
          "total_itc_pct": {
            "type": "float", "min": 0, "max": 1, "default": 0.0,
            "description": "Total investment tax credit in percent applied toward capital costs"
          },
          "total_rebate_us_dollars_per_kw": {
            "type": "float", "min": 0, "max": 1e9, "default": 0,
            "description": "Rebate based on installed power capacity"
          }
        },

      "Generator": {
        "size_kw": {
          "type": "float",
          "min": 0,
          "max": 1e9,
          "default": 0,
          "description": "Existing on-site generator capacity in kW."
        },
        "fuel_slope_gal_per_kwh": {
          "type": "float",
          "min": 0,
          "max": 10,
          "default": 0,
          "description": "Generator fuel burn rate in gallons/kWh."
        },
        "fuel_intercept_gal_per_hr": {
          "type": "float",
          "min": 0,
          "max": 10,
          "default": 0,
          "description": "Generator fuel consumption curve y-intercept in gallons per hour."
        },
        "fuel_avail_gal": {
          "type": "float",
          "min": 0,
          "max": 1e9,
          "default": 0,
          "description": "On-site generator fuel available in gallons."
        },
        "min_turn_down_pct": {
          "type": "float",
          "min": 0,
          "max": 1,
          "default": 0.3,
          "description": "Minimum generator loading in percent of capacity (size_kw)."
        }
      }
    }
  }
}


def flat_to_nested(i):

    return {
        "Scenario": {
            "timeout_seconds": i.get("timeout"),
            "user_uuid": i.get("user_uuid"),
            "description": i.get("description"),
            "time_steps_per_hour": i.get("time_steps_per_hour"),

            "Site": {
                "latitude": i.get("latitude"),
                "longitude": i.get("longitude"),
                "address": i.get("address"),
                "land_acres": i.get("land_area"),
                "roof_squarefeet": i.get("roof_area"),

                "Financial": {
                                "om_cost_escalation_pct": i.get("om_cost_growth_rate"),
                                "escalation_pct": i.get("rate_escalation"),
                                "owner_tax_pct": i.get("owner_tax_rate"),
                                "offtaker_tax_pct": i.get("offtaker_tax_rate"),
                                "owner_discount_pct": i.get("owner_discount_rate"),
                                "offtaker_discount_pct": i.get("offtaker_discount_rate"),
                                "analysis_years": i.get("analysis_period"),
             },

                "LoadProfile":
                    {
                        "doe_reference_name": i.get("load_profile_name"),
                        "annual_kwh": i.get("load_size"),
                        "year": i.get("load_year"),
                        "monthly_totals_kwh": i.get("load_monthly_kwh"),
                        "loads_kw": i.get("load_8760_kw"),
                        "outage_start_hour": i.get("outage_start"),
                        "outage_end_hour": i.get("outage_end"),
                        "critical_load_pct": i.get("crit_load_factor"),
                 },

                "ElectricTariff":
                    {
                        "urdb_utility_name": i.get("utility_name"),
                        "urdb_rate_name": i.get("rate_name"),
                        "urdb_response": i.get("urdb_rate"),
                        "blended_monthly_rates_us_dollars_per_kwh": i.get("blended_utility_rate"),
                        "blended_monthly_demand_charges_us_dollars_per_kw": i.get("demand_charge"),
                        "net_metering_limit_kw": i.get("net_metering_limit"),
                        "wholesale_rate_us_dollars_per_kwh": i.get("wholesale_rate"),
                        "interconnection_limit_kw": i.get("interconnection_limit"),
                 },

                "PV":
                    {
                        "min_kw": i.get("pv_kw_min"),
                        "max_kw": i.get("pv_kw_max"),
                        "installed_cost_us_dollars_per_kw": i.get("pv_cost"),
                        "om_cost_us_dollars_per_kw": i.get("pv_om"),
                        "degradation_pct": i.get("pv_degradation_rate"),
                        "azimuth": i.get("azimuth"),
                        "losses": i.get("losses"),
                        "array_type": i.get("array_type"),
                        "module_type": i.get("module_type"),
                        "gcr": i.get("gcr"),
                        "dc_ac_ratio": i.get("dc_ac_ratio"),
                        "inv_eff": i.get("inv_eff"),
                        "radius": i.get("radius"),
                        "tilt": i.get("tilt"),
                        "macrs_option_years": i.get("pv_macrs_schedule"),
                        "macrs_bonus_pct": i.get("pv_macrs_bonus_fraction"),
                        "macrs_itc_reduction": i.get("pv_macrs_itc_reduction"),
                        "federal_itc_pct": i.get("pv_itc_federal"),
                        "state_ibi_pct": i.get("pv_ibi_state"),
                        "state_ibi_max_us_dollars": i.get("pv_ibi_state_max"),
                        "utility_ibi_pct": i.get("pv_ibi_utility"),
                        "utility_ibi_max_us_dollars": i.get("pv_ibi_utility_max"),
                        "federal_rebate_us_dollars_per_kw": i.get("pv_rebate_federal"),
                        "state_rebate_us_dollars_per_kw": i.get("pv_rebate_state"),
                        "state_rebate_max_us_dollars": i.get("pv_rebate_state_max"),
                        "utility_rebate_us_dollars_per_kw": i.get("pv_rebate_utility"),
                        "utility_rebate_max_us_dollars":i.get("pv_rebate_utility_max"),
                        "pbi_us_dollars_per_kwh": i.get("pv_pbi"),
                        "pbi_max_us_dollars": i.get("pv_pbi_max"),
                        "pbi_years": i.get("pv_pbi_years"),
                        "pbi_system_max_kw": i.get("pv_pbi_system_max"),
                 },

                "Wind":
                    {
                        "min_kw": i.get("wind_kw_min"),
                        "max_kw": i.get("wind_kw_max"),
                        "installed_cost_us_dollars_per_kw": i.get("wind_cost"),
                        "om_cost_us_dollars_per_kw": i.get("wind_om"),
                        "macrs_option_years": i.get("wind_macrs_schedule"),
                        "macrs_bonus_pct": i.get("wind_macrs_bonus_fraction"),
                        "macrs_itc_reduction": i.get("wind_macrs_itc_reduction"),
                        "federal_itc_pct": i.get("wind_itc_federal"),
                        "state_ibi_pct": i.get("wind_ibi_state"),
                        "state_ibi_max_us_dollars": i.get("wind_ibi_state_max"),
                        "utility_ibi_pct": i.get("wind_ibi_utility"),
                        "utility_ibi_max_us_dollars": i.get("wind_ibi_utility_max"),
                        "federal_rebate_us_dollars_per_kw": i.get("wind_rebate_federal"),
                        "state_rebate_us_dollars_per_kw": i.get("wind_rebate_state"),
                        "state_rebate_max_us_dollars": i.get("wind_rebate_state_max"),
                        "utility_rebate_us_dollars_per_kw": i.get("wind_rebate_utility"),
                        "utility_rebate_max_us_dollars": i.get("wind_rebate_utility_max"),
                        "pbi_us_dollars_per_kwh": i.get("wind_pbi"),
                        "pbi_max_us_dollars": i.get("wind_pbi_max"),
                        "pbi_years": i.get("wind_pbi_years"),
                        "pbi_system_max_kw": i.get("wind_pbi_system_max"),
                 },

                "Storage":
                    {
                    "min_kw": i.get("batt_kw_min"),
                    "max_kw": i.get("batt_kw_max"),
                    "min_kwh": i.get("batt_kwh_min"),
                    "max_kwh": i.get("batt_kwh_max"),
                    "internal_efficiency_pct": i.get("batt_efficiency"),
                    "inverter_efficiency_pct": i.get("batt_inverter_efficiency"),
                    "rectifier_efficiency_pct": i.get("batt_rectifier_efficiency"),
                    "soc_min_pct": i.get("batt_soc_min"),
                    "soc_init_pct": i.get("batt_soc_init"),
                    "canGridCharge": i.get("batt_can_gridcharge"),
                    "installed_cost_us_dollars_per_kw": i.get("batt_cost_kw"),
                    "installed_cost_us_dollars_per_kwh": i.get("batt_cost_kwh"),
                    "replace_cost_us_dollars_per_kw": i.get("batt_replacement_cost_kw"),
                    "replace_cost_us_dollars_per_kwh": i.get("batt_replacement_cost_kwh"),
                    "inverter_replacement_year": i.get("batt_replacement_year_kw"),
                    "battery_replacement_year": i.get("batt_replacement_year_kwh"),
                    "macrs_option_years": i.get("batt_macrs_schedule"),
                    "macrs_bonus_pct": i.get("batt_macrs_bonus_fraction"),
                    "macrs_itc_reduction": i.get("batt_macrs_itc_reduction"),
                    "total_itc_pct":  i.get("batt_itc_total"),
                    "total_rebate_us_dollars_per_kw": i.get("batt_rebate_total"),
             },
         },
     },
 }
