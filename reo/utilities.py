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
from numpy import npv
from math import log10, ceil
from reo.models import ErrorModel
import pandas as pd
import numpy as np
import calendar
import datetime


def slope(x1, y1, x2, y2):
    return (y2 - y1) / (x2 - x1)


def intercept(x1, y1, x2, y2):
    return y2 - slope(x1, y1, x2, y2) * x2


def annuity(analysis_period, rate_escalation, rate_discount):
    """
        this formulation assumes cost growth in first period
        i.e. it is a geometric sum of (1+rate_escalation)^n / (1+rate_discount)^n
        for n = 1,..., analysis_period
    """
    x = (1 + rate_escalation) / (1 + rate_discount)
    if x != 1:
        pwf = round(x * (1 - x ** analysis_period) / (1 - x), 5)
    else:
        pwf = analysis_period
    return pwf


def degradation_factor(analysis_period, rate_degradation):
    if analysis_period == 0:
        return 0
    if analysis_period == 1:
        return 1 - rate_degradation
    factor = 1
    factors = [factor]
    for yr in range(1, int(analysis_period)):
        factor *= (1 - rate_degradation)
        factors.append(factor)
    return sum(factors)/analysis_period


def annuity_escalation(analysis_period, rate_escalation, rate_discount):
    '''
    :param analysis_period: years
    :param rate_escalation: escalation rate
    :param rate_discount: discount rate
    :return: present worth factor with escalation (inflation, or degradation if negative)
    NOTE: assume escalation/degradation starts in year 2
    '''
    pwf = 0
    for yr in range(1, int(analysis_period + 1)):
        pwf += (1 + rate_escalation) ** (yr - 1) / (1 + rate_discount) ** yr
    return pwf


def insert_u_bp(xp_array_incent, yp_array_incent, region, u_xbp, u_ybp, p, u_cap):

    xp_array_incent[region].append(u_xbp)
    yp_array_incent[region].append(u_ybp - u_ybp * p + u_cap)
    return xp_array_incent, yp_array_incent


def insert_p_bp(xp_array_incent, yp_array_incent, region, p_xbp, p_ybp, u, p_cap):

    xp_array_incent[region].append(p_xbp)
    yp_array_incent[region].append(p_ybp - (p_cap + p_xbp * u))
    return xp_array_incent, yp_array_incent


def insert_u_after_p_bp(xp_array_incent, yp_array_incent, region, u_xbp, u_ybp, p, p_cap, u_cap):

    xp_array_incent[region].append(u_xbp)
    if p_cap == 0:
        yp_array_incent[region].append(u_ybp - (p * u_ybp + u_cap))
    else:
        yp_array_incent[region].append(u_ybp - (p_cap + u_cap))
    return xp_array_incent, yp_array_incent


def insert_p_after_u_bp(xp_array_incent, yp_array_incent, region, p_xbp, p_ybp, u, u_cap, p_cap):

    xp_array_incent[region].append(p_xbp)
    if u_cap == 0:
        yp_array_incent[region].append(p_ybp - (p_cap + u * p_xbp))
    else:
        yp_array_incent[region].append(p_ybp - (p_cap + u_cap))
    return xp_array_incent, yp_array_incent


def setup_capital_cost_incentive(itc_basis, replacement_cost, replacement_year,
                                 discount_rate, tax_rate, itc,
                                 macrs_schedule, macrs_bonus_pct, macrs_itc_reduction):

    """ effective PV and battery prices with ITC and depreciation
        (i) depreciation tax shields are inherently nominal --> no need to account for inflation
        (ii) ITC and bonus depreciation are taken at end of year 1
        (iii) battery replacement cost: one time capex in user defined year discounted back to t=0 with r_owner
        (iv) Assume that cash incentives reduce ITC basis
        (v) Assume cash incentives are not taxable, (don't affect tax savings from MACRS)
        (vi) Cash incentives should be applied before this function into "itc_basis".
             This includes all rebates and percentage-based incentives besides the ITC
    """

    # itc reduces depreciable_basis
    depr_basis = itc_basis * (1 - macrs_itc_reduction * itc)

    # Bonus depreciation taken from tech cost after itc reduction ($/kW)
    bonus_depreciation = depr_basis * macrs_bonus_pct

    # Assume the ITC and bonus depreciation reduce the depreciable basis ($/kW)
    depr_basis -= bonus_depreciation

    # Calculate replacement cost, discounted to the replacement year accounting for tax deduction
    replacement = replacement_cost * (1-tax_rate) / ((1 + discount_rate) ** replacement_year)

    # Compute savings from depreciation and itc in array to capture NPV
    tax_savings_array = [0]
    for idx, macrs_rate in enumerate(macrs_schedule):
        depreciation_amount = macrs_rate * depr_basis
        if idx == 0:
            depreciation_amount += bonus_depreciation
        taxable_income = depreciation_amount
        tax_savings_array.append(taxable_income * tax_rate)

    # Add the ITC to the tax savings
    tax_savings_array[1] += itc_basis * itc

    # Compute the net present value of the tax savings
    tax_savings = npv(discount_rate, tax_savings_array)

    # Adjust cost curve to account for itc and depreciation savings ($/kW)
    cap_cost_slope = itc_basis - tax_savings + replacement

    # Sanity check
    if cap_cost_slope < 0:
        cap_cost_slope = 0

    return round(cap_cost_slope, 4)


