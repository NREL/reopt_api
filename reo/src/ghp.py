import numpy as np
import pandas as pd
import copy
from reo.utilities import MMBTU_TO_KWH, TONHOUR_TO_KWHT
from reo.src.incentives import Incentives, IncentivesNoProdBased
from reo.src.data_manager import big_number

ground_k_by_climate_zone = pd.read_csv("input_files/ground_conductivity.csv", index_col="zone", dtype={"zone":str, "k": float})

class GHPGHXInputs:
    """
    Map the GHPGHX inputs to the objects in this class
    """

    def __init__(self, inputs_dict, **kwargs):
        #TODO Add ALL the input fields for the GHPGHX model
        #   (remove all intermediate calculated fields based on inputs from here, so it's cleaner as the GHP POST)
        self.heating_thermal_mmbtu_per_hr = inputs_dict["heating_thermal_load_mmbtu_per_hr"]
        self.heating_thermal_kw = list(np.array(self.heating_thermal_mmbtu_per_hr) * MMBTU_TO_KWH)
        self.cooling_thermal_ton = inputs_dict["cooling_thermal_load_ton"]
        self.cooling_thermal_kw = list(np.array(self.cooling_thermal_ton) * TONHOUR_TO_KWHT)

class GHPGHXOutputs:
    """
    Define the GHPGHX response parameters that would go to REopt
    """

    def __init__(self, outputs_dict, **kwargs):           
        
        # Outputs/results of GHPGHX
        self.number_of_boreholes = outputs_dict["number_of_boreholes"]
        self.length_boreholes_ft = outputs_dict["length_boreholes_ft"]
        self.yearly_total_electric_consumption_series_kw = outputs_dict["yearly_total_electric_consumption_series_kw"]
        self.peak_combined_heatpump_thermal_ton = outputs_dict["peak_combined_heatpump_thermal_ton"]

class GHPGHX:
        
    def __init__(self, dfm, response, **kwargs):
        # Multiple GHP design choices/options strategy: make a GHPGHX object FOR EACH (in scenario.py)
        # Loop through range(len(response)) in data_manager to build array inputs for REopt
        self.ghp_uuid = response["ghp_uuid"]
        # Inputs of GHPGHX, which are still needed in REopt
        self.inputs = GHPGHXInputs(response["inputs"])   
        # Outputs of GHPGHX, such as number of bores for GHX size
        self.outputs = GHPGHXOutputs(response["outputs"])  # This is a single dictionary where the POST is a list_of_dict

        if kwargs.get("force_ghp"):
            self.force_ghp = 1
        else:
            self.force_ghp = 0
        self.installed_cost_heatpump_us_dollars_per_ton = kwargs.get("installed_cost_heatpump_us_dollars_per_ton")
        self.heatpump_capacity_sizing_factor_on_peak_load = kwargs.get("heatpump_capacity_sizing_factor_on_peak_load")
        self.installed_cost_ghx_us_dollars_per_ft = kwargs.get("installed_cost_ghx_us_dollars_per_ft")
        self.installed_cost_building_hydronic_loop_us_dollars_per_sqft = kwargs.get("installed_cost_building_hydronic_loop_us_dollars_per_sqft")
        self.om_cost_us_dollars_per_sqft_year = kwargs.get("om_cost_us_dollars_per_sqft_year")
        self.building_sqft = kwargs.get("building_sqft")

        # Heating and cooling loads served and electricity consumed by GHP
        # TODO with hybrid with auxiliary/supplemental heating/cooling devices, we may want to separate out/distiguish that energy
        self.heating_thermal_load_served_kw = self.inputs.heating_thermal_kw
        self.cooling_thermal_load_served_kw = self.inputs.cooling_thermal_kw
        self.electric_consumption_kw = self.outputs.yearly_total_electric_consumption_series_kw

        # Change units basis from ton to kW to use existing Incentives class
        self.kwargs_mod = copy.deepcopy(kwargs)
        for region in ["federal", "state", "utility"]:
            self.kwargs_mod[region + "_rebate_us_dollars_per_kw"] = kwargs.get(region + "_rebate_us_dollars_per_ton")
        self.incentives = IncentivesNoProdBased(**self.kwargs_mod)
        
        self.setup_installed_cost_curve()

        self.setup_om_cost()

        dfm.add_ghp(self)
    
    def setup_installed_cost_curve(self):
        # GHX and GHP sizing metrics for cost calculations
        self.total_ghx_ft = self.outputs.number_of_boreholes * self.outputs.length_boreholes_ft
        self.heatpump_peak_tons = self.outputs.peak_combined_heatpump_thermal_ton
        
        # Use initial cost curve to leverage existing incentives-based cost curve method in data_manager
        # The GHX and hydronic loop cost are the y-intercepts ([$]) of the cost for each design
        self.ghx_cost = self.total_ghx_ft * self.installed_cost_ghx_us_dollars_per_ft
        self.hydronic_loop_cost = self.building_sqft * self.installed_cost_building_hydronic_loop_us_dollars_per_sqft

        # The DataManager._get_REopt_cost_curve method expects at least a two-point tech_size_for_cost_curve to
        #   to use the first value of installed_cost_us_dollars_per_kw as an absolute $ value and
        #   the initial slope is based on the heat pump size (e.g. $/ton) of the cost curve for
        #   building a rebate-based cost curve if there are less-than big_number maximum incentives
        self.tech_size_for_cost_curve = [0.0, big_number]
        self.installed_cost_us_dollars_per_kw = [self.ghx_cost + self.hydronic_loop_cost, 
                                                self.installed_cost_heatpump_us_dollars_per_ton]

        # Using a separate call to _get_REopt_cost_curve in data_manager for "ghp" (not included in "available_techs")
        #    and then use the value below for heat pump capacity to calculate the final absolute cost for GHP

        # Use this with the cost curve to determine absolute cost
        self.heatpump_capacity_tons = self.heatpump_peak_tons * self.heatpump_capacity_sizing_factor_on_peak_load

    def setup_om_cost(self):
        # O&M Cost
        self.om_cost_year_one = self.building_sqft * self.om_cost_us_dollars_per_sqft_year