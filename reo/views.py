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
import csv
import os
import sys
import traceback as tb
import uuid
import copy
import json
from django.http import JsonResponse
from reo.src.load_profile import BuiltInProfile, LoadProfile, get_climate_zone
from reo.src.load_profile_boiler_fuel import LoadProfileBoilerFuel
from reo.src.load_profile_chiller_thermal import LoadProfileChillerThermal
from reo.models import URDBError
from reo.nested_inputs import nested_input_definitions
from reo.api import UUIDFilter
from reo.models import ModelManager
from reo.exceptions import UnexpectedError  #, RequestError  # should we save bad requests? could be sql injection attack?
import logging
log = logging.getLogger(__name__)
from reo.src.techs import Generator, CHP, AbsorptionChiller, Boiler
from reo.src.emissions_calculator import EmissionsCalculator
from django.http import HttpResponse
from django.template import  loader
import pandas as pd
from reo.utilities import generate_year_profile_hourly, TONHOUR_TO_KWHT, get_weekday_weekend_total_hours_by_month
from reo.validators import ValidateNestedInput
from datetime import datetime, timedelta
from reo.src.ghp import ground_k_by_climate_zone
# import math
# import geopandas as gpd
# from shapely import geometry as g


# loading the labels of hard problems - doing it here so loading happens once on startup
hard_problems_csv = os.path.join('reo', 'hard_problems.csv')
hard_problem_labels = [i[0] for i in csv.reader(open(hard_problems_csv, 'r'))]

def make_error_resp(msg):
        resp = dict()
        resp['messages'] = {'error': msg}
        resp['outputs'] = dict()
        resp['outputs']['Scenario'] = dict()
        resp['outputs']['Scenario']['status'] = 'error'
        return resp


def health(request):
    return HttpResponse("OK")


def help(request):

    try:
        response = copy.deepcopy(nested_input_definitions)
        return JsonResponse(response)

    except Exception as e:
        return JsonResponse({"Error": "Unexpected error in help endpoint: {}".format(e.args[0])}, status=500)


def invalid_urdb(request):

    try:
        # invalid set is populated by the urdb validator, hard problems defined in csv
        invalid_set = list(set([i.label for i in URDBError.objects.filter(type='Error')]))
        return JsonResponse({"Invalid IDs": list(set(invalid_set + hard_problem_labels))})

    except Exception as e:
        return JsonResponse({"Error": "Unexpected error in invalid_urdb endpoint: {}".format(e.args[0])}, status=500)


def annual_kwh(request):

    try:
        latitude = float(request.GET['latitude'])  # need float to convert unicode
        longitude = float(request.GET['longitude'])

        if latitude > 90 or latitude < -90:
            raise ValueError("latitude out of acceptable range (-90 <= latitude <= 90)")

        if longitude > 180 or longitude < -180:
            raise ValueError("longitude out of acceptable range (-180 <= longitude <= 180)")

        if 'doe_reference_name' in request.GET.keys():
            doe_reference_name = [request.GET.get('doe_reference_name')]
            percent_share_list = [100.0]
        elif 'doe_reference_name[0]' in request.GET.keys():
            idx = 0
            doe_reference_name = []
            percent_share_list = []
            while 'doe_reference_name[{}]'.format(idx) in request.GET.keys():
                doe_reference_name.append(request.GET['doe_reference_name[{}]'.format(idx)])
                if 'percent_share[{}]'.format(idx) in request.GET.keys():
                    percent_share_list.append(float(request.GET['percent_share[{}]'.format(idx)]))
                idx += 1
        else:
            doe_reference_name = None

        if doe_reference_name is not None:
            for name in doe_reference_name:
                if name not in BuiltInProfile.default_buildings:
                    raise ValueError("Invalid doe_reference_name {}. Select from the following: {}"
                             .format(name, BuiltInProfile.default_buildings))
            uuidFilter = UUIDFilter('no_id')
            log.addFilter(uuidFilter)
            b = LoadProfile(latitude=latitude, longitude=longitude, percent_share=percent_share_list,
                    doe_reference_name=doe_reference_name, critical_load_pct=0.5)
            response = JsonResponse(
            {'annual_kwh': b.annual_kwh,
             'city': b.city},
            )
            return response
        else:
            return JsonResponse({"Error": "Missing doe_reference_name input"}, status=500)

    except KeyError as e:
        return JsonResponse({"Error. Missing": str(e.args[0])}, status=500)

    except ValueError as e:
        return JsonResponse({"Error": str(e.args[0])}, status=500)

    except Exception as e:

        exc_type, exc_value, exc_traceback = sys.exc_info()
        debug_msg = "exc_type: {}; exc_value: {}; exc_traceback: {}".format(exc_type, exc_value.args[0],
                                                                            tb.format_tb(exc_traceback))
        log.debug(debug_msg)
        return JsonResponse({"Error": "Unexpected error in annual_kwh endpoint. Check log for more."}, status=500)


def remove(request, run_uuid):
    try:
        ModelManager.remove(run_uuid)  # ModelManager has some internal exception handling
        return JsonResponse({"Success": True}, status=204)

    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        err = UnexpectedError(exc_type, exc_value.args[0], tb.format_tb(exc_traceback), task='remove', run_uuid=run_uuid)
        err.save_to_db()
        resp = make_error_resp(err.message)
        return JsonResponse(resp)


