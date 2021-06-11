# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Guidelines
- When making a Pull Request into `develop` start a new double-hash header for "Develop - YYYY-MM-DD"
- When making a Pull Request into `master` change "Develop" to the next version number

### Formatting
- Use **bold** markup for field and model names (i.e. **outage_start_time_step**)
- Use `code` markup for  REopt Lite-specific file names, classes and endpoints (i.e `reo/validators.py`)
- Use _italic_ for code terms (i.e. _list_)
- Prepend change with tag(s) directing where it is in the repository:  
`reo`,`proforma`,`resilience_stats`,`*.jl`,`REopt_Lite_API`

Classify the change according to the following categories:
    
    ### Major Updates
    ### Minor Updates
    ##### Added
    ##### Changed
    ##### Fixed
    ##### Deprecated
    ##### Removed
    ### Patches

## v1.6.0 - 2021-06-09
### Minor Updates
##### Added
- `summary`: Added `/summary_by_chunk` endpoint to enable a fraction of a user's total runs and summary metrics to be returned; this prevents excessive wait times when the UI was trying to load all runs
- New `<host>/dev/futurecosts` endpoint 
##### Patches
- was returning -1 for `bau_sustained_time_steps` when no critical load was met in BAU case (now returns zero)
- fixed issue with modeling last time step of the year in outages 
- `NewMaxSize` was sometimes less than the `TechClassMinSize`, creating infeasible problems
- fix `user` URLs

## v1.5.0 - 2021-03-12
### Minor Updates
##### Changed
- `reo`, `*.jl`: Changed the units-basis for heating load, thermal production, and fuel consumption to kW/kWh, from mmbtu/mmbtu_per_hr and gal. This does not affect the units of the inputs or outputs.
##### Removed
- `reo`: The following inputs for `Site.Boiler`: `installed_cost_us_dollars_per_mmbtu_per_hr`, `min_mmbtu_per_hr`, and `max_mmbtu_per_hr`, and for `Site.ElectricChiller`: `installed_cost_us_dollars_per_kw`, `min_kw`, and `max_kw`.
### Patches
- `reo`: Catch issue in `process_results.py` where `renewable_electricity_energy_pct` is not explicitly set to _None_
- `reo`:  Catch case where `CHP` `prime_mover` is not set and not all required fields are filled in
- `reo`:  Catch issues with `itc_unit_basis` when the ITC is 100%
- `validators.py`: Fix bug where length of percent_share != length of doe_reference_name even though no percent_share is provided (in `LoadProfileBoilerFuel`)

## v1.4.4 - 2021-02-25
### Patches
- `reo`: In `validators.py` catches case where invalid percent_share entry was used in check special cases function
- `reo`: In `loadprofile.py` catches where 0 lat/long was resolving to _False_ and leading to _None_ for lat and long
- `reo`: Fix divide by 0 error in results processing
- `reo`: Handle floats as URBD periods
- `reo`: Fix `list_of_float` only types
    
## v1.4.3 - 2021-02-18
### Patches
- `reo`: new output `Financial.developer_om_and_replacement_present_cost_after_tax_us_dollars`
- `reo`: Fix **PVWatts** being called when user provides `PV.prod_factor_series_kw`
- `reopt_api`: new `docker-compose.nginx.yml` for standing up the API on a server with remote access (for example if one wants to host the API on a cloud service)
- `reopt_api`: update `Dockerfile.xpress` to use `nlaws/pyjul:1.5.3` base image (was using Julia 1.3)
- `reopt_api`: update `julia_envs/Xpress` PyCall from 1.91.4 to 1.92.2
    
## v1.4.2 - 2021-02-03
### Patches
- `reo`: Fix **Wind** `size_class` was not being set
- `proforma`: Fix could not handle runs prior to v1.4.0 with no CHP database entries
- `resilience_stats`: Fix could not handle runs prior to v1.4.0 with no CHP database entries
- `resilience_stats`: `outage_simulator` returns 100% survivability when chp_kw >= critical_loads_kw

## v1.4.1 - 2021-02-01
### Patches
- `reo`: Fixes database query error the occurs when getting production runs created prior to v1.4.0    

## v1.4.0 - 2021-01-29
### Major Updates
### Minor Updates
## Added
- `reo`/`reopt.jl`: Coincident peak rates and expected time steps can be specified. There can be a single rate and list of time steps. Or there can be multiple CP periods in a year with different rates, and then a set of time steps is specified for each rate. Peak demand occurring during each set of CP time steps is charged at the corresponding CP rate.

- `reo`: Add a new **ElectricTariff** inputs and outputs: 
 - **coincident_peak_load_active_timesteps**
 - **coincident_peak_load_charge_us_dollars_per_kw**
 - **year_one_coincident_peak_cost_us_dollars**
 - **year_one_coincident_peak_cost_bau_us_dollars**
 - **total_coincident_peak_cost_us_dollars**
 - **total_coincident_peak_cost_bau_us_dollars**

