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
from reo.src.data_manager import big_number
from reo.nested_inputs import macrs_five_year, macrs_seven_year
from reo.utilities import convert_gal_to_kwh


class StorageIncentives(object):
        
    def __init__(self, macrs_option_years, macrs_bonus_pct, total_itc_pct, total_rebate_us_dollars_per_kw,
                 macrs_itc_reduction=0.5, total_rebate_us_dollars_per_kwh=0):  # should we expose macrs_itc_reduction to users?
        
        self.itc_pct = total_itc_pct
        self.itc_max = big_number
        
        self.rebate = total_rebate_us_dollars_per_kw
        self.rebate_kwh = total_rebate_us_dollars_per_kwh
        self.rebate_max = big_number
        self.macrs_bonus_pct = macrs_bonus_pct
        self.macrs_itc_reduction = macrs_itc_reduction

        if macrs_option_years == 5:
            self.macrs_schedule = macrs_five_year
        elif macrs_option_years == 7:
            self.macrs_schedule = macrs_seven_year
        elif macrs_option_years == 0:
            self.macrs_bonus_pct = 0
            self.macrs_itc_reduction = 0
            self.macrs_schedule = [0]
        else:
            raise ValueError("macrs_option_years must be 0, 5 or 7.")
    

class Storage(object):
    """
    REopt class for energy storage.
    All default values in kwargs set by validator using nested_input_definitions.
    """

    def __init__(self, dfm, min_kw, max_kw, min_kwh, max_kwh,
                 internal_efficiency_pct, inverter_efficiency_pct, rectifier_efficiency_pct,
                 soc_min_pct, soc_init_pct, canGridCharge,
                 installed_cost_us_dollars_per_kw, installed_cost_us_dollars_per_kwh,
                 replace_cost_us_dollars_per_kw, replace_cost_us_dollars_per_kwh,
                 inverter_replacement_year, battery_replacement_year,
                 **kwargs):

        self.min_kw = min_kw
        self.max_kw = max_kw
        self.min_kwh = min_kwh
        self.max_kwh = max_kwh

        self.internal_efficiency_pct = internal_efficiency_pct
        self.inverter_efficiency_pct = inverter_efficiency_pct
        self.rectifier_efficiency_pct = rectifier_efficiency_pct
        self.roundtrip_efficiency = internal_efficiency_pct * inverter_efficiency_pct * rectifier_efficiency_pct

        self.soc_min_pct = soc_min_pct
        self.soc_init_pct = soc_init_pct
        self.canGridCharge = canGridCharge

        self.installed_cost_us_dollars_per_kw = installed_cost_us_dollars_per_kw
        self.installed_cost_us_dollars_per_kwh = installed_cost_us_dollars_per_kwh
        self.replace_cost_us_dollars_per_kw = replace_cost_us_dollars_per_kw
        self.replace_cost_us_dollars_per_kwh = replace_cost_us_dollars_per_kwh
        self.inverter_replacement_year = inverter_replacement_year
        self.battery_replacement_year = battery_replacement_year

        self.incentives = StorageIncentives(**kwargs)

        dfm.add_storage(self)


class TESIncentives(object):

    def __init__(self, macrs_option_years, macrs_bonus_pct):

        self.macrs_bonus_pct = macrs_bonus_pct

        if macrs_option_years == 5:
            self.macrs_schedule = macrs_five_year
        elif macrs_option_years == 7:
            self.macrs_schedule = macrs_seven_year
        elif macrs_option_years == 0:
            self.macrs_bonus_pct = 0
            self.macrs_schedule = [0]
        else:
            raise ValueError("macrs_option_years must be 0, 5 or 7.")

class HotTES(object):
    """
    REopt class for hot thermal energy storage (TES).
    All default values in kwargs set by validator using nested_input_definitions.
    """

    # Convert units based on gal to kWht (kWh "thermal), assumes a delta-T in the tank of 20F
    delta_T_degF = 180.0 - 160.0  # [F]        
    avg_cp_kj_per_kgK = 4.194  # [kJ/kg-K] Estimate at 170 degF
    avg_rho_kg_per_m3 = 973.728  # [kg/m^3] Estimate at 170 degF
    gal_to_kwh_conversion = convert_gal_to_kwh(delta_T_degF = delta_T_degF,
                                                rho_kg_per_m3 = avg_rho_kg_per_m3,
                                                cp_kj_per_kgK = avg_cp_kj_per_kgK)

    def __init__(self, dfm, **kwargs):

        # Assign all items in kwargs explicitly to the class
        for key, value in kwargs.items():
            setattr(self, key, value) 
 
        self.gal_to_kwh_conversion = HotTES.gal_to_kwh_conversion

        self.min_kwh = self.min_gal * self.gal_to_kwh_conversion
        self.max_kwh = self.max_gal * self.gal_to_kwh_conversion
        self.installed_cost_us_dollars_per_kwh = self.installed_cost_us_dollars_per_gal / self.gal_to_kwh_conversion
        self.om_cost_us_dollars_per_kwh = self.om_cost_us_dollars_per_gal / self.gal_to_kwh_conversion

        self.incentives = TESIncentives(self.macrs_option_years, self.macrs_bonus_pct)

        dfm.add_hot_tes(self)


class ColdTES(object):
    """
    REopt class for cold thermal energy storage (TES).
    All default values in kwargs set by validator using nested_input_definitions.
    """

    # Convert units based on gal to kWht (kWh "thermal), assumes a delta-T in the tank of 12F
    delta_T_degF = 56.0 - 44.0  # [F]
    avg_cp_kj_per_kgK = 4.195  # [kJ/kg-K] Estimate at 50 degF
    avg_rho_kg_per_m3 = 999.702  # [kg/m^3] Estimate at 50 degF
    gal_to_kwh_conversion = convert_gal_to_kwh(delta_T_degF = delta_T_degF,
                                                rho_kg_per_m3 = avg_rho_kg_per_m3,
                                                cp_kj_per_kgK = avg_cp_kj_per_kgK) 

    def __init__(self, dfm, **kwargs):

        # Assign all items in kwargs explicitly to the class
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.gal_to_kwh_conversion = ColdTES.gal_to_kwh_conversion

        self.min_kwht = self.min_gal * self.gal_to_kwh_conversion
        self.max_kwht = self.max_gal * self.gal_to_kwh_conversion
        self.installed_cost_us_dollars_per_kwht = self.installed_cost_us_dollars_per_gal / self.gal_to_kwh_conversion
        self.om_cost_us_dollars_per_kwht = self.om_cost_us_dollars_per_gal / self.gal_to_kwh_conversion

        self.incentives = TESIncentives(self.macrs_option_years, self.macrs_bonus_pct)

        dfm.add_cold_tes(self)


class HotWaterTank(object):
    """
    REopt class for hot water tank storage.
    All default values in kwargs set by validator using nested_input_definitions.
    """

    def __init__(self, dfm, **kwargs):

        # Assign all items in kwargs explicitly to the class
        for key, value in kwargs.items():
            setattr(self, key, value)
        dfm.add_hot_water_tank(self)