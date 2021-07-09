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
import os
import copy
import math
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import namedtuple
from reo.utilities import degradation_factor
import logging
import geopandas as gpd
from shapely import geometry as g
from reo.exceptions import LoadProfileError
log = logging.getLogger(__name__)
import json

library_path_base = os.path.join('input_files', 'LoadProfiles')
load_type_file_map = {"Electric": "Load8760_norm_",
                        "SpaceHeating": "SpaceHeating8760_norm_",
                        "DHW": "DHW8760_norm_",
                        "Cooling": "Cooling8760_norm_"}

space_heating_annual_loads = json.load(open(os.path.join(library_path_base, "space_heating_annual_mmbtu.json"), "rb"))
dhw_annual_loads = json.load(open(os.path.join(library_path_base, "dhw_annual_mmbtu.json"), "rb"))
total_heating_annual_loads = {city: {building: space_heating_annual_loads[city][building] + dhw_annual_loads[city][building] for building in space_heating_annual_loads[city].keys()} for city in space_heating_annual_loads.keys()}
space_heating_fraction_flat_load = {city: space_heating_annual_loads[city]["flatload"] / total_heating_annual_loads[city]["flatload"] for city in space_heating_annual_loads.keys()}

default_annual_electric_loads = {
      "Albuquerque": {
        "fastfoodrest": 193235,
        "fullservicerest": 367661,
        "hospital": 8468546,
        "largehotel": 2407649,
        "largeoffice": 6303595,
        "mediumoffice": 884408,
        "midriseapartment": 269734,
        "outpatient": 1678720,
        "primaryschool": 1070908,
        "retailstore": 505417,
        "secondaryschool": 2588879,
        "smallhotel": 755373,
        "smalloffice": 87008,
        "stripmall": 497132,
        "supermarket": 1947654,
        "warehouse": 228939,
        "flatload": 1765929
      },
      "LasVegas": {
        "retailstore": 552267,
        "largehotel": 2751152,
        "mediumoffice": 959668,
        "stripmall": 546209,
        "primaryschool": 1196111,
        "warehouse": 235888,
        "smalloffice": 95801,
        "supermarket": 2001224,
        "midriseapartment": 332312,
        "fullservicerest": 372350,
        "outpatient": 1782941,
        "fastfoodrest": 208062,
        "smallhotel": 818012,
        "largeoffice": 6750393,
        "secondaryschool": 3112938,
        "hospital": 9011047,
        "flatload": 1920398
      },
      "Atlanta": {
        "fastfoodrest": 197467,
        "fullservicerest": 353750,
        "hospital": 9054747,
        "largehotel": 2649819,
        "largeoffice": 6995864,
        "mediumoffice": 929349,
        "midriseapartment": 285349,
        "outpatient": 1672434,
        "primaryschool": 1128702,
        "retailstore": 543340,
        "secondaryschool": 2849901,
        "smallhotel": 795777,
        "smalloffice": 90162,
        "stripmall": 529719,
        "supermarket": 2092966,
        "warehouse": 223009,
        "flatload": 1899522
      },
      "Baltimore": {
        "fastfoodrest": 192831,
        "fullservicerest": 341893,
        "hospital": 8895223,
        "largehotel": 2534272,
        "largeoffice": 6836130,
        "mediumoffice": 945425,
        "midriseapartment": 273225,
        "outpatient": 1623103,
        "primaryschool": 1077312,
        "retailstore": 510257,
        "secondaryschool": 2698987,
        "smallhotel": 767538,
        "smalloffice": 86112,
        "stripmall": 504715,
        "supermarket": 2018760,
        "warehouse": 229712,
        "flatload": 1845968
      },
      "Boulder": {
        "fastfoodrest": 189092,
        "fullservicerest": 334005,
        "hospital": 8281865,
        "largehotel": 2313151,
        "largeoffice": 6127030,
        "mediumoffice": 884726,
        "midriseapartment": 255428,
        "outpatient": 1621950,
        "primaryschool": 1018424,
        "retailstore": 504256,
        "secondaryschool": 2441588,
        "smallhotel": 736174,
        "smalloffice": 84900,
        "stripmall": 495018,
        "supermarket": 1956244,
        "warehouse": 243615,
        "flatload": 1717967
      },
      "Chicago": {
        "fastfoodrest": 189558,
        "fullservicerest": 333659,
        "hospital": 8567087,
        "largehotel": 2402021,
        "largeoffice": 6369028,
        "mediumoffice": 972772,
        "midriseapartment": 265528,
        "outpatient": 1587062,
        "primaryschool": 1045477,
        "retailstore": 513106,
        "secondaryschool": 2568086,
        "smallhotel": 759657,
        "smalloffice": 86224,
        "stripmall": 506886,
        "supermarket": 2025507,
        "warehouse": 245750,
        "flatload": 1777338
      },
      "Duluth": {
        "fastfoodrest": 183713,
        "fullservicerest": 318867,
        "hospital": 8134328,
        "largehotel": 2231678,
        "largeoffice": 6036003,
        "mediumoffice": 1032533,
        "midriseapartment": 256393,
        "outpatient": 1534322,
        "primaryschool": 982163,
        "retailstore": 532503,
        "secondaryschool": 2333466,
        "smallhotel": 752284,
        "smalloffice": 83759,
        "stripmall": 500979,
        "supermarket": 1980986,
        "warehouse": 256575,
        "flatload": 1696910
      },
      "Fairbanks": {
        "fastfoodrest": 182495,
        "fullservicerest": 314760,
        "hospital": 7899166,
        "largehotel": 2181664,
        "largeoffice": 5956232,
        "mediumoffice": 1267132,
        "midriseapartment": 271840,
        "outpatient": 1620270,
        "primaryschool": 986128,
        "retailstore": 573411,
        "secondaryschool": 2344790,
        "smallhotel": 831480,
        "smalloffice": 86614,
        "stripmall": 545421,
        "supermarket": 2033295,
        "warehouse": 285064,
        "flatload": 1711235
      },
      "Helena": {
        "fastfoodrest": 185877,
        "fullservicerest": 325263,
        "hospital": 8068698,
        "largehotel": 2246239,
        "largeoffice": 6003137,
        "mediumoffice": 930630,
        "midriseapartment": 252659,
        "outpatient": 1568262,
        "primaryschool": 994496,
        "retailstore": 534933,
        "secondaryschool": 2357548,
        "smallhotel": 729797,
        "smalloffice": 84219,
        "stripmall": 503504,
        "supermarket": 1969137,
        "warehouse": 252245,
        "flatload": 1687915
      },
      "Houston": {
        "fastfoodrest": 210283,
        "fullservicerest": 383987,
        "hospital": 9634661,
        "largehotel": 3050370,
        "largeoffice": 7539308,
        "mediumoffice": 972535,
        "midriseapartment": 335063,
        "outpatient": 1756541,
        "primaryschool": 1258146,
        "retailstore": 589419,
        "secondaryschool": 3421024,
        "smallhotel": 863952,
        "smalloffice": 98508,
        "stripmall": 577987,
        "supermarket": 2225265,
        "warehouse": 221593,
        "flatload": 2071165
      },
      "LosAngeles": {
        "fastfoodrest": 188857,
        "fullservicerest": 352240,
        "hospital": 8498389,
        "largehotel": 2458786,
        "largeoffice": 6642784,
        "mediumoffice": 846742,
        "midriseapartment": 248028,
        "outpatient": 1565008,
        "primaryschool": 1095263,
        "retailstore": 486188,
        "secondaryschool": 2584380,
        "smallhotel": 751880,
        "smalloffice": 86655,
        "stripmall": 491972,
        "supermarket": 1935886,
        "warehouse": 182085,
        "flatload": 1775946
      },
      "Miami": {
        "fastfoodrest": 224494,
        "fullservicerest": 448713,
        "hospital": 10062043,
        "largehotel": 3437188,
        "largeoffice": 8002063,
        "mediumoffice": 1021224,
        "midriseapartment": 424956,
        "outpatient": 1929148,
        "primaryschool": 1426635,
        "retailstore": 635086,
        "secondaryschool": 4074081,
        "smallhotel": 972090,
        "smalloffice": 108279,
        "stripmall": 675793,
        "supermarket": 2260929,
        "warehouse": 202082,
        "flatload": 2244050
      },
      "Minneapolis": {
        "fastfoodrest": 188368,
        "fullservicerest": 330920,
        "hospital": 8425063,
        "largehotel": 2378872,
        "largeoffice": 6306693,
        "mediumoffice": 1005875,
        "midriseapartment": 267383,
        "outpatient": 1582701,
        "primaryschool": 1022667,
        "retailstore": 539203,
        "secondaryschool": 2498647,
        "smallhotel": 774571,
        "smalloffice": 85921,
        "stripmall": 511567,
        "supermarket": 2034650,
        "warehouse": 249332,
        "flatload": 1762652
      },
      "Phoenix": {
        "fastfoodrest": 216088,
        "fullservicerest": 389739,
        "hospital": 9265786,
        "largehotel": 2990053,
        "largeoffice": 7211666,
        "mediumoffice": 1004988,
        "midriseapartment": 378378,
        "outpatient": 1849358,
        "primaryschool": 1289084,
        "retailstore": 593924,
        "secondaryschool": 3503727,
        "smallhotel": 881843,
        "smalloffice": 104583,
        "stripmall": 590954,
        "supermarket": 2056195,
        "warehouse": 241585,
        "flatload": 2035497
      },
      "SanFrancisco": {
        "fastfoodrest": 183953,
        "fullservicerest": 317124,
        "hospital": 7752817,
        "largehotel": 2206880,
        "largeoffice": 6085403,
        "mediumoffice": 792199,
        "midriseapartment": 229671,
        "outpatient": 1394447,
        "primaryschool": 1009369,
        "retailstore": 449025,
        "secondaryschool": 2327074,
        "smallhotel": 698095,
        "smalloffice": 78132,
        "stripmall": 455802,
        "supermarket": 1841655,
        "warehouse": 185889,
        "flatload": 1625471
      },
      "Seattle": {
        "fastfoodrest": 184142,
        "fullservicerest": 318741,
        "hospital": 7912504,
        "largehotel": 2212410,
        "largeoffice": 6019271,
        "mediumoffice": 878390,
        "midriseapartment": 237242,
        "outpatient": 1434195,
        "primaryschool": 983498,
        "retailstore": 455854,
        "secondaryschool": 2282972,
        "smallhotel": 693921,
        "smalloffice": 79716,
        "stripmall": 460449,
        "supermarket": 1868973,
        "warehouse": 210300,
        "flatload": 1639536
      }
    }