def results(request, run_uuid):
    try:
        uuid.UUID(run_uuid)  # raises ValueError if not valid uuid

    except ValueError as e:
        if e.args[0] == "badly formed hexadecimal UUID string":
            resp = make_error_resp(e.args[0])
            return JsonResponse(resp, status=400)
        else:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            err = UnexpectedError(exc_type, exc_value.args[0], tb.format_tb(exc_traceback), task='results', run_uuid=run_uuid)
            err.save_to_db()
            return JsonResponse({"Error": str(err.args[0])}, status=400)

    try:
        d = ModelManager.make_response(run_uuid)  # ModelManager has some internal exception handling

        response = JsonResponse(d)
        return response

    except Exception:

        exc_type, exc_value, exc_traceback = sys.exc_info()
        err = UnexpectedError(exc_type, exc_value.args[0], tb.format_tb(exc_traceback), task='reo.views.results', run_uuid=run_uuid)
        err.save_to_db()
        resp = make_error_resp(err.message)
        return JsonResponse(resp, status=500)


def emissions_profile(request):
    try:
        latitude = float(request.GET['latitude'])  # need float to convert unicode
        longitude = float(request.GET['longitude'])

        ec = EmissionsCalculator(latitude=latitude,longitude=longitude)

        try:
            response = JsonResponse({
                    'region_abbr': ec.region_abbr,
                    'region': ec.region,
                    'emissions_series_lb_CO2_per_kWh': ec.emissions_series,
                    'units': 'Pounds Carbon Dioxide Equivalent',
                    'description': 'Regional hourly grid emissions factor for EPA AVERT regions.',
                    'meters_to_region': ec.meters_to_region
                })
            return response
        except AttributeError as e:
            return JsonResponse({"Error": str(e.args[0])}, status=500)

    except KeyError as e:
        return JsonResponse({"Error. Missing Parameter": str(e.args[0])}, status=500)

    except ValueError as e:
        return JsonResponse({"Error": str(e.args[0])}, status=500)

    except Exception:

        exc_type, exc_value, exc_traceback = sys.exc_info()
        debug_msg = "exc_type: {}; exc_value: {}; exc_traceback: {}".format(exc_type, exc_value.args[0],
                                                                            tb.format_tb(exc_traceback))
        log.error(debug_msg)
        return JsonResponse({"Error": "Unexpected Error. Please check your input parameters and contact reopt@nrel.gov if problems persist."}, status=500)