def setup_capital_cost_offgrid(analysis_period, discount_rate, init_cost, replacement_cost, useful_life):

    """ effective PV and battery prices considering multiple asset replacements over the analysis
        period and a final salvage value
    """

    # Total number of replacements needed
    n_replacements = ceil(analysis_period / useful_life) - 1

    replacement_years = []
    replacement_costs = []

    # Calculate discounted cost of each replacement 
    for i in range(n_replacements): 
        replacement_year = useful_life * (i + 1)    
        replacement_years.append(replacement_year)
        replacement_costs.append(replacement_cost * (1+discount_rate)**(-1*replacement_year))

    # Find salvage value if any
    salvage_value = 0 
    if analysis_period % useful_life != 0:
        salvage_years = useful_life - (analysis_period - max(replacement_years))
        salvage_value = (salvage_years/useful_life) * replacement_cost * ((1 + discount_rate)**(-1*analysis_period))

    # Final cost curve accounts for asset replacements and salvage value    
    cap_cost_slope = init_cost + sum(replacement_costs) - salvage_value    
    
    # Sanity check
    if cap_cost_slope < 0:
        cap_cost_slope = 0

    return round(cap_cost_slope, 4)


def check_common_outputs(Test, d_calculated, d_expected):
    """
    Used in tests to compare expected and API response values
    :param Test: test class instance
    :param d_calculated: dict of values from API (flat format)
    :param d_expected: dict of expected values (flat format)
    :return: None
    """

    c = d_calculated
    e = d_expected

    try:
        # check all calculated keys against the expected
        for key, value in e.items():
            tolerance = Test.REopt_tol
            if key == 'npv':
                tolerance = 2 * Test.REopt_tol

            if key in c and key in e:
                if (not isinstance(e[key], list) and isinstance(c[key], list)) or \
                        (isinstance(e[key], list) and not isinstance(c[key], list)):
                    Test.fail('Key: {0} expected type: {1} actual type {2}'.format(key, str(type(e[key])), str(type(c[key]))))
                elif e[key] == 0:
                    Test.assertEqual(c[key], e[key], 'Key: {0} expected: {1} actual {2}'.format(key, str(e[key]), str(c[key])))
                else:
                    if isinstance(e[key], float) or isinstance(e[key], int):
                        if key in ['batt_kw', 'batt_kwh']:
                            # variable rounding depends on scale of sizes
                            Test.assertAlmostEqual(c[key], e[key], -(int(log10(c[key]))))
                        else:
                            Test.assertTrue(abs((float(c[key]) - e[key]) / e[key]) < tolerance,
                                            'Key: {0} expected: {1} actual {2}'.format(key, str(e[key]), str(c[key])))
                    else:
                        pass
            else:
                print("Warning: Expected value for {} not in calculated dictionary.".format(key))

        if 'lcc_bau' in c and c['lcc_bau'] > 0:
        # Total LCC BAU is sum of utility costs
            Test.assertTrue(abs((float(c['lcc_bau'] or 0) - float(c['total_energy_cost_bau'] or 0) - float(c['total_min_charge_adder'] or 0)
                            - float(c['total_demand_cost_bau'] or 0) - float(c['existing_pv_om_cost_us_dollars'] or 0)
                            - float(c['total_fixed_cost_bau'] or 0)
                            - float(c['existing_gen_total_variable_om_cost_us_dollars'] or 0)
                            - float(c['existing_gen_total_fixed_om_cost_us_dollars'] or 0)
                            - float(c['existing_gen_total_fuel_cost_us_dollars'] or 0)
                            - float(c.get('total_boiler_fuel_cost_bau') or 0))
                            / float(c['lcc_bau'] or 0)) < Test.REopt_tol,
                            "LCC_BAU doesn't add up to sum of individual costs")
    except Exception as e:
        print("check_common_outputs failed: {}".format(e.args[0]))
        em = ErrorModel.objects.filter(run_uuid=c["run_uuid"]).first()
        if em is not None:
            raise Exception("""ErrorModel values:
                task: \t {}
                message: \t {}
                traceback: \t {}
                """.format(em.task, em.message, em.traceback)
            )
        else:
            raise e