def bau_outage_check(critical_loads_kw, existing_pv_kw_list, gen_existing_kw, gen_min_turn_down,
                     fuel_gal, fuel_slope, fuel_intercept, time_steps_per_hour):
    """
    Determine if existing generator and/or PV can meet critical load and for how long
    :param critical_loads_kw: list of float, length same as outage
    :param existing_pv_kw_list:  list of float, length same as outage, existing pv production
    :param gen_existing_kw: float, generator capacity
    :param gen_min_turn_down: float zero to one
    :param fuel_gal: float, gallons of fuel available
    :param fuel_slope: float, gallons/kWh
    :param fuel_intercept: float, gallons
    :param time_steps_per_hour: int
    :return: bool, int for number of time steps the existing generator and PV can meet the critical load, and
        boolean for if the entire critical load is met
    """
    if gen_existing_kw == 0 and existing_pv_kw_list in [None, []]:
        return False, 0

    elif gen_existing_kw > 0:
        if existing_pv_kw_list in [None, []]:
            existing_pv_kw_list = [0] * len(critical_loads_kw)

        for i, (load, pv) in enumerate(zip(critical_loads_kw, existing_pv_kw_list)):
            unmet = load - pv
            if unmet > 0:
                fuel_kwh = (fuel_gal - fuel_intercept) / fuel_slope
                gen_avail = min(fuel_kwh, gen_existing_kw * (1.0 / time_steps_per_hour))
                gen_output = max(min(unmet, gen_avail), gen_min_turn_down * gen_existing_kw)
                fuel_needed = fuel_intercept + fuel_slope * gen_output
                fuel_gal -= fuel_needed

                if gen_output < unmet:
                    return False, i

    else:  # gen_existing_kw = 0 and PV_existing_kw > 0
        for i, (load, pv) in enumerate(zip(critical_loads_kw, existing_pv_kw_list)):
            unmet = load - pv
            if unmet > 0:
                return False, i

    return True, len(critical_loads_kw)