def simulated_load(request):
    try:
        valid_keys = ["doe_reference_name","latitude","longitude","load_type","percent_share","annual_kwh",
                        "monthly_totals_kwh","annual_mmbtu","annual_fraction","annual_tonhour","monthly_tonhour",
                        "monthly_mmbtu","monthly_fraction","max_thermal_factor_on_peak_load","chiller_cop",
                        "addressable_load_fraction", "space_heating_fraction_of_heating_load"]
        for key in request.GET.keys():
            k = key
            if "[" in key:
                k = key.split('[')[0]
            if k not in valid_keys:
                raise ValueError("{} is not a valid input parameter".format(key))

        latitude = float(request.GET['latitude'])  # need float to convert unicode
        longitude = float(request.GET['longitude'])
        load_type = request.GET.get('load_type')

        if 'doe_reference_name' in request.GET.keys():
            doe_reference_name = [request.GET.get('doe_reference_name')]
            percent_share_list = [100.0]
        elif 'doe_reference_name[0]' in request.GET.keys():
            idx = 0
            doe_reference_name = []
            percent_share_list = []
            while 'doe_reference_name[{}]'.format(idx) in request.GET.keys():
                doe_reference_name.append(request.GET['doe_reference_name[{}]'.format(idx)])
                if 'percent_share[{}]'.format(idx) in request.GET.keys():
                    percent_share_list.append(float(request.GET['percent_share[{}]'.format(idx)]))
                idx += 1
        else:
            doe_reference_name = None

        if doe_reference_name is not None:
            if len(percent_share_list) != len(doe_reference_name):
                raise ValueError("The number of percent_share entries does not match that of the number of doe_reference_name entries")

            for drn in doe_reference_name:
                if drn not in BuiltInProfile.default_buildings:
                    raise ValueError("Invalid doe_reference_name - {}. Select from the following: {}"
                             .format(drn, BuiltInProfile.default_buildings))

        if load_type is None:
            load_type = 'electric'

        if latitude > 90 or latitude < -90:
            raise ValueError("latitude out of acceptable range (-90 <= latitude <= 90)")

        if longitude > 180 or longitude < -180:
            raise ValueError("longitude out of acceptable range (-180 <= longitude <= 180)")

        if load_type not in ['electric','heating','cooling']:
            raise ValueError("load_type parameter must be one of the folloing: 'heating', 'cooling', or 'electric'."
                             " If load_type is not specified, 'electric' is assumed.")

        if load_type == "electric":
            for key in request.GET.keys():
                if ('_mmbtu' in key) or ('_ton' in key) or ('_fraction' in key):
                    raise ValueError("Invalid key {} for load_type=electric".format(key))
            if doe_reference_name is None:
                raise ValueError("Please supply a doe_reference_name and optionally scaling parameters (annual_kwh or monthly_totals_kwh).")

            #Annual loads
            if 'annual_kwh' in request.GET.keys():
                annual_kwh = float(request.GET.get('annual_kwh'))
            else:
                annual_kwh = None

            #Monthly loads
            monthly_totals_kwh = None
            if 'monthly_totals_kwh[0]' in request.GET.keys():
                monthly_totals_kwh  = [request.GET.get('monthly_totals_kwh[{}]'.format(i)) for i in range(12)]
                if None in monthly_totals_kwh:
                    bad_index = monthly_totals_kwh.index(None)
                    raise ValueError("monthly_totals_kwh must contain a value for each month. {} is null".format('monthly_totals_kwh[{}]'.format(bad_index)))
                monthly_totals_kwh = [float(i) for i in monthly_totals_kwh]
            else:
                monthly_totals_kwh = None

            b = LoadProfile(dfm=None, latitude=latitude, longitude=longitude, doe_reference_name=doe_reference_name,
                           annual_kwh=annual_kwh, monthly_totals_kwh=monthly_totals_kwh, critical_load_pct=0,
                           percent_share=percent_share_list)

            lp = b.load_list

            response = JsonResponse(
                {'loads_kw': [round(ld, 3) for ld in lp],
                 'annual_kwh': b.annual_kwh,
                 'min_kw': round(min(lp), 3),
                 'mean_kw': round(sum(lp) / len(lp), 3),
                 'max_kw': round(max(lp), 3),
                 }
                )

            return response

        if load_type == "heating":
            for key in request.GET.keys():
                if ('_kw' in key) or ('_ton' in key): # or ('_fraction' in key):
                    raise ValueError("Invalid key {} for load_type=heating".format(key))
            
            if doe_reference_name is None:
                raise ValueError("Please supply a doe_reference_name and optional scaling parameters (annual_mmbtu or monthly_mmbtu).")

            #Annual loads
            if 'annual_mmbtu' in request.GET.keys():
                annual_mmbtu = float(request.GET.get('annual_mmbtu'))
            else:
                annual_mmbtu = None
                if len(percent_share_list) != len(doe_reference_name):
                    raise ValueError("The number of percent_share entries does not match that of the number of doe_reference_name entries")

            #Monthly loads
            if 'monthly_mmbtu' in request.GET.keys():
                string_array = request.GET.get('monthly_mmbtu')
                monthly_mmbtu = [float(v) for v in string_array.strip('[]').split(',')]
            elif 'monthly_mmbtu[0]' in request.GET.keys():
                monthly_mmbtu  = [request.GET.get('monthly_mmbtu[{}]'.format(i)) for i in range(12)]
                if None in monthly_mmbtu:
                    bad_index = monthly_mmbtu.index(None)
                    raise ValueError("monthly_mmbtu must contain a value for each month. {} is null".format('monthly_mmbtu[{}]'.format(bad_index)))
                monthly_mmbtu = [float(i) for i in monthly_mmbtu]
            else:
                monthly_mmbtu = None

            kwargs_heating = {}
            if 'addressable_load_fraction' in request.GET.keys():
                addressable_load_fraction = [float(request.GET.get('addressable_load_fraction'))]
            else:
                addressable_load_fraction = [nested_input_definitions["Scenario"]["Site"]["LoadProfileBoilerFuel"]["addressable_load_fraction"]["default"]]
            kwargs_heating["addressable_load_fraction"] = addressable_load_fraction

            if 'space_heating_fraction_of_heating_load' in request.GET.keys():
                space_heating_fraction_of_heating_load = [float(request.GET.get('space_heating_fraction_of_heating_load'))]
                kwargs_heating["space_heating_fraction_of_heating_load"] = space_heating_fraction_of_heating_load            

            b_space = LoadProfileBoilerFuel(load_type="SpaceHeating", dfm=None, latitude=latitude, longitude=longitude, doe_reference_name=doe_reference_name,
                           annual_mmbtu=annual_mmbtu, monthly_mmbtu=monthly_mmbtu, time_steps_per_hour=1,
                           percent_share=percent_share_list, **kwargs_heating)

            b_dhw = LoadProfileBoilerFuel(load_type="DHW", dfm=None, latitude=latitude, longitude=longitude, doe_reference_name=doe_reference_name,
                           annual_mmbtu=annual_mmbtu, monthly_mmbtu=monthly_mmbtu, time_steps_per_hour=1,
                           percent_share=percent_share_list, **kwargs_heating)            

            lp = [b_space.load_list[i] + b_dhw.load_list[i] for i in range(len(b_space.load_list))]

            response = JsonResponse(
                {'loads_mmbtu': [round(ld, 3) for ld in lp],
                 'annual_mmbtu': b_space.annual_mmbtu + b_dhw.annual_mmbtu,
                 'min_mmbtu': round(min(lp), 3),
                 'mean_mmbtu': round(sum(lp) / len(lp), 3),
                 'max_mmbtu': round(max(lp), 3),
                 'space_loads_mmbtu': [round(ld, 3) for ld in b_space.load_list],
                 'space_annual_mmbtu': b_space.annual_mmbtu,
                 'space_min_mmbtu': round(min(b_space.load_list), 3),
                 'space_mean_mmbtu': round(sum(b_space.load_list) / len(b_space.load_list), 3),
                 'space_max_mmbtu': round(max(b_space.load_list), 3),
                 'dhw_loads_mmbtu': [round(ld, 3) for ld in b_dhw.load_list],
                 'dhw_annual_mmbtu': b_dhw.annual_mmbtu,
                 'dhw_min_mmbtu': round(min(b_dhw.load_list), 3),
                 'dhw_mean_mmbtu': round(sum(b_dhw.load_list) / len(b_dhw.load_list), 3),
                 'dhw_max_mmbtu': round(max(b_dhw.load_list), 3),
                 }
                )

            return response

        if load_type == "cooling":
            for key in request.GET.keys():
                if ('_kw' in key) or ('_mmbtu' in key):
                    raise ValueError("Invalid key {} for load_type=heating".format(key))

            if request.GET.get('annual_fraction') is not None:  # annual_kwh is optional. if not provided, then DOE reference value is used.
                annual_fraction = float(request.GET['annual_fraction'])
                lp = [annual_fraction]*8760
                response = JsonResponse(
                    {'loads_fraction': [round(ld, 3) for ld in lp],
                     'annual_fraction': round(sum(lp) / len(lp), 3),
                     'min_fraction': round(min(lp), 3),
                     'mean_fraction': round(sum(lp) / len(lp), 3),
                     'max_fraction': round(max(lp), 3),
                     }
                    )
                return response

            if (request.GET.get('monthly_fraction') is not None) or (request.GET.get('monthly_fraction[0]') is not None):  # annual_kwh is optional. if not provided, then DOE reference value is used.
                if 'monthly_fraction' in request.GET.keys():
                    string_array = request.GET.get('monthly_fraction')
                    monthly_fraction = [float(v) for v in string_array.strip('[]').split(',')]
                elif 'monthly_fraction[0]' in request.GET.keys():
                    monthly_fraction  = [request.GET.get('monthly_fraction[{}]'.format(i)) for i in range(12)]
                    if None in monthly_fraction:
                        bad_index = monthly_fraction.index(None)
                        raise ValueError("monthly_fraction must contain a value for each month. {} is null".format('monthly_fraction[{}]'.format(bad_index)))
                    monthly_fraction = [float(i) for i in monthly_fraction]
                days_in_month = {   0:31,
                                    1:28,
                                    2:31,
                                    3:30,
                                    4:31,
                                    5:30,
                                    6:31,
                                    7:31,
                                    8:30,
                                    9:31,
                                    10:30,
                                    11:31}
                lp = []
                for i in range(12):
                    lp += [monthly_fraction[i]] * days_in_month[i] *24
                response = JsonResponse(
                    {'loads_fraction': [round(ld, 3) for ld in lp],
                     'annual_fraction': round(sum(lp) / len(lp), 3),
                     'min_fraction': round(min(lp), 3),
                     'mean_fraction': round(sum(lp) / len(lp), 3),
                     'max_fraction': round(max(lp), 3),
                     }
                    )
                return response

            if doe_reference_name is not None:
                #Annual loads
                if 'annual_tonhour' in request.GET.keys():
                    annual_tonhour = float(request.GET.get('annual_tonhour'))
                else:
                    annual_tonhour = None
                #Monthly loads
                if 'monthly_tonhour' in request.GET.keys():
                    string_array = request.GET.get('monthly_tonhour')
                    monthly_tonhour = [float(v) for v in string_array.strip('[]').split(',')]
                elif 'monthly_tonhour[0]' in request.GET.keys():
                    monthly_tonhour  = [request.GET.get('monthly_tonhour[{}]'.format(i)) for i in range(12)]
                    if None in monthly_tonhour:
                        bad_index = monthly_tonhour.index(None)
                        raise ValueError("monthly_tonhour must contain a value for each month. {} is null".format('monthly_tonhour[{}]'.format(bad_index)))
                    monthly_tonhour = [float(i) for i in monthly_tonhour]
                else:
                    monthly_tonhour = None

                chiller_cop = request.GET.get('chiller_cop')
                if chiller_cop is not None:
                    chiller_cop = float(chiller_cop)

                if 'max_thermal_factor_on_peak_load' in request.GET.keys():
                    max_thermal_factor_on_peak_load = float(request.GET.get('max_thermal_factor_on_peak_load'))
                else:
                    max_thermal_factor_on_peak_load = nested_input_definitions['Scenario']['Site']['ElectricChiller']['max_thermal_factor_on_peak_load']['default']

                c = LoadProfileChillerThermal(dfm=None, latitude=latitude, longitude=longitude, doe_reference_name=doe_reference_name,
                               annual_tonhour=annual_tonhour, monthly_tonhour=monthly_tonhour, time_steps_per_hour=1, annual_fraction=None,
                               monthly_fraction=None, percent_share=percent_share_list, max_thermal_factor_on_peak_load=max_thermal_factor_on_peak_load,
                               chiller_cop=chiller_cop)

                lp = c.load_list

                response = JsonResponse(
                    {'loads_ton': [round(ld/TONHOUR_TO_KWHT, 3) for ld in lp],
                     'annual_tonhour': round(c.annual_kwht/TONHOUR_TO_KWHT,3),
                     'chiller_cop': c.chiller_cop,
                     'min_ton': round(min(lp)/TONHOUR_TO_KWHT, 3),
                     'mean_ton': round((sum(lp)/len(lp))/TONHOUR_TO_KWHT, 3),
                     'max_ton': round(max(lp)/TONHOUR_TO_KWHT, 3),
                     }
                    )
                return response
            else:
                raise ValueError("Please supply a doe_reference_name and optional scaling parameters (annual_tonhour or monthly_tonhour), or annual_fraction, or monthly_fraction.")

    except KeyError as e:
        return JsonResponse({"Error. Missing": str(e.args[0])}, status=400)

    except ValueError as e:
        return JsonResponse({"Error": str(e.args[0])}, status=400)

    except Exception:

        exc_type, exc_value, exc_traceback = sys.exc_info()
        debug_msg = "exc_type: {}; exc_value: {}; exc_traceback: {}".format(exc_type, exc_value.args[0],
                                                                            tb.format_tb(exc_traceback))
        log.error(debug_msg)
        return JsonResponse({"Error": "Unexpected Error. Please check your input parameters and contact reopt@nrel.gov if problems persist."}, status=500)