def generate_year_profile_hourly(year, consecutive_periods):
    """
    This function creates a year-specific 8760 profile with 1.0 for timesteps which are defined in the relative_periods based on
        generalized (non-year specific) datetime metrics. All other values are 0.0. This functions uses numpy, pandas, datetime, and calendar packages/libraries.

    :param year: year for applying consecutive_periods changes based on year and leap years (cut off 12/31/year)
    :param consecutive_periods: either list of dictionaries where each dict defines a period (keys = "month", "start_week_of_month", "start_day_of_week", "start_hour", "duration_hours"; length N periods)
        OR can be a Pandas DataFrame with columns equivalent to the dict keys in which case it gets converted to list_of_dict. All of the value types are integers.
    :return year_profile_hourly_list: 8760 profile with 1.0 for timesteps defined in consecutive_periods, else 0.0.
    :return start_day_of_month_list: list of start_day_of_month which is calculated in this function
    :return errors_list: used in validators.py - errors related to the input consecutive_periods and the year's calendar
    """
    errors_list = []
    # Create datetime series of the year, remove last day of the year if leap year
    if calendar.isleap(year):
        end_date = "12/31/"+str(year)
    else:
        end_date = "1/1/"+str(year+1)
    dt_profile = pd.date_range(start='1/1/'+str(year), end=end_date, freq="1H", closed="left")
    year_profile_hourly_series = pd.Series(np.zeros(8760), index=dt_profile)
    
    # Check if the consecutive_periods is a list_of_dict or other (must be Pandas DataFrame), and if other, convert to list_of_dict
    if not isinstance(consecutive_periods, list):
        consecutive_periods = consecutive_periods.to_dict('records')

    day_of_week_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    start_day_of_month_list = []
    for i in range(len(consecutive_periods)):
        start_month = int(consecutive_periods[i]["month"])  # One-indexed both user input and Calendar package
        start_week_of_month = int(consecutive_periods[i]["start_week_of_month"] - 1)  # One-indexed for user, but zero-index for Calendar
        start_day_of_week = int(consecutive_periods[i]["start_day_of_week"] - 1)  # Monday - Sunday is 1 - 7 for user, 0 - 6 for Calendar
        start_hour = int(consecutive_periods[i]["start_hour"] - 1)  # One-indexed for user, datetime hour is zero-index
        duration_hours = int(consecutive_periods[i]["duration_hours"])
        error_start_text = "Error in chp_unavailability_period {}. ".format(i+1)
        try:
            start_day_of_month = calendar.Calendar().monthdayscalendar(year=year,month=start_month)[start_week_of_month][start_day_of_week]  # One-indexed
            start_day_of_month_list.append(start_day_of_month)
            if start_day_of_month == 0:  # This may happen if there is no day_of_week in the 1st, 5th or 6th week of the month
                raise DayOfWeekError("There is no start_day_of_week {} ({}) in week {} of month {} in the year {}. Remember, Monday is treated as the first day of the week.".format(start_day_of_week+1, day_of_week_name[start_day_of_week], start_week_of_month+1, start_month, year))
            else:
                start_datetime = datetime.datetime(year=year, month=start_month, day=start_day_of_month, hour=start_hour)
                if start_datetime + datetime.timedelta(hours=duration_hours-1) > dt_profile[-1]:
                    raise DurationOverflowsYearError("The start day/time and duration_hours exceeds the end of the year. Please specify two separate unavailability periods: one for the beginning of the year and one for up to the end of the year.")
                else:
                    year_profile_hourly_series[start_datetime:start_datetime + datetime.timedelta(hours=duration_hours-1)] = 1.0
            
        except DayOfWeekError as e:
            errors_list.append(error_start_text + str(e.args[0]))
        except DurationOverflowsYearError as e:
            errors_list.append(error_start_text + str(e.args[0]))
        except:
            errors_list.append(error_start_text + "Invalid set for month {} (1-12), start_week_of_month {} (1-4, possible 5 and 6), start_day_of_week {} (1-7), and start_hour_of_day {} (1-24) for the year {}.".format(start_month, start_week_of_month+1, start_day_of_week+1, start_hour+1, year))

    if errors_list == []:
        year_profile_hourly_list = list(year_profile_hourly_series)
    else:
        year_profile_hourly_list = []   
    
    return year_profile_hourly_list, start_day_of_month_list, errors_list