class BuiltInProfile(object):

    Default_city = namedtuple("Default_city", "name lat lng tmyid zoneid")
    default_cities = [
        Default_city('Miami', 25.761680, -80.191790, 722020, '1A'),
        Default_city('Houston', 29.760427, -95.369803, 722430, '2A'),
        Default_city('Phoenix', 33.448377, -112.074037, 722780, '2B'),
        Default_city('Atlanta', 33.748995, -84.387982, 722190, '3A'),
        Default_city('LasVegas', 36.1699, -115.1398, 723677, '3B'),
        Default_city('LosAngeles', 34.052234, -118.243685, 722950, '3B'),
        Default_city('SanFrancisco', 37.3382, -121.8863, 724940, '3C'),
        Default_city('Baltimore', 39.290385, -76.612189, 724060, '4A'),
        Default_city('Albuquerque', 35.085334, -106.605553, 723650, '4B'),
        Default_city('Seattle', 47.606209, -122.332071, 727930, '4C'),
        Default_city('Chicago', 41.878114, -87.629798, 725300, '5A'),
        Default_city('Boulder', 40.014986, -105.270546, 724699, '5B'),
        Default_city('Minneapolis', 44.977753, -93.265011, 726580, '6A'),
        Default_city('Helena', 46.588371, -112.024505, 727720, '6B'),
        Default_city('Duluth', 46.786672, -92.100485, 727450, '7'),
        Default_city('Fairbanks', 59.0397, -158.4575, 702610, '8'),
    ]
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
                         'FlatLoad',
                         'FlatLoad_24_5',
                         'FlatLoad_16_7',
                         'FlatLoad_16_5',
                         'FlatLoad_8_7',
                         'FlatLoad_8_5'
                         ]

    def __init__(self, annual_loads=default_annual_electric_loads, load_type='Electric',
                 latitude=None, longitude=None, doe_reference_name='', annual_energy=None,
                 monthly_totals_energy=None, **kwargs):
        """
        :param latitude: float
        :param longitude: float
        :param annual_energy: float or int
        :param monthly_totals_energy: list of 12 floats for monthly energy sums
        :param doe_reference_name: building type chosen by user
        :param year: year of load profile, needed for monthly scaling
        :param kwargs:
        """
        self.load_type = load_type
        self.library_path = os.path.join(library_path_base, self.load_type)
        self.builtin_profile_prefix = load_type_file_map[self.load_type]
        self.flatload_alternate_options = ['FlatLoad_24_5','FlatLoad_16_7','FlatLoad_16_5','FlatLoad_8_7','FlatLoad_8_5']
        self.annual_loads = annual_loads  # a dictionary of cities and default annual loads or a constant value for any city
        self.latitude = float(latitude) if latitude is not None else None
        self.longitude = float(longitude) if longitude is not None else None
        self.monthly_energy = monthly_totals_energy
        self.doe_reference_name = doe_reference_name
        self.nearest_city = None
        self.year = 2017
        self.annual_energy = annual_energy if annual_energy is not None else (
            sum(monthly_totals_energy) if monthly_totals_energy else self.default_annual_energy)
        self.annual_kwh = round(self.annual_energy,0)
        self.user_entered_space_heating_fraction = kwargs.get("space_heating_fraction")
        

    @property
    def built_in_profile(self):
        if self.monthly_energy in [None, []]:
            if self.doe_reference_name in ['FlatLoad'] + self.flatload_alternate_options:
                return [ld * self.annual_energy * self.heating_fraction[0] for ld in self.custom_normalized_flatload]            
            else:
                return [ld * self.annual_energy for ld in self.normalized_profile]
        return self.monthly_scaled_profile

    @property
    def city(self):
        if self.nearest_city is None:
            # try shapefile lookup
            log.info("Trying city lookup by shapefile.")
            gdf = gpd.read_file('reo/src/data/climate_cities.shp')
            gdf = gdf[gdf.geometry.intersects(g.Point(self.longitude, self.latitude))]
            if not gdf.empty:
                self.nearest_city = gdf.city.values[0].replace(' ', '')
            if self.nearest_city is None:
                cities_to_search = self.default_cities
            else:
                climate_zone = [c for c in self.default_cities if c.name==self.nearest_city][0].zoneid                
                cities_to_search = [c for c in self.default_cities if c.zoneid ==climate_zone]
            if len(cities_to_search) > 1:
                # else use old geometric approach, never fails...but isn't necessarily correct
                log.info("Using geometrically nearest city to lat/lng.")
                min_distance = None
                for i, c in enumerate(cities_to_search):
                    distance = math.sqrt((self.latitude - c.lat) ** 2 + (self.longitude - c.lng) ** 2)
                    if i == 0:
                        min_distance = distance
                        self.nearest_city = c.name
                    elif distance < min_distance:
                        min_distance = distance
                        self.nearest_city = c.name
        return self.nearest_city

    @property
    def default_annual_energy(self):
        building = self.building_type.lower()
        if building.startswith('flatload'):
            building = 'flatload'
        return self.annual_loads[self.city][building]

    @property
    def building_type(self):
        name = self.doe_reference_name.replace(' ', '')
        if (name not in self.default_buildings) and (name not in self.flatload_alternate_options):
            raise AttributeError(
                "load_profile error. Invalid doe_reference_name. Select from the following:\n{}".format(
                    self.default_buildings + self.flatload_alternate_options))
        return name

    @property
    def custom_normalized_flatload(self):
        # built in profiles are assumed to be hourly
        periods = 8760
        # get datetimes of all hours 
        series = pd.date_range(start=datetime(self.year, 1, 1, 0), end=datetime(self.year, 12, 31, 23), freq='h')

        # clip last day if a leap year
        series = series[:periods]
        
        # create boolean masks for weekday and hour of day filters
        if self.doe_reference_name in ['FlatLoad_24_5','FlatLoad_16_5','FlatLoad_8_5']:
            weekends = [5,6]
            weekday_mask = [i.weekday() not in weekends for i in series]
        else:
            weekday_mask = [True for i in series]
        if self.doe_reference_name in ['FlatLoad_16_5','FlatLoad_16_7']:
            hour_range = range(6,22)
            hour_mask = [i.hour in hour_range for i in series]
        elif self.doe_reference_name in ['FlatLoad_8_5','FlatLoad_8_7']:
            hour_range = range(9,17)
            hour_mask = [i.hour in hour_range for i in series]
        else:
            hour_mask = [True for i in series]
        # combine masks to a series where 1 is on and 0 is off
        series_binary = [int(i) for i in (np.array(weekday_mask) & np.array(hour_mask))]
        # convert combined masks to a normalized profile
        sum_series_binary = sum(series_binary)
        normalized_profile = [i/sum_series_binary for i in series_binary]
        return normalized_profile

    @property
    def monthly_scaled_profile(self):

        load_profile = []

        datetime_current = datetime(self.year, 1, 1, 0)
        month_total = 0
        month_scale_factor = []

        if self.doe_reference_name in ['FlatLoad'] + self.flatload_alternate_options:
            normalized_profile = self.custom_normalized_flatload
        else:
            normalized_profile = self.normalized_profile
        
        for load in normalized_profile:
            month = datetime_current.month
            # Monthly total based on annual_energy (sum of monthly_energy) and the normalized profile, later used to scale actual monthly energy
            month_total += self.annual_energy * load

            # add an hour
            datetime_current = datetime_current + timedelta(0, 0, 0, 0, 0, 1, 0)

            if month != datetime_current.month:
                if month_total == 0:
                    month_scale_factor.append(0)
                else:
                    month_scale_factor.append(float(self.monthly_energy[month - 1] / month_total * self.heating_fraction[month - 1]))
                month_total = 0

        datetime_current = datetime(self.year, 1, 1, 0)

        for load in normalized_profile:
            month = datetime_current.month

            load_profile.append(self.annual_energy * load * month_scale_factor[month - 1])

            # add an hour
            datetime_current = datetime_current + timedelta(0, 0, 0, 0, 0, 1, 0)

        return load_profile

    @property
    def normalized_profile(self):
        profile_path = os.path.join(self.library_path,
                                    self.builtin_profile_prefix + self.city + "_" + self.building_type + ".dat")
        normalized_profile = list()
        f = open(profile_path, 'r')
        for line in f:
            normalized_profile.append(float(line.strip('\n')))

        return normalized_profile

    @property
    def heating_fraction(self):
        if self.load_type == "SpaceHeating":
            if self.user_entered_space_heating_fraction in [None, []]:
                heating_fraction = [space_heating_fraction_flat_load[self.city] for _ in range(12)]
            elif len(self.user_entered_space_heating_fraction) == 1:
                heating_fraction = [self.user_entered_space_heating_fraction[0] for _ in range(12)]
            else:
                heating_fraction = self.user_entered_space_heating_fraction
        elif self.load_type == "DHW":            
            if self.user_entered_space_heating_fraction in [None, []]:
                heating_fraction = [1.0 - space_heating_fraction_flat_load[self.city] for _ in range(12)]
            elif len(self.user_entered_space_heating_fraction) == 1:
                heating_fraction = [1.0 - self.user_entered_space_heating_fraction[0] for _ in range(12)]
            else:
                heating_fraction = [1.0 - self.user_entered_space_heating_fraction[i] for i in range(12)]
        else:
            # Electric and Cooling loads use this fraction of 1.0 to make irrelevant
            heating_fraction = [1.0] * 12
        
        return heating_fraction