def generator_efficiency(request):
    """
    From Navigant report / dieselfuelsupply.com, fitting a curve to the partial to full load points:

        CAPACITY RANGE      m [gal/kW]  b [gal]
        0 < C <= 40 kW      0.068       0.0125
        40 < C <= 80 kW     0.066       0.0142
        80 < C <= 150 kW    0.0644      0.0095
        150 < C <= 250 kW   0.0648      0.0067
        250 < C <= 750 kW   0.0656      0.0048
        750 < C <= 1500 kW  0.0657      0.0043
        1500 < C  kW        0.0657      0.004
    """
    try:
        generator_kw = float(request.GET['generator_kw'])  # need float to convert unicode

        if generator_kw <= 0:
            raise ValueError("Invalid generator_kw, must be greater than zero.")

        m, b = Generator.default_fuel_burn_rate(generator_kw)

        response = JsonResponse(
            {'slope_gal_per_kwh': m,
             'intercept_gal_per_hr': b,
             }
        )
        return response

    except ValueError as e:
        return JsonResponse({"Error": str(e.args[0])}, status=500)

    except Exception:

        exc_type, exc_value, exc_traceback = sys.exc_info()
        debug_msg = "exc_type: {}; exc_value: {}; exc_traceback: {}".format(exc_type, exc_value.args[0],
                                                                            tb.format_tb(exc_traceback))
        log.debug(debug_msg)
        return JsonResponse({"Error": "Unexpected error in generator_efficiency endpoint. Check log for more."}, status=500)