## v1.3.0 - 2021-01-28
### Major Updates
### Minor Updates
- `reo`: New output **om_and_replacement_present_cost_after_tax_us_dollars**
- `reo`, `*.jl`: New load **LoadProfileBoilerFuel**
    - Heating load of the site, as defined by boiler fuel consumption
- `reo`, `*.jl`: New Tech **Boiler**
    - BAU Tech which serves heating load. It consumes fuel and produces hot thermal energy.
- `reo`: New **Site**-level input **FuelTariff**
    - Cost structure for fuel consumed by **Boiler** and **CHP** Techs. Currently allows fixed annual or monthly values for fuel cost.
- `reo`, `*.jl`: New load **LoadProfileChillerThermal**
    - Cooling load of the site, as defined by a thermal load produced by the BAU **ElectricChiller** or a fraction of total electric load.
    - This is treated as a subset of the total electric load (**LoadProfile**)
- `reo`, `*.jl`: New Tech **ElectricChiller**
    - BAU Tech which serves cooling load. It consumes electricity and produces chilled water to meet the cooling load or charge **ColdTES**.
- `reo`, `*.jl`: New Tech **CHP**
    - Combined heat and power (CHP) Tech which serves electric and heating loads. Its hot thermal production can also supply **AbsorptionChiller** or charge the **HotTES**.
- `reo`, `*.jl`: New Tech **AbsorptionChiller**
    - Cooling technology which serves cooling load with a hot thermal input. It can also charge **ColdTES**.
- `reo`, `*.jl`: New Storage **HotTES**
    - Storage model representing a hot water thermal energy storage tank. It can store hot thermal energy produced by **CHP** (or **Boiler**, but not typically).
- `reo`, `*.jl`: New Storage **ColdTES**
    - Storage model representing a chilled water thermal energy storage tank. It can store cold thermal energy produced by **ElectricChiller** or **AbsorptionChiller**.
- `reo`: Changed `/simulated_load` endpoint to add optional **load_type** query param for **cooling** and **heating**
    - Use **load_type** = "heating" with **annual_mmbtu** or **monthly_mmbtu** for heating load
    - Use **load_type** = "cooling" with **annual_tonhour** or **monthly_tonhour** for cooling load 
- `reo`: New endpoint `/chp_defaults`
    - Endpoint for the default **prime_mover**, **size_class**, and default cost and performance parameters for **CHP**
- `reo`: New endpoint `/loadprofile_chillerthermal_chiller_cop`
    - Endpoint for the default **LoadProfileChillerThermal.chiller_cop** based on peak cooling load
- `reo`: New endpoint `/absorption_chiller_defaults`
    - Endpoint for the default **AbsorptionChiller** cost and performance parameters based on thermal type ("hot_water" or "steam") and peak cooling load
- `reo`: New endpoint `/schedule_stats`
    - Endpoint for getting default **CHP.chp_unavailability_periods** and summary metrics of the unavailability profile
### Patches
 - `summary`: Address failing cases in user `summary` endpoint due to missing load profile data


## v1.2.0 - 2021-01-04
### Major Updates
### Minor Updates
##### Added
- `reo`: new inputs **outage_start_time_step** and **outage_end_time_step** to replace deprecated **outage_start_hour** and **outage_end_hour**. The latter are used as time step indices in the code, so for sub-hourly problems they do not have hourly units. For now **outage_start_hour** and **outage_end_hour** are kept in place to preserve backwards-compatibility. Also note that the new inputs are not zero-indexed.
- `reo`: new output **bau_sustained_time_steps** to replace deprecated **sustain_hours** (also not deprecated yet but warning is now in response).
- `*.jl`: new **dvProductionToCurtail** for all techs in all time steps (was previously construed with dvProductionToGrid for the third sales tier, which is meant for selling energy back to the grid beyond the annual load kWh constraint.)
- `reo`:  new inputs for all Techs: **can_net_meter**, **can_wholesale**, **can_export_beyond_site_load**, **can_curtail**
    - the first three correspond to the previous `SalesTiers`, now called `ExportTiers`
    - reduces the problem size in many cases since the previous model always included all three `SalesTiers` in every scenario and the new model only includes `ExportTiers` with non-zero compensation when there are Technologies that can participate

##### Changed
- `resilience_stats`: Calculate **avoided_outage_costs_us_dollars** from the `outagesimjob` endpoint
##### Fixed
##### Deprecated
- `reo`: **LoadProfile** **outage_start_hour** and **outage_end_hour** in favor of **outage_start_time_step** and **outage_end_time_step**
- `reo`: **LoadProfile** **sustain_hours** in favor of **bau_sustained_time_steps**

##### Removed

