from reo.src.load_profile import library_path_base, BuiltInProfile, space_heating_annual_loads, dhw_annual_loads, \
                                    total_heating_annual_loads, space_heating_fraction_flat_load
import json
import os
import copy
import numpy as np


class LoadProfileBoilerFuel(BuiltInProfile):
    """
    Boiler Load Profiles based on CRB defined load shapes or user-defined input

    This load class used for both space heating and domestic hot water (DHW)
    Two separate lpbf instances (lpbf_space and lpbf_dhw) are created in scenario.py so GHP can serve just space heating
    In the reopt_model.jl, the HeatingLoad is the sum of both space heating and DHW

    """  

    def __init__(self, load_type, dfm=None, latitude = None, longitude = None, nearest_city = None, time_steps_per_hour = None, 
                    year = None, **kwargs):
        """
        :param load_type: required input of DHW or SpaceHeating
        :param dfm: (object) data_manager to which this load object will be added
        :param latitude: (float) site latitude
        :param longitude: (float) site longitude
        :param nearest_city: (str) site nearest_city
        :param time_steps_per_hour: (int) simulation time resolution
        :param year: (int) electric LoadProfile year
        :param kwargs: (dict) LoadProfileBoilerFuel specific inputs as defined in reo/nested_inputs
        """

        self.load_type = load_type
        self.nearest_city = nearest_city
        self.latitude = latitude
        self.longitude = longitude
        self.time_steps_per_hour = time_steps_per_hour
        self.year = year

        # Using total/combined Space Heating plus DHW loads because the "normalized" profiles used in BuiltInProfile are based on the combined loads
        self.annual_loads = total_heating_annual_loads

        self.addressable_load_fraction = kwargs.get("addressable_load_fraction")
        self.space_heating_fraction = kwargs.get("space_heating_fraction_of_heating_load")
        
        if kwargs.get('loads_mmbtu_per_hour') is not None:
            if len(self.addressable_load_fraction) == 1:
                self.addressable_load_fraction = [self.addressable_load_fraction[0] for _ in range(8760 * self.time_steps_per_hour)]
            if not self.space_heating_fraction:
                # Assume 50/50 split between space heating and DHW if not entered by user (different defaults used for CRBs)
                self.space_heating_fraction = [0.5 for _ in range(8760 * self.time_steps_per_hour)]
            else:
                if len(self.space_heating_fraction) == 1:
                    self.space_heating_fraction = [self.space_heating_fraction[0] for _ in range(8760 * self.time_steps_per_hour)]
                # Note, split between Space Heating and DHW can be a single value or time step interval, not monthly
            if self.load_type == "SpaceHeating":
                self.load_list = [kwargs['loads_mmbtu_per_hour'][i] * 
                                    self.addressable_load_fraction[i] * 
                                    self.space_heating_fraction[i] for i in range(8760 * self.time_steps_per_hour)]
            else:
                self.load_list = [kwargs['loads_mmbtu_per_hour'][i] * 
                                    self.addressable_load_fraction[i] * 
                                    (1 - self.space_heating_fraction[i]) for i in range(8760 * self.time_steps_per_hour)]                                                
            self.annual_mmbtu = sum(self.load_list)

        else:  # building type and (annual_mmbtu OR monthly_mmbtu) defined by user
            doe_reference_name = kwargs['doe_reference_name']
            combine_loadlist = []
            
            for i in range(len(doe_reference_name)):
                # Monthly loads can only be used to scale a non-hybrid profile
                self.monthly_totals_energy = kwargs.get("monthly_mmbtu")
                if self.monthly_totals_energy not in [[], None]:
                    if len(self.addressable_load_fraction) == 1:
                        self.addressable_load_fraction = [self.addressable_load_fraction[0] for _ in range(12)]
                    # Note, when using doe_reference_name, the user cannot adjust the space_heating_fraction
                    kwargs['monthly_totals_energy'] = [self.monthly_totals_energy[i] * 
                                                        self.addressable_load_fraction[i] for i in range(12)]
                if len(doe_reference_name) > 1:
                    kwargs['monthly_totals_energy'] = None
                kwargs['annual_energy'] = None
                # We only scale by percent share if a raw annual mmbtu value has not been provided
                if kwargs.get("annual_mmbtu") is not None:
                    kwargs['annual_energy'] = kwargs["annual_mmbtu"] * self.addressable_load_fraction[0]
                    percent_share = 100
                else:
                    percent_share = kwargs.get("percent_share")[i]
                kwargs['annual_loads'] = self.annual_loads
                kwargs['load_type'] = self.load_type
                kwargs['latitude'] = latitude
                kwargs['longitude'] = longitude
                kwargs['doe_reference_name'] = doe_reference_name[i]
                kwargs['nearest_city'] = nearest_city
                kwargs['time_steps_per_hour'] = time_steps_per_hour
                kwargs['year'] = year
                kwargs['space_heating_fraction'] = self.space_heating_fraction
                super(LoadProfileBoilerFuel, self).__init__(**kwargs)
                if time_steps_per_hour > 1:
                    partial_load_list = np.concatenate([[x] * time_steps_per_hour \
                                                            for x in self.built_in_profile])
                else:
                    partial_load_list = self.built_in_profile
                combine_loadlist.append(partial_load_list)
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
            self.load_list = copy.copy(hybrid_loadlist)
            self.annual_mmbtu = int(round(sum(self.load_list),0))

        if dfm is not None and load_type == "SpaceHeating":
            dfm.add_load_boiler_fuel_space_heating(self)

        if dfm is not None and load_type == "DHW":
            dfm.add_load_boiler_fuel_dhw(self)