def chp_defaults(request):
    """
    Depending on the set of inputs, different sets of outputs are determine in addition to all CHP cost and performance parameter defaults:
        1. Inputs: existing_boiler_production_type_steam_or_hw and avg_boiler_fuel_load_mmbtu_per_hr
           Outputs: prime_mover, size_class, chp_size_based_on_avg_heating_load_kw
        2. Inputs: prime_mover and avg_boiler_fuel_load_mmbtu_per_hr
           Outputs: size_class
        3. Inputs: prime_mover and size_class
           Outputs: (uses default existing_boiler_production_type_steam_or_hw based on prime_mover to get default params)
        4. Inputs: prime_mover
           Outputs: (uses default size_class and existing_boiler_production_type_steam_or_hw based on prime_mover to get default params)
    
    The main purpose of this endpoint is to communicate the following table of dependency of CHP defaults versus 
        existing_boiler_production_type_steam_or_hw and avg_boiler_fuel_load_mmbtu_per_hr:
    If hot_water and <= 5 MWe chp_size_based_on_avg_heating_load_kw --> prime_mover = recip_engine of size_class X
    If hot_water and > 5 MWe chp_size_based_on_avg_heating_load_kw --> prime_mover = combustion_turbine of size_class X
    If steam and <= 2 MWe chp_size_based_on_avg_heating_load_kw --> prime_mover = recip_engine of size_class X
    If steam and > 2 MWe chp_size_based_on_avg_heating_load_kw --> prime_mover = combustion_turbine of size_class X

    Boiler efficiency is assumed for calculating chp_size_based_on_avg_heating_load_kw and may not be consistent with actual input value.
    """

    prime_mover_defaults_all = copy.deepcopy(CHP.prime_mover_defaults_all)
    n_classes = {pm: len(CHP.class_bounds[pm]) for pm in CHP.class_bounds.keys()}

    try:
        hw_or_steam = request.GET.get('existing_boiler_production_type_steam_or_hw')
        avg_boiler_fuel_load_mmbtu_per_hr = request.GET.get('avg_boiler_fuel_load_mmbtu_per_hr')
        prime_mover = request.GET.get('prime_mover')
        size_class = request.GET.get('size_class')

        if prime_mover is not None:  # Options 2, 3, or 4
            if hw_or_steam is None:  # Use default hw_or_steam based on prime_mover
                hw_or_steam = Boiler.boiler_type_by_chp_prime_mover_defaults[prime_mover]
        elif hw_or_steam is not None and avg_boiler_fuel_load_mmbtu_per_hr is not None:  # Option 1, determine prime_mover based on inputs
            if hw_or_steam not in ["hot_water", "steam"]:  # Validate user-entered hw_or_steam 
                raise ValueError("Invalid argument for existing_boiler_production_type_steam_or_hw; must be 'hot_water' or 'steam'")
        else:
            ValueError("Must provide either existing_boiler_production_type_steam_or_hw or prime_mover")

        # Need to numerically index thermal efficiency default on hot_water (0) or steam (1)
        hw_or_steam_index_dict = {"hot_water": 0, "steam": 1}
        hw_or_steam_index = hw_or_steam_index_dict[hw_or_steam]

        # Calculate heuristic CHP size based on average thermal load, using the default size class efficiency data
        avg_boiler_fuel_load_under_recip_over_ct = {"hot_water": 27.0, "steam": 7.0}  # [MMBtu/hr] Based on external calcs for size versus production by prime_mover type
        if avg_boiler_fuel_load_mmbtu_per_hr is not None:
            avg_boiler_fuel_load_mmbtu_per_hr = float(avg_boiler_fuel_load_mmbtu_per_hr)
            if prime_mover is None:
                if avg_boiler_fuel_load_mmbtu_per_hr <= avg_boiler_fuel_load_under_recip_over_ct[hw_or_steam]:
                    prime_mover = "recip_engine"  # Must make an initial guess at prime_mover to use those thermal and electric efficiency params to convert to size
                else:
                    prime_mover = "combustion_turbine"
            if size_class is None:
                size_class_calc = CHP.default_chp_size_class[prime_mover]
            else:
                size_class_calc = int(size_class)
            therm_effic = prime_mover_defaults_all[prime_mover]['thermal_effic_full_load'][hw_or_steam_index][size_class_calc]
            elec_effic = prime_mover_defaults_all[prime_mover]['elec_effic_full_load'][size_class_calc]
            boiler_effic = Boiler.boiler_efficiency_defaults[hw_or_steam]
            avg_heating_thermal_load_mmbtu_per_hr = avg_boiler_fuel_load_mmbtu_per_hr * boiler_effic
            chp_fuel_rate_mmbtu_per_hr = avg_heating_thermal_load_mmbtu_per_hr / therm_effic
            chp_elec_size_heuristic_kw = chp_fuel_rate_mmbtu_per_hr * elec_effic * 1.0E6 / 3412.0
        else:
            chp_elec_size_heuristic_kw = None
        
        # If size class is specified use that and ignore heuristic CHP sizing for determining size class
        if size_class is not None:
            size_class = int(size_class)
            if (size_class < 0) or (size_class >= n_classes[prime_mover]):
                raise ValueError('The size class input is outside the valid range for ' + str(prime_mover))
        # If size class is not specified, heuristic sizing based on avg thermal load and size class 0 efficiencies
        elif chp_elec_size_heuristic_kw is not None and size_class is None:
            # With heuristic size, find the suggested size class
            if chp_elec_size_heuristic_kw < CHP.class_bounds[prime_mover][1][1]:
                # If smaller than the upper bound of the smallest class, assign the smallest class
                size_class = 1
            elif chp_elec_size_heuristic_kw >= CHP.class_bounds[prime_mover][n_classes[prime_mover] - 1][0]:
                # If larger than or equal to the lower bound of the largest class, assign the largest class
                size_class = n_classes[prime_mover] - 1  # Size classes are zero-indexed
            else:
                # For middle size classes
                for sc in range(2, n_classes[prime_mover] - 1):
                    if (chp_elec_size_heuristic_kw >= CHP.class_bounds[prime_mover][sc][0]) and \
                            (chp_elec_size_heuristic_kw < CHP.class_bounds[prime_mover][sc][1]):
                        size_class = sc
        else:
            size_class = CHP.default_chp_size_class[prime_mover]
        
        prime_mover_defaults = CHP.get_chp_defaults(prime_mover, hw_or_steam, size_class)

        response = JsonResponse(
            {"prime_mover": prime_mover,
             "size_class": size_class,
             "hw_or_steam": hw_or_steam,
             "default_inputs": prime_mover_defaults,
             "chp_size_based_on_avg_heating_load_kw": chp_elec_size_heuristic_kw,
             "size_class_bounds": CHP.class_bounds
             }
        )
        return response

    except ValueError as e:
        return JsonResponse({"Error": str(e.args[0])}, status=500)

    except KeyError as e:
        return JsonResponse({"Error. Missing": str(e.args[0])}, status=500)

    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        debug_msg = "exc_type: {}; exc_value: {}; exc_traceback: {}".format(exc_type, exc_value.args[0],
                                                                            tb.format_tb(exc_traceback))
        log.debug(debug_msg)
        return JsonResponse({"Error": "Unexpected error in chp_defaults endpoint. Check log for more."}, status=500)