### Patches
- `resilience_stats`: Catch BAU cases and do not calculate avoided outage costs
- `summary`: Catch jobs that errored out and do not parse results
- `reo`: Catch `PVWattsDownloadError` when a bad response is received
- `reo`: **fuel_used_gal** output for **Generator** was incorrect for scenarios with **time_steps_per_hour** not equal to 1


## v1.1.0 - 2020-12-08
### Major
### Minor
##### Added
- `reo`: Add new Financial outputs :
     - **developer_annual_free_cashflow_series_us_dollars**
     - **offtaker_annual_free_cashflow_series_bau_us_dollars**
     - **offtaker_annual_free_cashflow_series_us_dollars** 
     - **offtaker_discounted_annual_free_cashflow_series_bau_us_dollars**
     - **offtaker_discounted_annual_free_cashflow_series_us_dollars**
- `reo`: New capability to model a rolling lookback if URDB lookbackRange is non-zero
- `reo`: Add a new third-party financing output: 
     - **net_present_cost_us_dollars**
- `reo`: New Wind curtailment output
     - **year_one_curtailed_production_series_kw**
- `reo`: Emissions factor series added for ElecticTariff (defaults to AVERT regional data) and Generator:
     - **emissions_factor_series_lb_CO2_per_kwh**
     - **emissions_factor_lb_CO2_per_gal**
- `reo`/`proforma`: ElectricTariff, Generator and Site year 1 emissions totals as new outputs from API and in Proform
     - **emissions_region** (Site Only)
     - **year_one_emissions_lb_C02**
     - **year_one_emissions_bau_lb_C02**
- `reo`: LCOE API output added for PV and Wind:
     - **lcoe_us_dollars_per_kwh**
- `reo`: Simple Payback/IRR API outputs added for Site:
     - **irr_pct**
     - **simple_payback_years**
- `reo`: New total storage rebates ($/kWh) Storage input:
     - **total_rebate_us_dollars_per_kwh**
- `proforma`: PV LCOE, Wind LCOE,  Host Present Worth Factor, Developer Present Worth Factor, PV Energy Levelization Factor, and Simple Payback added
- `*.jl`Add new constraint that sets `dvGridToStorage` to zero for all grid connected time steps when Storage.canGridCharge is false
- `reo`: Add hybrid load profile option. New LoadProfile inputs:
     - **percent_share**
     - **doe_reference_name** (now a str or lis of str)
- `reo`: Add PV curtailment output:
     - **year_one_curtailed_production_series_kw**
- `proforma`:  Two proforma templates, now with 3 tabs instead of 2. 
     [1] one party: separate optimal and BAU cash flows
     [2] two party: separate developer and host cash flows (showing capital recovery factor and developer IRR ). 
- `reo`: New output for year 1 existing PV production
     - **average_yearly_energy_produced_bau_kwh**
- `reo`: Add inputs to ElectricTariff to handle custom TOU energy rates (1-hr or 15-min resolutions):
	- **add_tou_energy_rates_to_urdb_rate**
	- **tou_energy_rates_us_dollars_per_kwh** 
- `reo`: Handle multiple PV systems by including a list of PV dictionaries instead of a single dictionary. New PV inputs include:
    - **pv_name**
	- **pv_number** 
	- **location**
- `reo`: New custom production factor inputs for PV and Wind: 
     - **prod_factor_series_kw**
- `reo`: Three new **Financial** outputs: 
     - **initial_capital_costs**
     - **initial_capital_costs_after_incentives**
     - **replacement_costs**
- `resilience_stats`: New `financial_check` endpoint

##### Changed
- `reo`: Remove third-party factor from **initial_capital_costs_after_incentives** output
- `reo`/`proforma`: Renames two party to third-party throughout the code
- `reo`: When the wholesale rate is zero, all excess production is forced into curtailment bin by setting the wholesale rate to -1,000 $/kWh
- `resilience_stats`: New post-and-poll process for resilience stats and removal of **avoided_outage_costs_us_dollars** calculation from results endpoint
     \
     **Note in the future this kind of change will be classified as major**
- `*.jl`: reverted export rate inputs to negative values (to match legacy conventions)
- `reo`: Enables existing diesel generator in the financial case outage simulation

##### Fixed
- `reo`: Developer generator OM costs now based on new capacity only in API-side calculations to match Proforma spreadsheet (could results in different API-reported NPV)
- `resilience_stats`: Bug fix **PV** was not contributing to sustaining outage in the BAU case
- `reo`: In non-third party cases the owner tax and discount percents were not saved to the database resulting in inaccurate after-incentive cost calculations in the web UI
- `*.jl`: **Wind** dispatch fixes in julia code - including hooking up missing outputs
- `*.jl`: Load balances constraints fixed in julia code
- `proforma`: Addressed bugs, including: 
    - Removed energy generation values from cash flow sheets
	- Added **Generator** fixed O&M cost outputs (was not accounted for in proforma)
	- Upfront capex was wrong with existing kw and no optimal kw
	- Removed **PV** degradation from other techs' annual production
	- Escalation and discount rates were applied incorrectly (off by one year)
	- O&M costs were double accounted, once with tax benefit, once without
	- Total installed costs was calculated incorrectly
	- **Wind** and **Storage** bonus fraction cell references were switched with each other in proforma_generator
	- Corrected **PV** PBI calcultion using new existing PV production output 

