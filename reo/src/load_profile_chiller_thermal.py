from reo.src.load_profile import library_path_base, BuiltInProfile
import os
import json
import pandas as pd
import numpy as np
from datetime import datetime
from reo.utilities import TONHOUR_TO_KWHT


class LoadProfileChillerThermal(BuiltInProfile):
    """
    Chiller Load Profiles based on CRB defined load shapes or user-defined input
    """
    
    with open(os.path.join(library_path_base, 'reference_cooling_kwh.json'), 'r') as f:
        annual_loads = json.loads(f.read())

    builtin_profile_prefix = "Cooling8760_norm_"

    electric_chiller_cop_defaults = {   "convert_elec_to_thermal": 4.55,
                                            "less_than_100_tons": 4.40,
                                            "greater_than_100_tons": 4.69}
    @staticmethod
    def get_default_cop(max_thermal_factor_on_peak_load, max_kw=None, max_kwt=None, max_ton=None):
        if max_ton is not None:
            max_cooling_load_tons = max_ton
        elif max_kwt is not None:
            max_cooling_load_tons = max_kwt / TONHOUR_TO_KWHT
        elif max_kw is not None:
            max_cooling_load_tons = max_kw / TONHOUR_TO_KWHT * \
                                LoadProfileChillerThermal.electric_chiller_cop_defaults["convert_elec_to_thermal"]
        else:
            raise Exception("Please supply a max_ton, max_kwt or max_kw value")
        estimated_max_chiller_thermal_capacity_tons = max_cooling_load_tons * max_thermal_factor_on_peak_load
        if estimated_max_chiller_thermal_capacity_tons < 100.0:
            return LoadProfileChillerThermal.electric_chiller_cop_defaults["less_than_100_tons"]
        else:
            return LoadProfileChillerThermal.electric_chiller_cop_defaults["greater_than_100_tons"]

    def __init__(self, load_type="Cooling", dfm=None, total_electric_load_list=[], latitude=None, longitude=None, nearest_city=None,
                        time_steps_per_hour=None, year=None, chiller_cop=None, max_thermal_factor_on_peak_load=None, **kwargs):
        """
        :param dfm: (object) data_manager to which this load object will be added
        :param total_electric_load_list: (array) electric LoadProfile object resulting from parsed inputs
        :param latitude: (float) site latitude
        :param longitude: (float) site longitude
        :param nearest_city: (str) site nearest_city
        :param time_steps_per_hour: (int) simulation time resolution
        :param year: (int) electric LoadProfile year
        :param chiller_cop: (float or int) Coefficient of Performance for Chiller
        :param max_thermal_factor_on_peak_load: (float or int) maximum thermal factor on peak load for the Chiller
        :param kwargs: (dict) LoadProfileChillerThermal specific inputs as defined in reo/nested_inputs
        """
        
        self.load_type = load_type
        
        self.nearest_city = nearest_city
        self.latitude = latitude
        self.longitude = longitude
        self.time_steps_per_hour = time_steps_per_hour
        self.year = year
        # Default electric_load_list to None, used later to see if we need to covert kWh to kWht
        electric_load_list = None
        
        # Use highest resultion/quality input first
        if kwargs.get('loads_ton') is not None:
            self.load_list = [i*TONHOUR_TO_KWHT for i in kwargs['loads_ton']]
        
        # DOE Reference building profile are used if there is a reference name provided
        elif kwargs.get('doe_reference_name'):
            doe_reference_name = kwargs.get('doe_reference_name') or []
            combine_loadlist = []
            for i in range(len(doe_reference_name)):
                # Monthly loads can only be used to scale a non-hybrid profile
                kwargs['monthly_totals_energy'] = kwargs.get("monthly_tonhour")
                if len(doe_reference_name)>1:
                    kwargs['monthly_totals_energy'] = None
                
                kwargs['annual_energy'] = None
                # Annual loads are used in place of percent shares if provided
                if kwargs.get("annual_tonhour") is not None:
                    kwargs['annual_energy'] = kwargs["annual_tonhour"]
                
                kwargs['annual_loads'] = self.annual_loads
                kwargs['load_type'] = self.load_type
                kwargs['latitude'] = latitude
                kwargs['longitude'] = longitude
                kwargs['doe_reference_name'] = doe_reference_name[i]
                kwargs['nearest_city'] = nearest_city
                kwargs['time_steps_per_hour'] = time_steps_per_hour
                kwargs['year'] = year
                super(LoadProfileChillerThermal, self).__init__(**kwargs)
                if time_steps_per_hour > 1:
                    partial_load_list = np.concatenate([[x] * time_steps_per_hour \
                                                            for x in self.built_in_profile])
                else:
                    partial_load_list = self.built_in_profile
                combine_loadlist.append(list(partial_load_list))

            # In the case where the user supplies a list of doe_reference_names and percent shares
            # for consistency we want to act as if we had scaled the partial load to the total site 
            # load which was unknown at the start of the loop above. This scalar makes it such that
            # when the percent shares are later applied that the total site load will be the sum
            # of the default annual loads for this location
            if (len(doe_reference_name) > 1) and kwargs['annual_energy'] is None:
                total_site_load = sum([sum(l) for l in combine_loadlist])
                for i, load in enumerate(combine_loadlist):
                    actual_percent_of_site_load = sum(load)/total_site_load
                    scalar = 1.0 / actual_percent_of_site_load
                    combine_loadlist[i] = list(np.array(load)* scalar)
            
            #Apply the percent share of annual load to each partial load
            if (len(doe_reference_name) > 1):
                for i, load in enumerate(combine_loadlist):
                    combine_loadlist[i] = list(np.array(load) * (kwargs.get("percent_share")[i]/100.0))

            # Aggregate total hybrid load
            hybrid_loadlist = list(np.sum(np.array(combine_loadlist), 0))
            
            if (kwargs.get("annual_tonhour") is not None) or (kwargs.get("monthly_tonhour") is not None):
                #load_list is always expected to be in units of kWt
                self.load_list = [i*TONHOUR_TO_KWHT for i in hybrid_loadlist]
            else:
                electric_load_list = hybrid_loadlist 
        
        # If no doe_reference_name or loads_ton provided, scale by a fraction of electric load
        elif kwargs.get('loads_fraction') is not None:
            electric_load_list = list(np.array(kwargs['loads_fraction']) * np.array(total_electric_load_list))

        elif kwargs.get('monthly_fraction') is not None:
            month_series = pd.date_range(datetime(year,1,1), datetime(year+1,1,1), periods=8760*time_steps_per_hour)
            electric_load_list = [total_electric_load_list[i] * kwargs['monthly_fraction'][month-1] \
                                     for i, month in enumerate(month_series.month)] 

        elif kwargs.get('annual_fraction') is not None:
            electric_load_list = [kwargs['annual_fraction'] * kw for kw in total_electric_load_list]
        
        #Calculate COP based on kwth load or kw load (if not user-entered) 
        self.chiller_cop = chiller_cop
        # Update COP based on estimated max chiller load
        if self.chiller_cop is None:
            if electric_load_list is not None:
                #This is a static method so it can be accessible in views.py
                self.chiller_cop = LoadProfileChillerThermal.get_default_cop(
                                max_kw=max(electric_load_list),
                                max_thermal_factor_on_peak_load=max_thermal_factor_on_peak_load)
            else:
                #This is a static method so it can be accessible in views.py
                self.chiller_cop = LoadProfileChillerThermal.get_default_cop(
                                max_kwt=max(self.load_list),
                                max_thermal_factor_on_peak_load=max_thermal_factor_on_peak_load)
        
        # load_list is always expected to be in units of kWth
        if electric_load_list is not None:            
            self.load_list = [i*self.chiller_cop for i in electric_load_list]
        self.annual_kwht = int(round(sum(self.load_list),0))
        if dfm is not None:
            dfm.add_load_chiller_thermal(self)