class DayOfWeekError(Exception):
    pass

class DurationOverflowsYearError(Exception):
    pass

def get_weekday_weekend_total_hours_by_month(year, year_profile_hourly_list):
    """
    Get a summary of a yearly profile by calculating the weekday, weekend, and total hours by month (e.g. for chp_unavailability_periods viewing in the UI)
    :param year for establishing the calendar
    :param year_profile_hourly_list: list of 0's and 1's for tallying the metrics above; typically created using the generate_year_profile_hourly function
    :return weekday_weekend_total_hours_by_month: nested dictionary with 12 keys (one for each month) each being a dictionary of weekday_hours, weekend_hours, and total_hours
    """
        # Create datetime series of the year, remove last day of the year if leap year
    if calendar.isleap(year):
        end_date = "12/31/"+str(year)
    else:
        end_date = "1/1/"+str(year+1)
    dt_profile = pd.date_range(start='1/1/'+str(year), end=end_date, freq="1H", closed="left")
    year_profile_hourly_series = pd.Series(year_profile_hourly_list, index=dt_profile)
    unavail_hours = year_profile_hourly_series[year_profile_hourly_series == 1]
    weekday_weekend_total_hours_by_month = {m:{} for m in range(1,13)}
    for m in range(1,13):
        unavail_hours_month = unavail_hours[unavail_hours.index.month==m]
        weekday_weekend_total_hours_by_month[m]["weekends"] = int(sum(unavail_hours_month[(unavail_hours_month.index.dayofweek==5) | (unavail_hours_month.index.dayofweek==6)]))
        weekday_weekend_total_hours_by_month[m]["weekdays"] = int(sum(unavail_hours_month) - weekday_weekend_total_hours_by_month[m]["weekends"])
        weekday_weekend_total_hours_by_month[m]["total"] = int(weekday_weekend_total_hours_by_month[m]["weekdays"] + weekday_weekend_total_hours_by_month[m]["weekends"])

    return weekday_weekend_total_hours_by_month

#conversion factor for ton-hours to kilowatt-hours thermal
TONHOUR_TO_KWHT = 3.51685  # [kWh/ton-hr]

#Creates and empty dot accessible dict for spoofing an empty DB record (i.e. empty_record().size_kw resolves to None)
class empty_record(dict):
        __getattr__ = dict.get

# Convert MMBtu to kWh or MMBtu/hr to kW
MMBTU_TO_KWH = 293.07107018  # [kWh/MMBtu]

# Convert m^3 to gal
M3_TO_GAL = 264.172  # [gal/m^3]

# Convert gallon of diesel to kWh
GAL_DIESEL_TO_KWH = 40.7

def convert_gal_to_kwh(delta_T_degF, rho_kg_per_m3, cp_kj_per_kgK):
    """
    Convert gallons of stored liquid (e.g. water, water/glycol) to kWh of stored energy in a stratefied tank
    :param delta_T_degF: temperature difference between the hot/warm side and the cold side
    :param rho_kg_per_m3: density of the liquid
    :param cp_kj_per_kgK: heat capacity of the liquid
    :return gal_to_kwh
    """  
    delta_T_K = delta_T_degF * 5.0 / 9.0  # [K]
    m3_to_kj = rho_kg_per_m3 * cp_kj_per_kgK * delta_T_K  # [kJ/m^3]
    gal_to_kwh = m3_to_kj / M3_TO_GAL / 3600.0  # [kWh/gal]

    return gal_to_kwh