class LoadProfile(BuiltInProfile):
    """
    Important notes regarding different load profiles (from user's perspective):

    There are four different load profiles, two within the inputs, which can be net or native:

        1. "loads_kw" == typical site load optionally uploaded by user (8760), can be None
        2. "critical_loads_kw" == site critical load optionally uploaded by user(8760), can be None

    And two within the outputs:
        3. "year_one_electric_load_series_kw" == typical load with critical load inserted during outage (8760).
            For scenarios without outages, this series is the same as #1 if user uploads,  or the built-in profile.
        4. "critical_load_series_kw" == critical load for outage simulator. Same as #2 if user uploads, else
            it is determined as either "loads_kw" or built-in profile times the "critical_load_pct".
    """

    def __init__(self, dfm=None, user_profile=None, pvs=[], critical_loads_kw=None, critical_load_pct=None,
                 outage_start_time_step=None, outage_end_time_step=None, loads_kw_is_net=True, critical_loads_kw_is_net=False,
                 analysis_years=1, time_steps_per_hour=1, gen_existing_kw=0, gen_min_turn_down=0,
                 fuel_avail_before_outage=0, fuel_slope=1, fuel_intercept=0, **kwargs):

        self.time_steps_per_hour = time_steps_per_hour
        self.n_timesteps = self.time_steps_per_hour * 8760
        self.doe_reference_name = kwargs.get('doe_reference_name')
        self.nearest_city = None
        self.year = kwargs.get('year')
        # "pop"ing the following two values to replace them before calling BuiltInProfile (super class)
        doe_reference_name_list = kwargs.pop("doe_reference_name", [])
        self.annual_kwh = kwargs.pop("annual_kwh", None)

        if user_profile:
            self.load_list = user_profile
            self.unmodified_load_list = copy.copy(self.load_list)
            self.bau_load_list = copy.copy(self.load_list)

        else:  # building type and (annual_kwh OR monthly_totals_energy) defined by user
            if len(doe_reference_name_list) == 0:
                message = ("Invalid LoadProfile inputs. At a minimum, please supply a loads_kw or doe_reference_name.")
                log.error("Scenario.py raising error: " + message)
                lp_error = LoadProfileError(task='reo.src.load_profile.py', run_uuid=dfm.run_id, user_uuid=dfm.user_id, message=message)
                lp_error.save_to_db()
                raise lp_error

            else:
                combine_loadlist = []
                for i in range(len(doe_reference_name_list)):
                    kwargs["doe_reference_name"] = doe_reference_name_list[i]
                    if self.annual_kwh is not None:
                        kwargs["annual_energy"] = self.annual_kwh
                    if len(doe_reference_name_list[i])>1:
                        kwargs['monthly_totals_energy'] = kwargs.get('monthly_totals_kwh')
                    super(LoadProfile, self).__init__(**kwargs)
                    if self.time_steps_per_hour > 1:
                        load_list = [val for val in self.built_in_profile for _ in range(self.time_steps_per_hour)]
                    else:
                        load_list = self.built_in_profile 
                    combine_loadlist.append(load_list)

                # In the case where the user supplies a list of doe_reference_names and percent shares
                # for consistency we want to act as if we had scaled the partial load to the total site 
                # load which was unknown at the start of the loop above. This scalar makes it such that
                # when the percent shares are later applied that the total site load will be the sum
                # of the default annual loads for this location
                if (len(doe_reference_name_list) > 1) and self.annual_kwh is None:
                    total_site_load = sum([sum(l) for l in combine_loadlist])
                    for i, load in enumerate(combine_loadlist):
                        actual_percent_of_site_load = sum(load)/total_site_load
                        scalar = 1.0 / actual_percent_of_site_load
                        combine_loadlist[i] = list(np.array(load)* scalar)
                
                # Apply the percent share of annual load to each partial load
                if (len(doe_reference_name_list) > 1):
                    for i,load in enumerate(combine_loadlist):
                        combine_loadlist[i] = (np.array(load) * (kwargs.get("percent_share")[i]/100.0)).tolist()
                
                # Aggregate total hybrid load
                self.unmodified_load_list = (np.sum(np.array(combine_loadlist), axis=0)).tolist()

        if loads_kw_is_net:
            self.load_list, existing_pv_kw_list = self._account_for_existing_pv(pvs, analysis_years)
        else:
            self.load_list = copy.copy(self.unmodified_load_list)
            existing_pv_kw_list = None
        self.bau_load_list = copy.copy(self.load_list)
        """
        Account for outage in load_list (loads_kw).
            1. if user provides critical_loads_kw then splice it into load_list during outage.
            2. if user DOES NOT provide critical_loads_kw, use critical_load_pct to scale load_list during outage.
        In both cases, if existing PV and load is net then add existing PV to critical_loads_kw.
        """
        outage_with_user_crit_load = all(x not in [critical_loads_kw, outage_start_time_step, outage_end_time_step]
                                          for x in [None, []])
        outage_with_crit_load_pct = None not in [critical_load_pct, outage_start_time_step, outage_end_time_step]

        if outage_with_user_crit_load:

            if existing_pv_kw_list is not None and critical_loads_kw_is_net:
                # Add existing pv in if net critical load provided
                for i, p in enumerate(existing_pv_kw_list):
                    critical_loads_kw[i] += p
            if existing_pv_kw_list is not None:
                existing_pv_kw_list = existing_pv_kw_list[outage_start_time_step - 1:outage_end_time_step]

        elif outage_with_crit_load_pct:  # use native_load * critical_load_pct

            if existing_pv_kw_list not in [None, []]:
                existing_pv_kw_list = existing_pv_kw_list[outage_start_time_step - 1:outage_end_time_step]
                
            critical_loads_kw = [ld * critical_load_pct for ld in self.load_list]
            # Note: existing PV accounted for in load_list

        elif critical_loads_kw not in [None, []]:
            """
             This elif is handling the case when a user uploads a critical load profile for resilience analysis and the
             financial run needs to pick up on the same critical load series for apple-to-apple comparison in the
             outage-simulation stage. (This is a web app specific use-case)
            """
            resilience_check_flag = True
            bau_sustained_time_steps = 0 # no outage

        else:  # missing outage_start_time_step, outage_end_time_step, or critical_load_kw => no specified outage
            critical_loads_kw = [critical_load_pct * ld for ld in self.unmodified_load_list]
            resilience_check_flag = True
            bau_sustained_time_steps = 0  # no outage

        if outage_with_crit_load_pct or outage_with_crit_load_pct:

            # splice critical loads in to load_list (used in optimal case)
            self.load_list[outage_start_time_step - 1:outage_end_time_step] = \
                critical_loads_kw[outage_start_time_step - 1:outage_end_time_step]

            # replace bau load with zeros during outage
            self.bau_load_list[outage_start_time_step - 1:outage_end_time_step] = \
                [0.0 for _ in critical_loads_kw[outage_start_time_step - 1:outage_end_time_step]]

            resilience_check_flag, bau_sustained_time_steps = \
                bau_outage_check(critical_loads_kw[outage_start_time_step - 1:outage_end_time_step],
                                    existing_pv_kw_list, gen_existing_kw, gen_min_turn_down,
                                    fuel_avail_before_outage, fuel_slope, fuel_intercept,
                                    self.time_steps_per_hour)

            if bau_sustained_time_steps > 0:  # include critical load in bau load for the time that it can be met
                self.bau_load_list[outage_start_time_step:outage_start_time_step+bau_sustained_time_steps] = \
                    critical_loads_kw[outage_start_time_step:outage_start_time_step+bau_sustained_time_steps]

        # resilience_check_flag: True if existing diesel and/or PV can sustain critical load during outage
        self.resilience_check_flag = resilience_check_flag
        self.bau_sustained_time_steps = bau_sustained_time_steps
        self.annual_kwh = int(round(sum(self.load_list), 0))
        self.bau_annual_kwh = int(round(sum(self.bau_load_list), 0))
        self.loads_kw_is_net = loads_kw_is_net
        self.critical_loads_kw_is_net = critical_loads_kw_is_net
        self.critical_load_series_kw = critical_loads_kw

        if dfm is not None:
            dfm.add_load(self)

    def _account_for_existing_pv(self, pvs, years):
        # account for existing PV in load profile if loads_kw_is_net
        existing_pv_kw_list = None
        for pv in pvs:  # get all of the existing production
            if pv is not None:
                if pv.existing_kw > 0:
                    """
                    Create existing PV profile.
                    Must account for levelization factor to align with how PV is modeled in REopt:
                    Because we only model one year, we multiply the "year 1" PV production by a levelization_factor
                    that accounts for the PV capacity degradation over the analysis_years. In other words, by
                    multiplying the pv.prod_factor by the levelization_factor we are modeling the average pv production.
                    """
                    levelization_factor = round(degradation_factor(years, pv.degradation_pct), 5)
                    # for first PV just override the existing_pv_kw_list, otherwise add to existing production
                    new_existing_pv_kw_list = [pv.existing_kw * x * levelization_factor for x in pv.prod_factor]
                    if existing_pv_kw_list is None:
                        existing_pv_kw_list = new_existing_pv_kw_list
                    else:
                        existing_pv_kw_list = [i + j for i, j in zip(new_existing_pv_kw_list, existing_pv_kw_list)]
        if existing_pv_kw_list is not None:
            # add existing pv to load profile to create native load from net load
            native_load = [i + j for i, j in zip(self.unmodified_load_list, existing_pv_kw_list)]
            return native_load, existing_pv_kw_list
        return copy.copy(self.unmodified_load_list), existing_pv_kw_list

def get_climate_zone(latitude, longitude):
    gdf = gpd.read_file('reo/src/data/climate_cities.shp')
    gdf = gdf[gdf.geometry.intersects(g.Point(longitude, latitude))]
    if not gdf.empty:
        nearest_city = gdf.city.values[0].replace(' ', '')
    if nearest_city is None:
        cities_to_search = BuiltInProfile.default_cities
    else:
        climate_zone = [c for c in BuiltInProfile.default_cities if c.name==nearest_city][0].zoneid
        cities_to_search = [c for c in BuiltInProfile.default_cities if c.zoneid==climate_zone]
    if len(cities_to_search) > 1:
        # else use old geometric approach, never fails...but isn't necessarily correct
        min_distance = None
        for i, c in enumerate(cities_to_search):
            distance = math.sqrt((latitude - c.lat) ** 2 + (longitude - c.lng) ** 2)
            if i == 0:
                min_distance = distance
                nearest_city = c.name
            elif distance < min_distance:
                min_distance = distance
                nearest_city = c.name
    
    climate_zone = [c for c in BuiltInProfile.default_cities if c.name==nearest_city][0].zoneid

    return climate_zone