def loadprofile_chillerthermal_chiller_cop(request):
    """
    This provides the following default parameters for electric chiller:
        1. COP of electric chiller (LoadProfileChillerThermal.chiller_cop) based on peak cooling thermal load

    Required inputs:
        1. max_kw - max electric chiller electric load in kW

    Optional inputs:
        1. Max cooling capacity (ElectricChiller.max_thermal_factor_on_peak_load) as a ratio of peak cooling load
            a. If not entered, assume default (1.25)
    """

    try:
        max_kw = request.GET.get('max_kw')
        max_ton = request.GET.get('max_ton')
        if max_kw and max_ton:
            raise ValueError("Supplied both max_kw (electric) and max_ton (thermal), but should only supply one of them")
        elif max_kw:
            max_kw = float(max_kw)
        elif max_ton:
            max_ton = float(max_ton)
        else:
            raise ValueError("Missing either max_kw (electric) or max_ton (thermal) parameter")

        if 'max_thermal_factor_on_peak_load' in request.GET.keys():
            max_thermal_factor_on_peak_load = float(request.GET.get('max_thermal_factor_on_peak_load'))
        else:
            max_thermal_factor_on_peak_load = \
                nested_input_definitions['Scenario']['Site']['ElectricChiller']['max_thermal_factor_on_peak_load']['default']

        cop = LoadProfileChillerThermal.get_default_cop(max_thermal_factor_on_peak_load=max_thermal_factor_on_peak_load, max_kw=max_kw, max_ton=max_ton)
        response = JsonResponse(
            {   "chiller_cop": cop,
                "TONHOUR_TO_KWHT": TONHOUR_TO_KWHT
            }
        )
        return response

    except ValueError as e:
        return JsonResponse({"Error": str(e.args[0])}, status=500)

    except KeyError as e:
        return JsonResponse({"Error. Missing": str(e.args[0])}, status=500)

    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        debug_msg = "exc_type: {}; exc_value: {}; exc_traceback: {}".format(exc_type, exc_value.args[0],
                                                                            tb.format_tb(exc_traceback))
        log.debug(debug_msg)
        return JsonResponse({"Error": "Unexpected error in loadprofile_chillerthermal_chiller_cop endpoint. Check log for more."}, status=500)