##### Deprecated
##### Removed

### Patches
- `reo`: Catch and flag _NaN_ input parameters
- `*.jl`: Update `Xpress.jl` to v0.12 (should fix the OOM issues with celery workers)
- `reo`: Set new cap on tax rates to avoid a divide by zero in results processing and the proforma
- `*.jl`: fix OutOfMemory error in docker containers when building constraints in models that have more than one time step per hour
- `reo`: Fix divide by 0 error in BAU outage sim job code when no existing PV
- `reo`: Fix **simple_payback_years** and **irr_pct** calcs in `reo/process_results.py`
- `reo`: Fix bug in **upfront_capex_after_incentives**
- `reo`: `Scenario.py` was checking for wrong message in exception and raising `UnexpectedError` instead of `WindDownloadError`
- `*.jl`: Diesel fuel costs were indexed on electric tariff tiers, which was necessary before the reformulation, but now leads to an index error in the JuMP model.
- `reo`: Addresses multiple pvs and a division by 0 case in outage simulator inputs
- `reo`: Report _NaN_ IRR values as _null_
- `reo`: Require **energyratestructure**, **energyweekendschedule** and **energyweekdayschedule** in a URDB rate; added new checking of URDB float fields
- `proforma`: Fix bug when **year_one_export_benefit_bau_us_dollars** or **year_one_export_benefit_us_dollars** is null
- `reo`: Updated handling of cases where outagesim results are not ready
- `*.jl`: DER export to grid (in NEM and wholesale `SalesTiers`) was not set to zero during `TimeStepsWithoutGrid`.
- `reo`: Run scenarios through `reopt.jl` to get the code precompiled in system images
- `reo`: Fixes generator power output bug in resilience check
- `resilience_stats`: Catches case where the same outagesim job is submitted twice
- `resilience_stats`: Replaces _JsonResponse_ with _ImmediateHttpResponse_ for errors in `outagesimjob` workflow
- `reo`: Bug fix to enable battery dispatch results to be returned
- `resilience_stats`: When an outagesimjob has already been returned the status code is now 208 (Already Reported) rather than 500
- `reo`: Enable rerunning of POSTs (clean up **PV** and **Wind** prod factor and all `percent_share` entries in `results` response)
- `reo`: Uses new Wind Toolkit API URL
- `proforma`: Updated storage to read per kW and per kWh incentives
- `proforma`: Updated final cashflow to include non-taxed year 0 incentives (CBI and IBI)
- `*.jl`: `MinChargeAdd` in `reopt.jl` was only accounting for year zero charges (needs to be lifecycle charges)
- `REopt_Lite_API`: Use Django version 2.2.13 (had been 2.2.6)
- `reo`: Handling the financial scenario's user uploaded critical load series bug
- `reo`: Fix bug in URDB parsing timestep for TOU rates
- `reo`: Fix bug in error handling for load profiles with negative non-net loads
- `reo`: Handle non `REoptError`s in scenario.py
- `reo`: `results` response will not return empty lists in inputs or outputs
- `reo`: Use default **LoadProfile** `year` of 2017 for all built-in load profiles
- `reo`: Set 2019 default `year` in nested_inputs
- `*.jl`: Fix bug where `pwf_prod_incent` was accounting for the discount rate and `LevelizationFactorProdIncent` was accounting for production degradation
- `reo`: Upgrade to URDB 7, maintain backwards compatibility
- `resilience_stats`: New resilience stats and financial metrics added to user summary endpoint
- `reo`: More informative PVWatts error when site it too far away
- `reo`/`resilience_stats`: Fix bug where `simulated_load` endpoint was not handling `monthly_totals_kwh`
- `reo`: Fix bug where **Wind** was not constrained based on `land_acres`
- `resilience_stats`: Fix resilience stastics bugs including: 
    - mis-scaling the existing **PV** production
    - `resilience_stats` was returning 8759 hours survived when critical load was met for entire year
    - `resilience_stats` battery model was assuming that inverter was DC capacity, but inverter is AC capacity
    - the monthly and hourly survival probabilities were being returned as 1 when there was zero probability
- `*.jl`: Upgrade psutil from 4.3.1 to 5.6.6.

## v1.0.0 - 2020-02-28
### Major
- First release of the REopt API