def absorption_chiller_defaults(request):
    """
    This provides the following default parameters for the absorption chiller:
        1. COP of absorption chiller (AbsorptionChiller.chiller_cop) based on hot_water_or_steam input or prime_mover
        2. CapEx (AbsorptionChiller.installed_cost_us_dollars_per_ton) and
                OpEx (AbsorptionChiller.om_cost_us_dollars_per_ton) of absorption chiller based on peak cooling thermal
                load

    Required inputs:
        1. max_cooling_load_tons

    Optional inputs:
        1. hot_water_or_steam (Boiler.existing_boiler_production_type_steam_or_hw)
            a. If not provided, hot_water is assumed
        2. prime_mover (CHP.prime_mover)
            a. If hot_water_or_steam is provided, this is not used
            b. If hot_water_or_steam is NOT provided and prime_mover is, this will refer to
                Boiler.boiler_type_by_chp_prime_mover_defaults
    """
    try:
        max_cooling_load_tons = request.GET.get('max_cooling_load_tons')
        hot_water_or_steam = request.GET.get('hot_water_or_steam')
        prime_mover = request.GET.get('prime_mover')

        if max_cooling_load_tons is None:
            raise ValueError("Missing required max_cooling_load_tons query parameter.")
        else:
            # Absorption chiller COP
            absorp_chiller_cop = AbsorptionChiller.get_absorp_chiller_cop(hot_water_or_steam=hot_water_or_steam,
                                                                            chp_prime_mover=prime_mover)
            absorp_chiller_elec_cop = nested_input_definitions["Scenario"]["Site"]["AbsorptionChiller"]["chiller_elec_cop"]["default"]

            # Absorption chiller costs
            max_cooling_load_tons = float(max_cooling_load_tons)
            absorp_chiller_capex, \
            absorp_chiller_opex = \
            AbsorptionChiller.get_absorp_chiller_costs(max_cooling_load_tons,
                                                        hw_or_steam=hot_water_or_steam,
                                                        chp_prime_mover=prime_mover)

        response = JsonResponse(
            { "AbsorptionChiller": {
                "chiller_cop": absorp_chiller_cop,
                "chiller_elec_cop": absorp_chiller_elec_cop,
                "installed_cost_us_dollars_per_ton": absorp_chiller_capex,
                "om_cost_us_dollars_per_ton": absorp_chiller_opex
                }
            }
        )
        return response

    except ValueError as e:
        return JsonResponse({"Error": str(e.args[0])}, status=500)

    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        debug_msg = "exc_type: {}; exc_value: {}; exc_traceback: {}".format(exc_type, exc_value.args[0],
                                                                            tb.format_tb(exc_traceback))
        log.debug(debug_msg)
        return JsonResponse({"Error": "Unexpected error in absorption_chiller_defaults endpoint. Check log for more."}, status=500)


def schedule_stats(request):
    """
    Get a summary of a yearly profile by calculating the weekday, weekend, and total hours by month (e.g. for chp_unavailability_periods viewing in the UI)
    :param year: required input year for establishing the calendar
    :param chp_prime_mover: required if chp_unavailability_periods is not provided, otherwise not required or used
    :param chp_unavailability_periods: list of dictionaries, one dict per unavailability period (as defined in nested_inputs.py)
    :return formatted_datetime_periods: start and end dates of each period, formatted to ISO 8601 as YYYY-MM-DDThh
    :return weekday_weekend_total_hours_by_month: nested dictionary with 12 keys (one for each month) each being a dictionary of weekday_hours, weekend_hours, and total_hours
    """
    try:
        if request.method == "GET":
            if not (request.GET["year"] and request.GET["chp_prime_mover"]):
                ValueError("A GET request method is only applicable for getting the default stats using year and chp_prime_mover as query params")
            year = int(request.GET["year"])
            chp_prime_mover = request.GET["chp_prime_mover"]
            chp_unavailability_periods = None
        elif request.method == "POST":
            request_dict = json.loads(request.body)
            year = int(request_dict.get('year'))
            chp_prime_mover = request_dict.get('chp_prime_mover')
            chp_unavailability_periods = request_dict.get('chp_unavailability_periods')

        if chp_unavailability_periods is not None:  # Use chp_unavailability_periods and ignore CHP.prime_mover, if input
            used_default = False
            errors_chp_unavailability_periods = ValidateNestedInput.validate_chp_unavailability_periods(year, chp_unavailability_periods)
        elif chp_unavailability_periods is None and chp_prime_mover is not None:  # Use default chp_unavailability_periods which is dependent on CHP.prime_mover
            used_default = True
            errors_chp_unavailability_periods = []  # Don't need to check for errors in defaults, used as conditional below so need to define
            chp_unavailability_path = os.path.join('input_files', 'CHP', chp_prime_mover+'_unavailability_periods.csv')
            chp_unavailability_periods_df = pd.read_csv(chp_unavailability_path)
            chp_unavailability_periods = chp_unavailability_periods_df.to_dict('records')
        else:
            ValueError("Must provide chp_prime_mover for default chp_unavailability_periods if not providing chp_unavailability_periods")

        if errors_chp_unavailability_periods == []:
            chp_unavailability_hourly_list, start_day_of_month_list, errors_list = generate_year_profile_hourly(year, chp_unavailability_periods)
            weekday_weekend_total_hours_by_month = get_weekday_weekend_total_hours_by_month(year, chp_unavailability_hourly_list)
            formatted_datetime_periods = []
            for i, period in enumerate(chp_unavailability_periods):
                start_datetime = datetime(year=year, month=period['month'], day=start_day_of_month_list[i], hour=period['start_hour']-1)
                end_datetime = start_datetime + timedelta(hours=period['duration_hours'])
                formatted_datetime_periods.append({"start_datetime": start_datetime.strftime("%Y-%m-%dT%H:%M:%S"), 
                                                    "end_datetime": end_datetime.strftime("%Y-%m-%dT%H:%M:%S")})
        else:
            raise ValueError(" ".join(errors_chp_unavailability_periods))

        response = JsonResponse(
            {
                "providing_default_chp_unavailability_periods": used_default,
                "formatted_datetime_periods": formatted_datetime_periods,
                "weekday_weekend_total_hours_by_month": weekday_weekend_total_hours_by_month,
                "chp_unavailability_periods": chp_unavailability_periods
            }
        )
        return response

    except ValueError as e:
        return JsonResponse({"Error": str(e.args[0])}, status=400)

    except KeyError as e:
        return JsonResponse({"Error. Missing": str(e.args[0])}, status=400)

    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        debug_msg = "exc_type: {}; exc_value: {}; exc_traceback: {}".format(exc_type, exc_value.args[0],
                                                                            tb.format_tb(exc_traceback))
        log.debug(debug_msg)
        return JsonResponse({"Error": "Unexpected error in schedule_stats endpoint. Check log for more."}, status=500)

def ground_conductivity(request):
    """
    GET ground thermal conductivity based on the climate zone from the lat/long input
    param: latitude: latitude of the site location
    param: longitude: longitude of the site location
    return: Climate Zone: climate zone of the site location
    return: Thermal Conductivity [Btu/(hr-ft-degF)]: thermal conductivity of the ground in climate zone
    """
    try:
        latitude = float(request.GET['latitude'])  # need float to convert unicode
        longitude = float(request.GET['longitude'])

        climate_zone = get_climate_zone(latitude, longitude)
        k = ground_k_by_climate_zone.loc[climate_zone,"k"]

        response = JsonResponse(
            {
                "Climate Zone": climate_zone,
                "Thermal Conductivity": k
            }
        )
        return response

    except ValueError as e:
        return JsonResponse({"Error": str(e.args[0])}, status=400)

    except KeyError as e:
        return JsonResponse({"Error. Missing": str(e.args[0])}, status=400)

    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        debug_msg = "exc_type: {}; exc_value: {}; exc_traceback: {}".format(exc_type, exc_value.args[0],
                                                                            tb.format_tb(exc_traceback))
        log.debug(debug_msg)
        return JsonResponse({"Error": "Unexpected error in ground_conductivity endpoint. Check log for more."}, status=500)