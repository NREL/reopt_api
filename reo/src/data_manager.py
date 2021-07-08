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
import copy
from reo.src.urdb_parse import UrdbParse
from reo.src.fuel_params import FuelParams
from reo.utilities import annuity, degradation_factor, slope, intercept, insert_p_after_u_bp, insert_p_bp, \
    insert_u_after_p_bp, insert_u_bp, setup_capital_cost_incentive, annuity_escalation, MMBTU_TO_KWH
import numpy as np
max_incentive = 1.0e10

big_number = 1.0e10
squarefeet_to_acre = 2.2957e-5


def get_techs_not_none(techs, cls):
    ret = []
    for tech in techs:
        if eval('cls.' + tech) is not None:
            ret.append(tech)
    return ret


class DataManager:
    """
    Creates input dicts for reopt.jl and manages data transfer between Celery tasks
    """
    def __init__(self, run_id, user_id=None, n_timesteps=8760):
        self.pvs = []
        self.pvnms = []
        self.pv1 = None
        self.pv1nm = None
        self.wind = None
        self.windnm = None
        self.generator = None
        self.chp = None
        self.util = None
        self.boiler = None
        self.elecchl = None
        self.absorpchl = None
        self.storage = None
        self.hot_tes = None
        self.cold_tes = None
        self.site = None
        self.elec_tariff = None
        self.fuel_tariff = None
        self.load = None
        self.heating_load = None
        self.cooling_load = None
        self.rc = None
        self.ac = None
        self.hp = None
        self.hot_water_tank = None
        self.wher = None
        self.whhp = None
        self.reopt_inputs = None
        self.reopt_inputs_bau = None
        self.add_soc_incentive = None

        # following attributes used to pass data to process_results.py
        # If we serialize the python classes then we could pass the objects between Celery tasks
        # (which we could do by making a custom serializer, but have not yet).
        # For now we just put the values that we need in dicts that get passed between the tasks.
        self.LoadProfile = {}
        self.year_one_energy_cost_series_us_dollars_per_kwh = []
        self.year_one_demand_cost_series_us_dollars_per_kw = []

        self.available_techs = ['pv1', 'pv1nm', 'wind', 'windnm', 'generator', 'chp', 'boiler',
                                'elecchl', 'absorpchl', 'ac', 'hp', 'wher', 'whhp']  # order is critical for REopt! Note these are passed to reopt.jl as uppercase
        self.available_tech_classes = ['PV1', 'WIND', 'GENERATOR', 'CHP', 'BOILER',
                                       'ELECCHL', 'ABSORPCHL', 'AC', 'HP', 'WHER', 'WHHP']  # this is a REopt 'class', not a python class
        self.bau_techs = []
        self.NMILRegime = ['BelowNM', 'NMtoIL', 'AboveIL']
        self.fuel_burning_techs = ['GENERATOR', 'CHP']

        self.run_id = run_id
        self.user_id = user_id
        self.n_timesteps = n_timesteps
        self.steplength = 8760.0 / self.n_timesteps
        self.pwf_e = 0  # used in results.py -> outage_costs.py to escalate & discount avoided outage costs

    def add_load(self, load):
        self.LoadProfile["year_one_electric_load_series_kw"] = load.load_list
        self.LoadProfile["critical_load_series_kw"] = load.critical_load_series_kw
        self.LoadProfile["resilience_check_flag"] = load.resilience_check_flag
        self.LoadProfile["bau_sustained_time_steps"] = load.bau_sustained_time_steps
        self.LoadProfile["annual_kwh"] = load.annual_kwh
        self.load = load

    def add_load_boiler_fuel(self, load):
        self.LoadProfile["year_one_boiler_fuel_load_series_mmbtu_per_hr"] = load.load_list
        self.LoadProfile["annual_heating_mmbtu"] = load.annual_mmbtu
        self.heating_load = load

    def add_load_chiller_thermal(self, load):
        self.LoadProfile["year_one_chiller_electric_load_series_kw"] = list(np.array(load.load_list) / load.chiller_cop)
        self.LoadProfile["annual_cooling_kwh"] = load.annual_kwht / load.chiller_cop
        self.cooling_load = load

    def add_boiler(self, boiler):
        self.boiler = boiler
        self.boiler_efficiency = boiler.boiler_efficiency
        self.bau_techs.append('boiler')

    def add_electric_chiller(self, electric_chiller):
        self.elecchl = electric_chiller
        self.elecchl_cop = electric_chiller.chiller_cop
        self.bau_techs.append('elecchl')

    def add_rc(self, rc):
        self.rc = rc

    def add_flex_tech_ac(self, flex_tech_ac):
        self.ac = flex_tech_ac
        if self.ac.existing_kw > 0:
            self.rc.use_flexloads_model_bau = True
            # self.ac.use_crankcase_bau = self.ac.use_crankcase
            if 'ac' not in self.bau_techs:
                self.bau_techs.append('ac')
            if 'hp' not in self.bau_techs:
                self.bau_techs.append('hp')

    def add_flex_tech_hp(self, flex_tech_hp):
        self.hp = flex_tech_hp
        if self.hp.existing_kw > 0:
            self.rc.use_flexloads_model_bau = True
            if 'hp' not in self.bau_techs:
                self.bau_techs.append('hp')
            if 'ac' not in self.bau_techs:
                self.bau_techs.append('ac')

    def add_hot_water_tank(self, hot_water_tank):
        self.hot_water_tank = hot_water_tank

    def add_flex_tech_erwh(self, flex_tech_erwh):
        self.wher = flex_tech_erwh
        self.bau_techs.append('wher')

    def add_flex_tech_hpwh(self, flex_tech_hpwh):
        self.whhp = flex_tech_hpwh
        self.bau_techs.append('whhp')

    def add_pv(self, pv):
        junk = pv.prod_factor  # avoids redundant PVWatts call for pvnm
        self.pvs.append(pv)
        self.pvnms.append(copy.deepcopy(pv))
        self.pvnms[-1].nmil_regime = 'NMtoIL'

        pv_number = len(self.pvs)

        if pv.existing_kw > 0:
            self.bau_techs = ["pv"+str(pv_number), "pv"+str(pv_number)+"nm"] + self.bau_techs

        # update self.available_techs (baseline is ['pv1', 'pv1nm', 'wind', 'windnm', 'generator'])
        if pv_number > 1:
            i = pv_number - 1
            self.available_techs = self.available_techs[:i*2] + ["pv"+str(pv_number), "pv"+str(pv_number)+"nm"] + \
                                   self.available_techs[i*2:]
            self.available_tech_classes = self.available_tech_classes[:i] + ["PV" + str(pv_number)] + \
                                   self.available_tech_classes[i:]
            # eg. ['pv1', 'pvnm1', 'pv2', 'pvnm2', 'wind', 'windnm', 'generator']

        # for backwards compatibility with all self._get* methods we need to attach the individual PV objects to self:
        exec("self.pv" + str(pv_number) + " = self.pvs[{}]".format(pv_number-1))
        exec("self.pv" + str(pv_number) + "nm" + " = self.pvnms[{}]".format(pv_number - 1))

    def add_wind(self, wind):
        junk = wind.prod_factor  # avoids redundant WindToolkit call for windnm
        self.wind = wind
        self.windnm = copy.deepcopy(wind)
        self.windnm.nmil_regime = 'NMtoIL'

    def add_util(self, util):
        self.util = util

    def add_generator(self, generator):
        self.generator = generator

        if self.generator.existing_kw > 0:

            # following if-clause is to avoid appending generator twice in the bau_techs list
            # for the test-case when two tests are run under same class definition (e.g. test_diesel_generator.py)
            # bau_techs will never have more than 1 entry for 'generator'
            if 'generator' not in self.bau_techs:
                self.bau_techs.append('generator')

    def add_chp(self, chp):
        self.chp = chp

    def add_absorption_chiller(self, absorption_chiller):
        self.absorpchl = absorption_chiller

    def add_site(self, site):
        self.site = site

    def add_storage(self, storage):
        self.storage = storage
        # storage_bau.dat gets same definitions as storage.dat so that initializations don't fail in bau case
        # however, storage is typically 'turned off' by having max size set to zero in maxsizes_bau.dat
        # TODO: save reopt_inputs dictionary?
        # efficiencies are defined in finalize method because their arrays depend on which Techs are defined

    def add_hot_tes(self, hot_tes):
        self.hot_tes = hot_tes
        # All attributes are written in finalize method because they are stacked 1..2 for hot_tes..cold_tes storages

    def add_cold_tes(self, cold_tes):
        self.cold_tes = cold_tes
        # All attributes are written in finalize method because they are stacked 1..2 for hot_tes..cold_tes storages

    def add_elec_tariff(self, elec_tariff):
        self.elec_tariff = elec_tariff

    def add_fuel_tariff(self, fuel_tariff):
        self.fuel_tariff = fuel_tariff

    def _get_REopt_pwfs(self, techs):
        sf = self.site.financial
        pwf_owner = annuity(sf.analysis_years, 0, sf.owner_discount_pct) # not used in REopt
        pwf_offtaker = annuity(sf.analysis_years, 0, sf.offtaker_discount_pct)  # not used in REopt
        pwf_om = annuity(sf.analysis_years, sf.om_cost_escalation_pct, sf.owner_discount_pct)
        pwf_e = annuity(sf.analysis_years, sf.escalation_pct, sf.offtaker_discount_pct)
        pwf_boiler_fuel = annuity(sf.analysis_years, sf.boiler_fuel_escalation_pct, sf.offtaker_discount_pct)
        pwf_chp_fuel = annuity(sf.analysis_years, sf.chp_fuel_escalation_pct, sf.offtaker_discount_pct)
        self.pwf_e = pwf_e
        # pwf_op = annuity(sf.analysis_years, sf.escalation_pct, sf.owner_discount_pct)

        if sf.third_party_ownership:
            two_party_factor = (pwf_offtaker * (1 - sf.offtaker_tax_pct)) \
                                / (pwf_owner * (1 - sf.owner_tax_pct))
        else:
            two_party_factor = 1

        levelization_factor = list()
        pwf_fuel_by_tech = list()

        for tech in techs:

            if eval('self.' + tech) is not None:

                if tech.startswith("pv"):  # pv has degradation

                    #################
                    # NOTE: I don't think that levelization factors should include an escalation rate.  The degradation
                    # does not escalate in out years.
                    ################
                    degradation_pct = eval('self.' + tech + '.degradation_pct')
                    levelization_factor.append(round(degradation_factor(sf.analysis_years, degradation_pct), 5))
                else:
                    levelization_factor.append(1.0)

                # Assign pwf_fuel_by_tech
                if tech in ['chp', 'chpnm']:
                    pwf_fuel_by_tech.append(round(pwf_chp_fuel, 5))
                elif tech == 'boiler':
                    pwf_fuel_by_tech.append(round(pwf_boiler_fuel, 5))
                else:
                    pwf_fuel_by_tech.append(round(pwf_e, 5))

        return levelization_factor, pwf_e, pwf_om, two_party_factor, pwf_boiler_fuel, pwf_chp_fuel, pwf_fuel_by_tech

    def _get_REopt_production_incentives(self, techs):
        sf = self.site.financial
        pwf_prod_incent = list()
        max_prod_incent = list()
        max_size_for_prod_incent = list()

        production_incentive_rate = list()

        for tech in techs:

            if eval('self.' + tech) is not None:

                if tech not in ['generator', 'boiler', 'elecchl', 'absorpchl', 'ac', 'hp', 'wher', 'whhp']:

                    # prod incentives don't need escalation
                    if tech.startswith("pv"):  # PV has degradation
                        pwf_prod_incent.append(
                            annuity_escalation(eval('self.' + tech + '.incentives.production_based.years'),
                                               -1 * eval('self.' + tech + '.degradation_pct'),
                                               sf.owner_discount_pct))
                    else:
                        pwf_prod_incent.append(
                            annuity(eval('self.' + tech + '.incentives.production_based.years'),
                                    0, sf.owner_discount_pct))
                    max_prod_incent.append(
                        eval('self.' + tech + '.incentives.production_based.max_us_dollars_per_year')
                    )
                    max_size_for_prod_incent.append(
                        eval('self.' + tech + '.incentives.production_based.max_kw')
                    )

                    production_incentive_rate.append(
                        eval('self.' + tech + '.incentives.production_based.us_dollars_per_kw')
                    )
                else:

                    pwf_prod_incent.append(0.0)
                    max_prod_incent.append(0.0)
                    max_size_for_prod_incent.append(0.0)
                    production_incentive_rate.append(0.0)

        return pwf_prod_incent, max_prod_incent, max_size_for_prod_incent, production_incentive_rate

    def _get_REopt_cost_curve(self, techs):
        regions = ['utility', 'state', 'federal', 'combined']
        cap_cost_slope = list()
        cap_cost_x = list()
        cap_cost_yint = list()
        n_segments_max = 0  # tracking the maximum number of cost curve segments
        n_segments = 1
        n_segments_list = list()
        tech_to_size = float(big_number)

        for tech in techs:

            if eval('self.' + tech) is not None and tech not in ['boiler', 'elecchl']:

                existing_kw = 0.0
                if hasattr(eval('self.' + tech), 'existing_kw'):
                    if eval('self.' + tech + '.existing_kw') is not None:
                        existing_kw = eval('self.' + tech + '.existing_kw')

                tech_cost = eval('self.' + tech + '.installed_cost_us_dollars_per_kw')
                tech_incentives = dict()

                for region in regions[:-1]:
                    tech_incentives[region] = dict()

                    if tech not in ['generator', 'absorpchl', 'ac', 'hp', 'wher', 'whhp']:

                        if region == 'federal' or region == 'total':
                            tech_incentives[region]['%'] = eval('self.' + tech + '.incentives.' + region + '.itc')
                            tech_incentives[region]['%_max'] = eval('self.' + tech + '.incentives.' + region + '.itc_max')
                        else:  # region == 'state' or region == 'utility'
                            tech_incentives[region]['%'] = eval('self.' + tech + '.incentives.' + region + '.ibi')
                            tech_incentives[region]['%_max'] = eval('self.' + tech + '.incentives.' + region + '.ibi_max')

                        tech_incentives[region]['rebate'] = eval('self.' + tech + '.incentives.' + region + '.rebate')
                        tech_incentives[region]['rebate_max'] = eval('self.' + tech + '.incentives.' + region + '.rebate_max')

                        # Workaround to consider fact that REopt incentive calculation works best if "unlimited" incentives are entered as 0
                        if tech_incentives[region]['%_max'] == max_incentive:
                            tech_incentives[region]['%_max'] = 0.0
                        if tech_incentives[region]['rebate_max'] == max_incentive:
                            tech_incentives[region]['rebate_max'] = 0.0

                    else:  # for generator and absorption chiller, there are no incentives
                        tech_incentives[region]['%'] = 0.0
                        tech_incentives[region]['%_max'] = 0.0
                        tech_incentives[region]['rebate'] = 0.0
                        tech_incentives[region]['rebate_max'] = 0.0

                # Intermediate Cost curve
                # New input of tech_size_for_cost_curve to be associated with tech_cost (installed_cost_us_dollars_per_kw) with same type and length
                if hasattr(eval('self.' + tech), 'tech_size_for_cost_curve'):
                    if eval('self.' + tech + '.tech_size_for_cost_curve') not in [None, []]:
                        tech_size = eval('self.' + tech + '.tech_size_for_cost_curve')
                    else:
                        tech_size = [float(big_number)]
                else:
                    tech_size = [float(big_number)]

                xp_array_incent = dict()
                if len(tech_size) > 1:
                    xp_array_incent['utility'] = []
                    if tech_size[0] != 0: # Append a 0 to the front of the list if not included(we'll assume that it has a 0 y-intercept below)
                        xp_array_incent['utility'] += [0]
                    xp_array_incent['utility'] += [tech_size[i] for i in range(len(tech_size))]  # [$]  # Append list of sizes for cost curve [kW]
                    xp_array_incent['utility'] += [float(big_number)]  # Append big number size to assume same cost as last input point
                else:
                    xp_array_incent['utility'] = [0.0, float(big_number)]

                yp_array_incent = dict()
                if len(tech_size) > 1:
                    if tech_size[0] == 0:
                        yp_array_incent['utility'] = [tech_cost[0]]  # tech_cost[0] is assumed to be in units of $, if there is tech_size[0]=0 point
                        yp_array_incent['utility'] += [tech_size[i] * tech_cost[i] for i in range(1, len(tech_cost))]  # [$]
                    else:
                        yp_array_incent['utility'] = [0]
                        yp_array_incent['utility'] += [tech_size[i] * tech_cost[i] for i in range(len(tech_cost))]  # [$]
                    yp_array_incent['utility'] += [float(big_number) * tech_cost[-1]]  # Last cost assumed for big_number size
                    # Final cost curve
                    cost_curve_bp_y = [yp_array_incent['utility'][0]]
                else:
                    if isinstance(tech_cost, list):
                        yp_array_incent['utility'] = [0.0, float(big_number) * tech_cost[0]]  # [$]
                    else:
                        yp_array_incent['utility'] = [0.0, float(big_number) * tech_cost]  # [$]
                    # Final cost curve
                    cost_curve_bp_y = [0.0]

                # Final cost curve
                cost_curve_bp_x = [0.0]

                for r in range(len(regions)-1):

                    region = regions[r]  # regions = ['utility', 'state', 'federal', 'combined']
                    next_region = regions[r + 1]

                    # Apply incentives, initialize first value
                    xp_array_incent[next_region] = [0.0]
                    yp_array_incent[next_region] = [0.0]

                    # percentage based incentives
                    p = float(tech_incentives[region]['%'])
                    p_cap = float(tech_incentives[region]['%_max'])

                    # rebates, for some reason called 'u' in REopt
                    u = float(tech_incentives[region]['rebate'])
                    u_cap = float(tech_incentives[region]['rebate_max'])

                    # reset switches and break point counter
                    switch_percentage = False
                    switch_rebate = False

                    if p == 0 or p_cap == 0:
                        switch_percentage = True
                    if u == 0 or u_cap == 0:
                        switch_rebate = True

                    # start at second point, first is always zero
                    for point in range(1, len(xp_array_incent[region])):

                        # previous points
                        xp_prev = xp_array_incent[region][point - 1]
                        yp_prev = yp_array_incent[region][point - 1]

                        # current, unadjusted points
                        xp = xp_array_incent[region][point]
                        yp = yp_array_incent[region][point]

                        # initialize the adjusted points on cost curve
                        xa = xp
                        ya = yp

                        # initialize break points
                        u_xbp = 0.0
                        u_ybp = 0.0
                        p_xbp = 0.0
                        p_ybp = 0.0

                        if not switch_rebate:
                            u_xbp = u_cap / u
                            u_ybp = slope(xp_prev, yp_prev, xp, yp) * u_xbp + intercept(xp_prev, yp_prev, xp, yp)

                        if not switch_percentage:
                            p_xbp = (p_cap / p - intercept(xp_prev, yp_prev, xp, yp)) / slope(xp_prev, yp_prev, xp, yp)
                            p_ybp = p_cap / p

                        if ((p * yp) < p_cap or p_cap == 0) and ((u * xp) < u_cap or u_cap == 0):
                            ya = yp - (p * yp + u * xp)
                        elif (p * yp) < p_cap and (u * xp) >= u_cap:
                            if not switch_rebate:
                                if u * xp != u_cap:
                                    xp_array_incent, yp_array_incent = \
                                        insert_u_bp(xp_array_incent, yp_array_incent, next_region, u_xbp, u_ybp, p, u_cap)
                                switch_rebate = True
                            ya = yp - (p * yp + u_cap)
                        elif (p * yp) >= p_cap and (u * xp) < u_cap:
                            if not switch_percentage:
                                if p * yp != p_cap:
                                    xp_array_incent, yp_array_incent = \
                                        insert_p_bp(xp_array_incent, yp_array_incent, next_region, p_xbp, p_ybp, u, p_cap)
                                switch_percentage = True
                            ya = yp - (p_cap + xp * u)
                        elif p * yp >= p_cap and u * xp >= u_cap:
                            if not switch_rebate and not switch_percentage:
                                if p_xbp == u_xbp:
                                    xp_array_incent, yp_array_incent = \
                                        insert_u_bp(xp_array_incent, yp_array_incent, next_region, u_xbp, u_ybp, p, u_cap)
                                    switch_percentage = True
                                    switch_rebate = True
                                elif p_xbp < u_xbp:
                                    if p * yp != p_cap:
                                        xp_array_incent, yp_array_incent = \
                                            insert_p_bp(xp_array_incent, yp_array_incent, next_region, p_xbp, p_ybp, u,
                                                        p_cap)
                                    switch_percentage = True
                                    if u * xp != u_cap:
                                        xp_array_incent, yp_array_incent = \
                                            insert_u_after_p_bp(xp_array_incent, yp_array_incent, next_region, u_xbp, u_ybp,
                                                                p, p_cap, u_cap)
                                    switch_rebate = True
                                else:
                                    if u * xp != u_cap:
                                        xp_array_incent, yp_array_incent = \
                                            insert_u_bp(xp_array_incent, yp_array_incent, next_region, u_xbp, u_ybp, p, u_cap)
                                    switch_rebate = True
                                    if p * yp != p_cap:
                                        xp_array_incent, yp_array_incent = \
                                            insert_p_after_u_bp(xp_array_incent, yp_array_incent, next_region, p_xbp, p_ybp,
                                                                u, u_cap, p_cap)
                                    switch_percentage = True
                            elif switch_rebate and not switch_percentage:
                                if p * yp != p_cap:
                                    xp_array_incent, yp_array_incent = \
                                        insert_p_after_u_bp(xp_array_incent, yp_array_incent, next_region, p_xbp, p_ybp, u,
                                                            u_cap, p_cap)
                                switch_percentage = True
                            elif switch_percentage and not switch_rebate:
                                if u * xp != u_cap:
                                    xp_array_incent, yp_array_incent = \
                                        insert_u_after_p_bp(xp_array_incent, yp_array_incent, next_region, u_xbp, u_ybp, p,
                                                            p_cap, u_cap)
                                switch_rebate = True

                            # Finally compute adjusted values
                            if p_cap == 0:
                                ya = yp - (p * yp + u_cap)
                            elif u_cap == 0:
                                ya = yp - (p_cap + u * xp)
                            else:
                                ya = yp - (p_cap + u_cap)

                        xp_array_incent[next_region].append(xa)
                        yp_array_incent[next_region].append(ya)

                        # compute cost curve, funky logic in REopt ignores everything except xa, ya
                        if region == 'federal':
                            cost_curve_bp_x.append(xa)
                            cost_curve_bp_y.append(ya)

                tmp_cap_cost_slope = list()
                tmp_cap_cost_yint = list()

                for seg in range(1, len(cost_curve_bp_x)):
                    tmp_slope = round((cost_curve_bp_y[seg] - cost_curve_bp_y[seg - 1]) /
                                      (cost_curve_bp_x[seg] - cost_curve_bp_x[seg - 1]), 0)
                    tmp_y_int = round(cost_curve_bp_y[seg] - tmp_slope * cost_curve_bp_x[seg], 0)

                    tmp_cap_cost_slope.append(tmp_slope)
                    tmp_cap_cost_yint.append(tmp_y_int)

                n_segments = len(tmp_cap_cost_slope)

                # Following logic modifies the cap cost segments to account for the tax benefits of the ITC and MACRs
                updated_cap_cost_slope = list()
                updated_y_intercept = list()

                if tech not in ['ac', 'hp', 'wher', 'whhp']:
                    for s in range(n_segments):

                        if cost_curve_bp_x[s + 1] > 0:
                            # Remove federal incentives for ITC basis and tax benefit calculations
                            itc = eval('self.' + tech + '.incentives.federal.itc')
                            rebate_federal = eval('self.' + tech + '.incentives.federal.rebate')
                            if itc is None or rebate_federal is None:
                                itc = 0.0
                                rebate_federal = 0.0
                            if itc == 1:
                                itc_unit_basis = 0
                            else:
                                itc_unit_basis = (tmp_cap_cost_slope[s] + rebate_federal) / (1 - itc)
                        else:
                            # Not sure how else to handle this case, perhaps there is a better way to handle it?
                            raise Exception('Invalid cost curve for {}. Value at index {} ({}) cannot be less than or equal to 0'.format(tech, s, cost_curve_bp_x[s + 1]))

                        sf = self.site.financial
                        updated_slope = setup_capital_cost_incentive(
                            itc_basis=itc_unit_basis,  # input tech cost with incentives, but no ITC
                            replacement_cost=0,
                            replacement_year=sf.analysis_years,
                            discount_rate=sf.owner_discount_pct,
                            tax_rate=sf.owner_tax_pct,
                            itc=itc,
                            macrs_schedule=eval('self.' + tech + '.incentives.macrs_schedule'),
                            macrs_bonus_pct=eval('self.' + tech + '.incentives.macrs_bonus_pct'),
                            macrs_itc_reduction=eval('self.' + tech + '.incentives.macrs_itc_reduction')
                        )
                        # The way REopt incentives currently work, the federal rebate is the only incentive that doesn't reduce ITC basis
                        updated_slope -= rebate_federal
                        updated_cap_cost_slope.append(updated_slope)

                    for p in range(1, n_segments + 1):
                        cost_curve_bp_y[p] = cost_curve_bp_y[p - 1] + updated_cap_cost_slope[p - 1] * \
                                                                    (cost_curve_bp_x[p] - cost_curve_bp_x[p - 1])
                        updated_y_intercept.append(cost_curve_bp_y[p] - updated_cap_cost_slope[p - 1] * cost_curve_bp_x[p])

                    tmp_cap_cost_slope = updated_cap_cost_slope
                    tmp_cap_cost_yint = updated_y_intercept

                """
                Adjust first cost curve segment to account for existing_kw.
                NOTE:
                - first X "breakpoint" and y-intercept must ALWAYS be zero (to be compatible with REopt constraints and
                    costing formulation.
                - if existing_kw > 0, then the first slope must also be zero (cannot be negative!).

                Steps:
                    1. find the segment for existing_kw
                    2. find the y-value for existing_kw (which is an x-value)
                    3. set the cost curve to x-axis from zero kw up to existing_kw
                    4. shift the rest of the cost curve down by the y-value found in step 2
                    5. reset n_segments (existing_kw can add a breakpoint, or take them away)
                """
                if existing_kw > 0:  # PV or Generator has existing_kw
                    # find the first index in cost_curve_bp_x that is larger than existing_kw, then reset cost curve
                    for i, bp in enumerate(cost_curve_bp_x[1:]):  # need to make sure existing_kw is never larger then last bp
                        if bp <= existing_kw:
                            continue
                        else:
                            y_shift = -(tmp_cap_cost_slope[i] * existing_kw + tmp_cap_cost_yint[i])
                            tmp_cap_cost_slope = [0.0] + tmp_cap_cost_slope[i:]
                            tmp_cap_cost_yint = [0.0] + [y + y_shift for y in tmp_cap_cost_yint[i:]]
                            cost_curve_bp_x = [0.0, existing_kw] + cost_curve_bp_x[i+1:]
                            n_segments = len(tmp_cap_cost_slope)
                            break

                # append the current Tech's segments to the arrays that will be passed to REopt
                cap_cost_slope += tmp_cap_cost_slope
                cap_cost_yint += tmp_cap_cost_yint
                cap_cost_x += cost_curve_bp_x

                # Have to take n_segments as the maximum number across all technologies
                n_segments_max = max(n_segments, n_segments_max)
                n_segments_list.append(n_segments)

            # Append 0's to non-costed technologies
            elif eval('self.' + tech) is not None and tech in ['boiler', 'elecchl']:

                cap_cost_slope.append(0.0)
                cap_cost_yint.append(0.0)
                cap_cost_x += [0.0, big_number]

                # Have to take n_segments as the maximum number across all technologies
                n_segments = 1
                n_segments_max = max(n_segments, n_segments_max)
                n_segments_list.append(n_segments)

        """
        Last step in creating cost curve is filling in the curves for each tech that does not have
        n_segments == n_segments_max. The filling in is achieved by duplicating the origin with zero cap_cost_slope for
        as many additional segments that are needed.
        """
        adj_cap_cost_slope, adj_cap_cost_x, adj_cap_cost_yint = list(), list(), list()
        for n_segments in n_segments_list:
            slope_list = cap_cost_slope[0:n_segments]
            del cap_cost_slope[0:n_segments]
            y_list = cap_cost_yint[0:n_segments]
            del cap_cost_yint[0:n_segments]
            x_list = cap_cost_x[0:n_segments+1]
            del cap_cost_x[0:n_segments+1]

            n_segments_to_add = n_segments_max - n_segments
            adj_cap_cost_slope += [0.0]*n_segments_to_add + slope_list
            adj_cap_cost_yint += [0.0]*n_segments_to_add + y_list
            adj_cap_cost_x += [0.0]*n_segments_to_add + x_list

        return adj_cap_cost_slope, adj_cap_cost_x, adj_cap_cost_yint, n_segments_max

    def _get_REopt_techToNMILMapping(self, techs):
        TechToNMILMapping = list()

        if len(techs) == 0:
            TechsByNMILRegime = []
            NMIL_regime = []
        else:
            TechsByNMILRegime = [[] for _ in self.NMILRegime]
            NMIL_regime = self.NMILRegime

        for tech in techs:

            if eval('self.' + tech) is not None:

                tech_regime = eval('self.' + tech + '.nmil_regime')

                for i,regime in enumerate(self.NMILRegime):
                    if regime == tech_regime:
                        TechToNMILMapping.append(1)
                        TechsByNMILRegime[i].append(tech.upper())
                    else:
                        TechToNMILMapping.append(0)

        return TechToNMILMapping, TechsByNMILRegime, NMIL_regime

    def _get_REopt_array_tech_load(self, techs):
        """
        Many arrays are built from Tech and Load. As many as possible are defined here to reduce for-loop iterations
        :param techs: list of strings, eg. ['pv', 'pvnm']
        :return: tech_to_location, derate, \
               om_cost_us_dollars_per_kw, om_cost_us_dollars_per_kwh, production_factor, charge_efficiency, \
               discharge_efficiency, techs_charging_storage, electric_derate
        """
        production_factor = list()
        tech_to_location = list()
        derate = list()
        electric_derate = list()
        om_cost_us_dollars_per_kw = list()
        om_cost_us_dollars_per_kwh = list()
        chp_thermal_prod_factor = list()
        om_cost_us_dollars_per_hr_per_kw_rated = list()

        charge_efficiency = list()
        discharge_efficiency = list()

        for tech in techs:
            if eval('self.' + tech) is not None:
                derate.append(eval('self.' + tech + '.derate'))
                if not tech.lower().startswith('chp'):
                    for pf in eval('self.' + tech + '.prod_factor'):
                        production_factor.append(float(pf))
                        electric_derate.append(1.0)
                else:
                    pf_electric, pf_hot_thermal = self.chp.prod_factor
                    for pf in pf_electric:
                        production_factor.append(float(pf))
                    chp_thermal_prod_factor = [float(pf) for pf in pf_hot_thermal]
                    for pf in self.chp.chp_power_derate:
                        electric_derate.append(float(pf))

                charge_efficiency.append(self.storage.rectifier_efficiency_pct *
                                                 self.storage.internal_efficiency_pct**0.5)
                charge_efficiency.append(self.hot_tes.internal_efficiency_pct)
                charge_efficiency.append(self.cold_tes.internal_efficiency_pct)
                # Yearly fixed O&M per unit power
                if tech.lower() in ['boiler', 'elecchl']:
                    om_cost_us_dollars_per_kw.append(0)
                else:
                    om_cost_us_dollars_per_kw.append(eval('self.' + tech + '.om_cost_us_dollars_per_kw'))


                # only generator and chp techs have variable o&m cost
                if tech.lower() == 'generator':
                    om_cost_us_dollars_per_kwh.append(float(eval('self.' + tech + '.kwargs["om_cost_us_dollars_per_kwh"]')))
                    om_cost_us_dollars_per_hr_per_kw_rated.append(0.0)
                elif tech.lower() == 'chp':
                    om_cost_us_dollars_per_kwh.append(float(eval('self.' + tech + '.om_cost_us_dollars_per_kwh')))
                    om_cost_us_dollars_per_hr_per_kw_rated.append(float(eval('self.' + tech + '.om_cost_us_dollars_per_hr_per_kw_rated')))
                else:
                    om_cost_us_dollars_per_kwh.append(0.0)
                    om_cost_us_dollars_per_hr_per_kw_rated.append(0.0)

                for location in ['roof', 'ground', 'both']:
                    if tech.startswith('pv'):
                        if eval('self.' + tech + '.location') == location:
                            tech_to_location.append(1)
                        else:
                            tech_to_location.append(0)
                    else:
                        tech_to_location.append(0)

        discharge_efficiency.append(self.storage.inverter_efficiency_pct * self.storage.internal_efficiency_pct**0.5)
        # Current TES efficiency input is just charging/in efficiency, so eta_tes_out is 1.
        discharge_efficiency.append(1.0)
        discharge_efficiency.append(1.0)

        # In BAU case, storage.dat must be filled out for REopt initializations, but max size is set to zero

        return tech_to_location, derate, \
               om_cost_us_dollars_per_kw, om_cost_us_dollars_per_kwh, om_cost_us_dollars_per_hr_per_kw_rated, \
               production_factor, charge_efficiency, discharge_efficiency, \
               electric_derate, chp_thermal_prod_factor

    def _get_REopt_techs(self, techs):
        reopt_techs = list()
        for tech in techs:
            if eval('self.' + tech) is not None:
                reopt_techs.append(tech.upper())

        return reopt_techs

    def _get_REopt_tech_classes(self, techs, bau):
        """

        :param techs: list of strings, eg. ['pv1', 'pvnm1']
        :return: tech_classes, tech_class_min_size
        """
        if len(techs) == 0:
            return [0.0 for _ in self.available_tech_classes], [[] for _ in self.available_tech_classes]
        tech_class_min_size = list()  # array(TechClass)
        techs_in_class = list()  # array(TechClass)
        for tc in self.available_tech_classes:
            min_sizes = [0.0]
            for tech in (x for x in techs if x.startswith(tc.lower()) and 'nm' not in x):
                if eval('self.' + tech) is not None:
                    if hasattr(eval('self.' + tech), 'existing_kw'):
                        if bau:
                            min_sizes.append((eval('self.' + tech + '.existing_kw') or 0.0))
                        else:
                            min_sizes.append((eval('self.' + tech + '.existing_kw') or 0.0) + (eval('self.' + tech + '.min_kw') or 0.0))
                    else:
                        min_sizes.append((eval('self.' + tech + '.min_kw') or 0.0))

            tech_class_min_size.append(max(min_sizes))

        for tc in self.available_tech_classes:
            class_list = list()
            for tech in techs:
                if eval('self.' + tech) is not None:
                    if eval('self.' + tech + '.reopt_class').upper() == tc.upper():
                        class_list.append(tech.upper())
            techs_in_class.append(class_list)

        return tech_class_min_size, techs_in_class

    def _get_REopt_tech_max_sizes_min_turn_down(self, techs, bau=False):
        max_sizes = list()
        min_turn_down = list()
        min_allowable_size = list()
        # default to large max size per location. Max size by roof, ground, both
        max_sizes_location = [1.0e9, 1.0e9, 1.0e9]
        pv_roof_limited, pv_ground_limited, pv_space_limited = False, False, False
        roof_existing_pv_kw = 0.0
        ground_existing_pv_kw = 0.0
        both_existing_pv_kw = 0.0
        for tech in techs:

            if eval('self.' + tech) is not None:
                existing_kw = 0.0
                if hasattr(eval('self.' + tech), 'existing_kw'):
                    if eval('self.' + tech + '.existing_kw') is not None:
                        existing_kw = eval('self.' + tech + '.existing_kw')

                if hasattr(eval('self.' + tech), 'min_turn_down_pct'):
                    min_turn_down.append(eval('self.' + tech + '.min_turn_down_pct'))
                else:
                    min_turn_down.append(0.0)

                if hasattr(eval('self.' + tech), 'min_allowable_kw'):
                    min_allowable_size.append(eval('self.' + tech + '.min_allowable_kw'))
                else:
                    min_allowable_size.append(0)

                beyond_existing_cap_kw = eval('self.' + tech + '.max_kw')  # default is big_number
                if tech.startswith('pv'):  # has acres_per_kw and kw_per_square_foot attributes, as well as location
                    if eval('self.' + tech + '.location') == 'both':
                        both_existing_pv_kw += existing_kw
                        if self.site.roof_squarefeet is not None and self.site.land_acres is not None:
                            # don't restrict unless they specify both land_area and roof_area,
                            # otherwise one of them is "unlimited" in UI
                            roof_max_kw = self.site.roof_squarefeet * eval('self.' + tech + '.kw_per_square_foot')
                            land_max_kw = self.site.land_acres / eval('self.' + tech + '.acres_per_kw')
                            beyond_existing_cap_kw = min(roof_max_kw + land_max_kw, beyond_existing_cap_kw)
                            pv_space_limited = True
                    elif eval('self.' + tech + '.location') == 'roof':
                        roof_existing_pv_kw += existing_kw
                        if self.site.roof_squarefeet is not None:
                            roof_max_kw = self.site.roof_squarefeet * eval('self.' + tech + '.kw_per_square_foot')
                            beyond_existing_cap_kw = min(roof_max_kw, beyond_existing_cap_kw)
                            pv_roof_limited = True

                    elif eval('self.' + tech + '.location') == 'ground':
                        ground_existing_pv_kw += existing_kw
                        if self.site.land_acres is not None:
                            land_max_kw = self.site.land_acres / eval('self.' + tech + '.acres_per_kw')
                            beyond_existing_cap_kw = min(land_max_kw, beyond_existing_cap_kw)
                            pv_ground_limited = True

                else:
                    if eval('self.' + tech + '.acres_per_kw') is not None:
                        if eval('self.' + tech + '.kw_per_square_foot') is not None:
                            if self.site.roof_squarefeet is not None and self.site.land_acres is not None:
                                # don't restrict unless they specify both land_area and roof_area,
                                # otherwise one of them is "unlimited" in UI
                                roof_max_kw = self.site.roof_squarefeet * eval('self.' + tech + '.kw_per_square_foot')
                                land_max_kw = self.site.land_acres / eval('self.' + tech + '.acres_per_kw')
                                beyond_existing_cap_kw = min(roof_max_kw + land_max_kw, beyond_existing_cap_kw)

                if tech.startswith('wind'):  # has acres_per_kw attribute
                    if self.site.land_acres is not None:
                        site_constraint_kw = self.site.land_acres / eval('self.' + tech + '.acres_per_kw')
                        if site_constraint_kw < 1500:
                            # turbines less than 1.5 MW aren't subject to the acres/kW limit
                            site_constraint_kw = 1500
                        beyond_existing_cap_kw = min(site_constraint_kw, beyond_existing_cap_kw)

                if bau and existing_kw > 0:  # existing PV in BAU scenario
                    max_sizes.append(float(existing_kw))
                else:
                    max_sizes.append(float(existing_kw + beyond_existing_cap_kw))

        if pv_roof_limited is True:
            max_sizes_location[0] = float(roof_existing_pv_kw/2 + roof_max_kw)
        if pv_ground_limited is True:
            max_sizes_location[1] = float(ground_existing_pv_kw/2 + land_max_kw)
        if pv_space_limited is True:
            max_sizes_location[2] = float(both_existing_pv_kw/2 + roof_max_kw + land_max_kw)
        # existing PV kW's divided by 2 b/c of the duplicate existing capacity created by `pv*nm`

        return max_sizes, min_turn_down, max_sizes_location, min_allowable_size

    def _get_tech_subsets(self, techs):
        tech_subdivisions = list()
        for tech in techs:
            tech_sub = list()
            if tech in self.available_techs:
                tech_sub.append('CapCost')
            if tech in self.fuel_burning_techs:
                tech_sub.append('FuelBurn')
            tech_subdivisions.append(tech_sub)
        return tech_subdivisions

    def _get_time_steps_with_grid(self):
        """
        Obtains the subdivision of time steps with a grid connection and those
        without (i.e., under an outage).  Uses the utility's prod_factor value
        (1=connected, 0 o.w.) at each time step to obtain these sets, which
        are presented as lists.

        Parameters
            None
        Returns
            time_steps_with_grid -- list of ints indicating grid-connected
                time steps
            time_steps_without_grid -- list of ints indicating outage time
                steps
        """
        time_steps_with_grid = list()
        time_steps_without_grid = list()
        for i, pf in enumerate(self.util.prod_factor):
            if pf > 0.5:
                time_steps_with_grid.append(i+1)
            else:
                time_steps_without_grid.append(i+1)
        return time_steps_with_grid, time_steps_without_grid

    def _get_REopt_storage_techs_and_params(self):
        storage_techs = ['Elec']
        storage_power_cost = list()
        storage_energy_cost = list()
        storage_min_power = [self.storage.min_kw]
        storage_max_power = [self.storage.max_kw]
        storage_min_energy = [self.storage.min_kwh]
        storage_max_energy = [self.storage.max_kwh]
        storage_decay_rate = [0.0]

        # Obtain storage costs and params
        sf = self.site.financial
        StorageCostPerKW = setup_capital_cost_incentive(
            self.storage.installed_cost_us_dollars_per_kw,  # use full cost as basis
            self.storage.replace_cost_us_dollars_per_kw,
            self.storage.inverter_replacement_year,
            sf.owner_discount_pct,
            sf.owner_tax_pct,
            self.storage.incentives.itc_pct,
            self.storage.incentives.macrs_schedule,
            self.storage.incentives.macrs_bonus_pct,
            self.storage.incentives.macrs_itc_reduction
        )
        StorageCostPerKW -= self.storage.incentives.rebate
        StorageCostPerKWH = setup_capital_cost_incentive(
            self.storage.installed_cost_us_dollars_per_kwh,  # there are no cash incentives for kwh
            self.storage.replace_cost_us_dollars_per_kwh,
            self.storage.battery_replacement_year,
            sf.owner_discount_pct,
            sf.owner_tax_pct,
            self.storage.incentives.itc_pct,
            self.storage.incentives.macrs_schedule,
            self.storage.incentives.macrs_bonus_pct,
            self.storage.incentives.macrs_itc_reduction
        )
        StorageCostPerKWH -= self.storage.incentives.rebate_kwh

        storage_power_cost.append(StorageCostPerKW)
        storage_energy_cost.append(StorageCostPerKWH)
        if self.hot_tes is not None:
            HotTESCostPerKWH = setup_capital_cost_incentive(
                self.hot_tes.installed_cost_us_dollars_per_kwh,  # use full cost as basis
                0,
                0,
                sf.owner_discount_pct,
                sf.owner_tax_pct,
                0,
                self.hot_tes.incentives.macrs_schedule,
                self.hot_tes.incentives.macrs_bonus_pct,
                0
            )
            storage_techs.append('HotTES')
            storage_power_cost.append(0.0)
            storage_energy_cost.append(HotTESCostPerKWH)
            #Note: power not sized in REopt; assume full charge or discharge in one timestep.
            storage_min_power.append(self.hot_tes.min_kwh / self.steplength)
            storage_max_power.append(self.hot_tes.max_kwh / self.steplength)
            storage_min_energy.append(self.hot_tes.min_kwh)
            storage_max_energy.append(self.hot_tes.max_kwh)
            storage_decay_rate.append(self.hot_tes.thermal_decay_rate_fraction)

        if self.cold_tes is not None:
            ColdTESCostPerKWHT = setup_capital_cost_incentive(self.cold_tes.installed_cost_us_dollars_per_kwht,  # use full cost as basis
                                                        0,
                                                        0,
                                                        sf.owner_discount_pct,
                                                        sf.owner_tax_pct,
                                                        0,
                                                        self.cold_tes.incentives.macrs_schedule,
                                                        self.cold_tes.incentives.macrs_bonus_pct,
                                                        0)
            storage_techs.append('ColdTES')
            storage_power_cost.append(0.0)
            storage_energy_cost.append(ColdTESCostPerKWHT)
            #Note: power not sized in REopt; assume full charge or discharge in one timestep.
            storage_min_power.append(self.cold_tes.min_kwht / self.steplength)
            storage_max_power.append(self.cold_tes.max_kwht / self.steplength)
            storage_min_energy.append(self.cold_tes.min_kwht)
            storage_max_energy.append(self.cold_tes.max_kwht)
            storage_decay_rate.append(self.cold_tes.thermal_decay_rate_fraction)

        thermal_storage_techs = storage_techs[1:]
        hot_tes_techs = [] if self.hot_tes is None else ['HotTES']
        cold_tes_techs = [] if self.cold_tes is None else ['ColdTES']

        return storage_techs, thermal_storage_techs, hot_tes_techs, \
            cold_tes_techs, storage_power_cost, storage_energy_cost, \
            storage_min_power, storage_max_power, storage_min_energy, \
            storage_max_energy, storage_decay_rate

    def _get_FlexTechsCOP(self, techs):

        cop = list()
        max_elec_penalty = list()

        for tech in techs:
            single_tech_op = list()
            if eval('self.' + tech) is not None:
                if tech in ['wher']:
                    cop.extend([1.0] * self.n_timesteps)
                    single_tech_op.extend([1.0] * self.n_timesteps)
                elif tech in ['ac', 'hp', 'whhp']:
                    for val in eval('self.' + tech + '.cop'):
                        cop.append(float(val))
                        single_tech_op.append((1/float(val))*100)
                else:
                    pass
                if len(single_tech_op)>0:
                    max_elec_penalty.append(single_tech_op)

        if len([sum(i) for i in zip(*max_elec_penalty)]) > 0:
            max_elec_penalty = [sum(i)*100 for i in zip(*max_elec_penalty)]
        else:
            max_elec_penalty = [0.0] * self.n_timesteps
        return cop, max_elec_penalty

    def _get_RC_inputs(self, use_flexloads_model):

        if use_flexloads_model:
            return self.rc.a_matrix, self.rc.b_matrix, self.rc.u_inputs, self.rc.n_temp_nodes, self.rc.n_input_nodes
        else:
            return [0.0], [0.0], [0.0]*self.n_timesteps, 1, 1

    def _get_HVAC_inputs(self):
        shr = [] if self.ac is None else self.ac.shr
        dse = []
        fan_power_ratio = []
        techs = ['ac', 'hp']
        for tech in techs:
            if eval('self.' + tech) is not None:
                dse.append(float(eval('self.' + tech + '.dse')))
                fan_power_ratio.append(float(eval('self.' + tech + '.fan_power_ratio')))
            else:
                dse.append(1.0)
                fan_power_ratio.append(0.0)

        return shr, dse, fan_power_ratio

    def _get_WH_inputs(self):
        if self.wher == None and self.whhp == None:
            return False, [0.0], [0.0], [0.0] * self.n_timesteps, [0.0], 1, 1, 1, 1, 0.0, 0.0, 0.0, 0.0
        else:
            return True, self.hot_water_tank.a_matrix, self.hot_water_tank.b_matrix, self.hot_water_tank.u_inputs, self.hot_water_tank.init_temperatures_degC, \
                   self.hot_water_tank.n_temp_nodes, self.hot_water_tank.n_input_nodes, self.hot_water_tank.injection_node, self.hot_water_tank.water_node, \
                   self.hot_water_tank.temperature_lower_bound_degC, self.hot_water_tank.temperature_upper_bound_degC, self.hot_water_tank.comfort_temp_limit_degC, \
                   self.hot_water_tank.comfort_WH_value_usd_per_degC

    def _get_export_curtailment_params(self, techs, export_rates, net_metering_limit_kw):
        """
        :param techs: list of string
        :param export_rates: list of lists from UrdbParse, rates in order of the export tiers:
            1. Net metering [NEM]
            2. Wholesale [WHL]
            3. Excess beyond site load [EXC]
        :returns
            rates_by_tech: list of lists
            techs_by_export_tier: dict with valid export_tiers as keys, lists of tech strings as values
            export_tiers: list of string
            techs_cannot_curtail: list of string
            filtered_export_rates: list of lists
        """
        rates_by_tech = list()  # ExportTiersByTech, list of lists, becomes indexed on techs in julia
        export_tiers = list()
        techs_by_export_tier = dict()
        techs_cannot_curtail = list()
        filtered_export_rates = list()

        if len(techs) > 0:
            net_metering = False
            any_can_net_meter = False
            for tech in techs:  # have to do these for loops because `any` changes the scope and can't access `self`
                if eval('self.' + tech.lower() + '.can_net_meter'):
                    any_can_net_meter = True
                    break
            if any_can_net_meter and net_metering_limit_kw > 0:
                net_metering = True
                filtered_export_rates.append(export_rates[0])
                export_tiers.append("NEM")
                techs_by_export_tier["NEM"] = list()

            wholesale_exporting = False
            any_can_wholesale = False
            for tech in techs:
                if eval('self.' + tech.lower() + '.can_wholesale'):
                    any_can_wholesale = True
                    break
            if any_can_wholesale and sum(export_rates[1]) != 0:
                wholesale_exporting = True
                filtered_export_rates.append(export_rates[1])
                export_tiers.append("WHL")
                techs_by_export_tier["WHL"] = list()

            exporting_beyond_site_load = False
            any_can_export_beyond_site_load = False
            for tech in techs:
                if eval('self.' + tech.lower() + '.can_export_beyond_site_load'):
                    any_can_export_beyond_site_load = True
                    break
            if any_can_export_beyond_site_load and sum(export_rates[2]) != 0:
                exporting_beyond_site_load = True
                filtered_export_rates.append(export_rates[2])
                export_tiers.append("EXC")
                techs_by_export_tier["EXC"] = list()

            for tech in techs:
                rates = list()
                if not tech.lower().endswith('nm') and net_metering:
                    # these techs can access NEM and curtailment rates, and are limited to the net_metering_limit_kw
                    if eval('self.' + tech.lower() + '.can_net_meter'):
                        rates.append("NEM")
                        techs_by_export_tier["NEM"].append(tech.upper())
                else:
                    # techs that end with 'nm' are the option to install capacity beyond the net metering capacity limit
                    # these techs can access wholesale and curtailment rates
                    if eval('self.' + tech.lower() + '.can_wholesale') and wholesale_exporting:
                        rates.append("WHL")
                        techs_by_export_tier["WHL"].append(tech.upper())
                if eval('self.' + tech.lower() + '.can_export_beyond_site_load') and exporting_beyond_site_load:
                    rates.append("EXC")
                    techs_by_export_tier["EXC"].append(tech.upper())
                rates_by_tech.append(rates)
                if not eval('self.' + tech.lower() + '.can_curtail'):
                    techs_cannot_curtail.append(tech.upper())

        return rates_by_tech, techs_by_export_tier, export_tiers, techs_cannot_curtail, filtered_export_rates

    def finalize(self):
        """
        necessary for writing out parameters that depend on which Techs are defined
        eg. in REopt ProdFactor: array (Tech,Load,TimeStep).
        Note: whether or not a given Tech can serve a given Load can also be controlled via TechToLoadMatrix
        :return: None
        """
        reopt_techs = self._get_REopt_techs(self.available_techs)
        reopt_techs_bau = self._get_REopt_techs(self.bau_techs)

        tech_class_min_size, techs_in_class = self._get_REopt_tech_classes(self.available_techs, False)
        tech_class_min_size_bau, techs_in_class_bau = self._get_REopt_tech_classes(self.bau_techs, True)

        flex_techs_cop, max_elec_penalty = self._get_FlexTechsCOP(self.available_techs)
        flex_techs_cop_bau, max_elec_penalty_bau = self._get_FlexTechsCOP(self.bau_techs)

        a_matrix, b_matrix, u_inputs, n_temp_nodes, n_input_nodes = self._get_RC_inputs(self.rc.use_flexloads_model)
        a_matrix_bau, b_matrix_bau, u_inputs_bau, n_temp_nodes_bau, n_input_nodes_bau = self._get_RC_inputs(
            self.rc.use_flexloads_model_bau)

        shr, dse, fan_power_ratio = self._get_HVAC_inputs()

        use_wh_model, a_matrix_wh, b_matrix_wh, u_inputs_wh, init_temperatures_degC_wh, n_temp_nodes_wh, n_input_nodes_wh, \
        injection_node_wh, water_node, temperature_lower_bound_degC, temperature_upper_bound_degC, comfort_temp_limit_degC, \
        comfort_WH_value_usd_per_degC = self._get_WH_inputs()

        tech_to_location, derate, om_cost_us_dollars_per_kw, \
            om_cost_us_dollars_per_kwh, om_cost_us_dollars_per_hr_per_kw_rated, production_factor, \
            charge_efficiency, discharge_efficiency, \
            electric_derate, chp_thermal_prod_factor = self._get_REopt_array_tech_load(self.available_techs)
        tech_to_location_bau, derate_bau, om_cost_us_dollars_per_kw_bau, \
            om_cost_us_dollars_per_kwh_bau, om_cost_us_dollars_per_hr_per_kw_rated_bau, production_factor_bau, \
            charge_efficiency_bau, discharge_efficiency_bau, \
            electric_derate_bau, chp_thermal_prod_factor_bau = self._get_REopt_array_tech_load(self.bau_techs)

        max_sizes, min_turn_down, max_sizes_location, min_allowable_size = self._get_REopt_tech_max_sizes_min_turn_down(
            self.available_techs)
        max_sizes_bau, min_turn_down_bau, max_sizes_location_bau, min_allowable_size_bau = self._get_REopt_tech_max_sizes_min_turn_down(
            self.bau_techs, bau=True)

        levelization_factor, pwf_e, pwf_om, two_party_factor, \
        pwf_boiler_fuel, pwf_chp_fuel, pwf_fuel_by_tech = self._get_REopt_pwfs(self.available_techs)
        levelization_factor_bau, pwf_e_bau, pwf_om_bau, two_party_factor_bau, \
        pwf_boiler_fuel_bau, pwf_chp_fuel_bau, pwf_fuel_by_tech_bau = self._get_REopt_pwfs(self.bau_techs)

        pwf_prod_incent, max_prod_incent, max_size_for_prod_incent, production_incentive_rate \
            = self._get_REopt_production_incentives(self.available_techs)
        pwf_prod_incent_bau, max_prod_incent_bau, max_size_for_prod_incent_bau, production_incentive_rate_bau \
            = self._get_REopt_production_incentives(self.bau_techs)

        cap_cost_slope, cap_cost_x, cap_cost_yint, n_segments = self._get_REopt_cost_curve(self.available_techs)
        cap_cost_slope_bau, cap_cost_x_bau, cap_cost_yint_bau, n_segments_bau = self._get_REopt_cost_curve(
            self.bau_techs)

        storage_techs, thermal_storage_techs, hot_tes_techs, \
            cold_tes_techs, storage_power_cost, storage_energy_cost, \
            storage_min_power, storage_max_power, storage_min_energy, \
            storage_max_energy, storage_decay_rate = self._get_REopt_storage_techs_and_params()

        parser = UrdbParse(big_number=big_number, elec_tariff=self.elec_tariff,
                           techs=get_techs_not_none(self.available_techs, self),
                           bau_techs=get_techs_not_none(self.bau_techs, self))
        tariff_args = parser.parse_rate(self.elec_tariff.utility_name, self.elec_tariff.rate_name)
        TechToNMILMapping, TechsByNMILRegime, NMIL_regime = self._get_REopt_techToNMILMapping(self.available_techs)
        TechToNMILMapping_bau, TechsByNMILRegime_bau, NMIL_regime_bau = self._get_REopt_techToNMILMapping(self.bau_techs)
        if len(NMIL_regime) == 0:
            NMILLimits = []
        else:
            NMILLimits = [self.elec_tariff.net_metering_limit_kw, self.elec_tariff.interconnection_limit_kw,
                          self.elec_tariff.interconnection_limit_kw * 10]
        if len(NMIL_regime_bau) == 0:
            NMILLimits_bau = []
        else:
            NMILLimits_bau = [self.elec_tariff.net_metering_limit_kw, self.elec_tariff.interconnection_limit_kw,
                              self.elec_tariff.interconnection_limit_kw * 10]
        self.year_one_energy_cost_series_us_dollars_per_kwh = parser.energy_rates_summary
        self.year_one_demand_cost_series_us_dollars_per_kw = parser.demand_rates_summary

        subdivisions = ['CapCost']

        subdivisions_by_tech = self._get_tech_subsets(reopt_techs)
        subdivisions_by_tech_bau = self._get_tech_subsets(reopt_techs_bau)

        # There are no cost curves yet, but incentive size limits and existing techs require cost curve segments
        # TODO: create this array in _get_REopt_cost_curve?
        seg_by_tech_subdivision = list()
        seg_by_tech_subdivision_bau = list()
        for _ in subdivisions:
            for _ in reopt_techs:
                seg_by_tech_subdivision.append(n_segments)
            for  _ in reopt_techs_bau:
                seg_by_tech_subdivision_bau.append(n_segments_bau)

        # TODO: switch back to cap_cost_x input since we are just repeating its values?
        segment_min_size = []
        for j in range(0, len(cap_cost_x), n_segments+1):
            for _ in subdivisions:
                for i in range(j, n_segments+j):
                    segment_min_size.append(max(min_allowable_size[int(j/(n_segments+1))], cap_cost_x[i]))

        segment_min_size_bau = []
        for j in range(0, len(cap_cost_x_bau), n_segments_bau+1):
            for _ in subdivisions:
                for i in range(j, n_segments_bau+j):
                    segment_min_size_bau.append(max(min_allowable_size_bau[int(j/(n_segments+1))], cap_cost_x_bau[i]))

        segment_max_size = []
        for j in range(0, len(cap_cost_x), n_segments+1):
            for _ in subdivisions:
                for i in range(j, n_segments+j):
                    segment_max_size.append(cap_cost_x[i+1])

        segment_max_size_bau = []
        for j in range(0, len(cap_cost_x_bau), n_segments_bau+1):
            for _ in subdivisions:
                for i in range(j, n_segments_bau+j):
                    segment_max_size_bau.append(cap_cost_x_bau[i+1])

        grid_charge_efficiency = self.storage.rectifier_efficiency_pct * self.storage.internal_efficiency_pct**0.5

        fb_techs = [t for t in reopt_techs if t in self.fuel_burning_techs]
        fb_techs_bau = [t for t in reopt_techs_bau if t in self.fuel_burning_techs]

        techs_no_turndown = [t for t in reopt_techs if t.startswith("PV") or t.startswith("WIND")]
        techs_no_turndown_bau = [t for t in reopt_techs_bau if t.startswith("PV") or t.startswith("WIND")]

        electric_techs = [t for t in reopt_techs if t.startswith("PV") or t.startswith("WIND") or t.startswith("GENERATOR") or t.startswith("CHP")]
        electric_techs_bau = [t for t in reopt_techs_bau if t.startswith("PV") or t.startswith("WIND") or t.startswith("GENERATOR") or t.startswith("CHP")]

        flex_techs = [t for t in reopt_techs if t.startswith("AC") or t.startswith("HP") or t.startswith("WHER") or t.startswith("WHHP")]
        flex_techs_bau = [t for t in reopt_techs_bau if t.startswith("AC") or t.startswith("HP") or t.startswith("WHER") or t.startswith("WHHP")]

        wh_techs = [t for t in reopt_techs if t.startswith("WHER") or t.startswith("WHHP")]
        wh_techs_bau = [t for t in reopt_techs_bau if t.startswith("WHER") or t.startswith("WHHP")]

        time_steps_with_grid, time_steps_without_grid = self._get_time_steps_with_grid()

        rates_by_tech, techs_by_export_tier, export_tiers, techs_cannot_curtail, export_rates = \
            self._get_export_curtailment_params(reopt_techs, tariff_args.grid_export_rates,
                                                self.elec_tariff.net_metering_limit_kw)
        rates_by_tech_bau, techs_by_export_tier_bau, export_tiers_bau, techs_cannot_curtail_bau, export_rates_bau = \
            self._get_export_curtailment_params(reopt_techs_bau, tariff_args.grid_export_rates_bau,
                                                self.elec_tariff.net_metering_limit_kw)

        # Populate heating (convert to kw/kwh) and cooling loads with zeros if not included in model.
        if self.heating_load != None:
            heating_load = [self.heating_load.load_list[i] * MMBTU_TO_KWH for i in range(len(self.heating_load.load_list))]
        else:
            heating_load = [0.0 for _ in self.load.load_list]
        if self.LoadProfile["annual_cooling_kwh"] > 0.0:
            cooling_load = self.cooling_load.load_list
            # Zero out cooling load for outage hours
            if time_steps_without_grid not in [None, []]:
                for outage_time_step in time_steps_without_grid:
                    cooling_load[outage_time_step-1] = 0.0
                    self.LoadProfile["year_one_chiller_electric_load_series_kw"][outage_time_step-1] = 0.0
                self.LoadProfile["annual_cooling_kwh"] = sum(cooling_load) / self.elecchl_cop * self.steplength
        else:
            cooling_load = [0.0 for _ in self.load.load_list]

        # Create non-cooling electric load which is ElecLoad in the reopt.jl model
        # cooling_load is thermal, so convert to electric and subtract from total electric load to get non_cooling
        non_cooling_electric_load = [self.load.load_list[ts] - cooling_load[ts] / self.cooling_load.chiller_cop for ts in range(len(self.load.load_list))]
        non_cooling_electric_load_bau = [self.load.bau_load_list[ts] - cooling_load[ts] / self.cooling_load.chiller_cop for ts in range(len(self.load.bau_load_list))]

        sf = self.site.financial

        ### Populate CHP, heating, cooling technologies and efficiencies
        chp_techs = [t for t in reopt_techs if t.lower().startswith('chp')]
        chp_techs_bau = [t for t in reopt_techs_bau if t.lower().startswith('chp')]

        electric_chillers = [t for t in reopt_techs if t.lower().startswith('elecchl')]
        electric_chillers_bau = [t for t in reopt_techs_bau if t.lower().startswith('elecchl')]

        absorption_chillers = [t for t in reopt_techs if t.lower().startswith('absorpchl')]
        absorption_chillers_bau = [t for t in reopt_techs_bau if t.lower().startswith('absorpchl')]

        cooling_techs = [t for t in reopt_techs if t.lower().startswith('elecchl') or t.lower().startswith('absorpchl')]
        cooling_techs_bau = [t for t in reopt_techs_bau if t.lower().startswith('elecchl') or t.lower().startswith('absorpchl')]

        heating_techs = [t for t in reopt_techs if t.lower().startswith('chp') or t.lower().startswith('boiler')]
        heating_techs_bau = [t for t in reopt_techs_bau if t.lower().startswith('chp') or t.lower().startswith('boiler')]

        boiler_techs = [t for t in reopt_techs if t.lower().startswith('boiler')]
        boiler_techs_bau = [t for t in reopt_techs_bau if t.lower().startswith('boiler')]

        boiler_efficiency = self.boiler.boiler_efficiency if self.boiler != None else 1.0
        elec_chiller_cop = self.elecchl.chiller_cop if self.elecchl != None else 1.0

        if self.chp is not None:
            cooling_thermal_factor = self.chp.cooling_thermal_factor
        else:
            cooling_thermal_factor = 1.0

        absorp_chiller_cop = self.absorpchl.chiller_cop * cooling_thermal_factor if self.absorpchl != None else 1.0
        absorp_chiller_elec_cop = self.absorpchl.chiller_elec_cop if self.absorpchl != None else 1.0

        # Fuel burning parameters and other CHP-specific parameters
        fuel_params = FuelParams(big_number=big_number, elec_tariff=self.elec_tariff, fuel_tariff=self.fuel_tariff,
                           generator=eval('self.generator'))

        fuel_costs, fuel_limit, fuel_types, techs_by_fuel_type, fuel_burn_slope, fuel_burn_intercept \
            = fuel_params._get_fuel_burning_tech_params(reopt_techs, generator=eval('self.generator'),
                                                        chp=eval('self.chp'))
        fuel_costs_bau, fuel_limit_bau, fuel_types_bau, techs_by_fuel_type_bau, fuel_burn_slope_bau, \
            fuel_burn_intercept_bau =  fuel_params._get_fuel_burning_tech_params(reopt_techs_bau,
                                                        generator=eval('self.generator'), chp=eval('self.chp'))

        chp_fuel_burn_intercept, chp_thermal_prod_slope, chp_thermal_prod_intercept, chp_derate \
            = fuel_params._get_chp_unique_params(chp_techs, chp=eval('self.chp'))
        chp_fuel_burn_intercept_bau, chp_thermal_prod_slope_bau, chp_thermal_prod_intercept_bau, chp_derate_bau \
            = fuel_params._get_chp_unique_params(chp_techs_bau, chp=eval('self.chp'))

        self.reopt_inputs = {
            'Tech': reopt_techs,
            'TechToLocation': tech_to_location,
            'MaxSizesLocation': max_sizes_location,
            'TechClass': self.available_tech_classes,
            'TurbineDerate': derate,
            'NMILRegime': NMIL_regime,
            'MaxSize': max_sizes,
            'TechClassMinSize': tech_class_min_size,
            'MinTurndown': min_turn_down,
            'LevelizationFactor': levelization_factor,
            'pwf_e': pwf_e,
            'pwf_om': pwf_om,
            'pwf_fuel': pwf_fuel_by_tech,
            'two_party_factor': two_party_factor,
            'pwf_prod_incent': pwf_prod_incent,
            'MaxProdIncent': max_prod_incent,
            'MaxSizeForProdIncent': max_size_for_prod_incent,
            'CapCostSlope': cap_cost_slope,
            'CapCostX': cap_cost_x,
            'CapCostYInt': cap_cost_yint,
            'r_tax_owner': sf.owner_tax_pct,
            'r_tax_offtaker': sf.offtaker_tax_pct,
            'StorageCostPerKW': storage_power_cost,
            'StorageCostPerKWH': storage_energy_cost,
            'OMperUnitSize': om_cost_us_dollars_per_kw,
            'OMcostPerUnitProd': om_cost_us_dollars_per_kwh,
            'OMcostPerUnitHourPerSize': om_cost_us_dollars_per_hr_per_kw_rated,
            'analysis_years': int(sf.analysis_years),
            'NumRatchets': tariff_args.demand_num_ratchets,
            'FuelBinCount': tariff_args.energy_tiers_num,
            'DemandBinCount': tariff_args.demand_tiers_num,
            'DemandMonthsBinCount': tariff_args.demand_month_tiers_num,
            'DemandRatesMonth': tariff_args.demand_rates_monthly,
            'DemandRates': tariff_args.demand_rates_tou,
            'TimeStepRatchets': tariff_args.demand_ratchets_tou,
            'MaxDemandInTier': tariff_args.demand_max_in_tiers,
            'MaxUsageInTier': tariff_args.energy_max_in_tiers,
            'MaxDemandMonthsInTier': tariff_args.demand_month_max_in_tiers,
            'FixedMonthlyCharge': tariff_args.fixed_monthly_charge,
            'AnnualMinCharge': tariff_args.annual_min_charge,
            'MonthlyMinCharge': tariff_args.min_monthly_charge,
            'DemandLookbackMonths': tariff_args.demand_lookback_months,
            'DemandLookbackRange': tariff_args.demand_lookback_range,
            'DemandLookbackPercent': tariff_args.demand_lookback_percent,
            'TimeStepRatchetsMonth': tariff_args.demand_ratchets_monthly,
            'TimeStepCount': self.n_timesteps,
            'TimeStepScaling': self.steplength,
            'AnnualElecLoadkWh': self.load.annual_kwh,
            'StorageMinChargePcent': self.storage.soc_min_pct,
            'InitSOC': self.storage.soc_init_pct,
            'NMILLimits': NMILLimits,
            'TechToNMILMapping': TechToNMILMapping,
            'CapCostSegCount': n_segments,
            'CoincidentPeakLoadTimeSteps': self.elec_tariff.coincident_peak_load_active_timesteps,
            'CoincidentPeakRates': self.elec_tariff.coincident_peak_load_charge_us_dollars_per_kw,
            'CoincidentPeakPeriodCount': self.elec_tariff.coincident_peak_num_periods,
            'FuelCost': fuel_costs,
            'ElecRate': tariff_args.energy_costs,
            'GridExportRates': export_rates,
            'FuelBurnSlope': fuel_burn_slope,
            'FuelBurnYInt': fuel_burn_intercept,
            'ProductionIncentiveRate': production_incentive_rate,
            'ProductionFactor': production_factor,
            'ElecLoad': non_cooling_electric_load,
            'FuelLimit': fuel_limit,
            'ChargeEfficiency': charge_efficiency,
            'GridChargeEfficiency': grid_charge_efficiency,
            'DischargeEfficiency': discharge_efficiency,
            'StorageMinSizeEnergy': storage_min_energy,
            'StorageMaxSizeEnergy': storage_max_energy,
            'StorageMinSizePower': storage_min_power,
            'StorageMaxSizePower': storage_max_power,
            'StorageMinSOC': [self.storage.soc_min_pct, self.hot_tes.soc_min_pct, self.cold_tes.soc_min_pct],
            'StorageInitSOC': [self.storage.soc_init_pct, self.hot_tes.soc_init_pct, self.cold_tes.soc_init_pct],
            'StorageCanGridCharge': self.storage.canGridCharge,
            'SegmentMinSize': segment_min_size,
            'SegmentMaxSize': segment_max_size,
            'Storage': storage_techs,
            'FuelType': fuel_types,
            'Subdivision': subdivisions,
            'PricingTierCount': tariff_args.energy_tiers_num,
            'ElecStorage': ['Elec'],
            'SubdivisionByTech': subdivisions_by_tech,
            'SegByTechSubdivision': seg_by_tech_subdivision,
            'TechsInClass': techs_in_class,
            'TechsByFuelType': techs_by_fuel_type,
            'ElectricTechs': electric_techs,
            'FuelBurningTechs': fb_techs,
            'TechsNoTurndown': techs_no_turndown,
            'ExportTiers': export_tiers,
            'TimeStepsWithGrid': time_steps_with_grid,
            'TimeStepsWithoutGrid': time_steps_without_grid,
            'ExportTiersByTech': rates_by_tech,
            'TechsByExportTier': [techs_by_export_tier[k] for k in export_tiers],
            'ExportTiersBeyondSiteLoad': ["EXC"],
            'ElectricDerate': electric_derate,
            'TechsByNMILRegime': TechsByNMILRegime,
            'TechsCannotCurtail': techs_cannot_curtail,
            'TechsByNMILRegime': TechsByNMILRegime,
            'HeatingLoad': heating_load,
            'CoolingLoad': cooling_load,
            'ThermalStorage': thermal_storage_techs,
            'HotTES': hot_tes_techs,
            'ColdTES': cold_tes_techs,
            'CHPTechs': chp_techs,
            'ElectricChillers': electric_chillers,
            'AbsorptionChillers': absorption_chillers,
            'CoolingTechs': cooling_techs,
            'HeatingTechs': heating_techs,
            'BoilerTechs': boiler_techs,
            'BoilerEfficiency': boiler_efficiency,
            'ElectricChillerCOP': elec_chiller_cop,
            'AbsorptionChillerCOP': absorp_chiller_cop,
            'AbsorptionChillerElecCOP': absorp_chiller_elec_cop,
            'CHPThermalProdSlope': chp_thermal_prod_slope,
            'CHPThermalProdIntercept': chp_thermal_prod_intercept,
            'FuelBurnYIntRate': chp_fuel_burn_intercept,
            'CHPThermalProdFactor': chp_thermal_prod_factor,
            'CHPDoesNotReduceDemandCharges': tariff_args.chp_does_not_reduce_demand_charges,
            'CHPStandbyCharge': tariff_args.chp_standby_rate_us_dollars_per_kw_per_month,
            'StorageDecayRate': storage_decay_rate,
            'AddSOCIncentive': self.add_soc_incentive,
            # Flex loads
            'FlexTechs': flex_techs,
            'HVACTechs': ["AC", "HP"],
            'UseFlexLoadsModel': self.rc.use_flexloads_model,
            'AMatrix': a_matrix,
            'BMatrix': b_matrix,
            'UInputs': u_inputs,
            'SHR': shr,
            'InitTemperatures': self.rc.init_temperatures,
            'TempNodesCount': n_temp_nodes,
            'InputNodesCount': n_input_nodes,
            'InjectionNode': self.rc.injection_node,
            'SpaceNode': self.rc.space_node,
            'TempLowerBound': self.rc.temperature_lower_bound,
            'TempUpperBound': self.rc.temperature_upper_bound,
            'ComfortTempLimitHP': self.rc.comfort_temp_lower_bound_degC,
            'ComfortTempLimitAC': self.rc.comfort_temp_upper_bound_degC,
            'HVACComfortValue': self.rc.comfort_HVAC_value_usd_per_degC,
            'FlexTechsCOP': flex_techs_cop,
            'DSE': dse,
            'FanPowerRatio': fan_power_ratio,
            'MaxElecPenalty': max_elec_penalty,
            # Water heater
            'UseWaterHeaterModel': use_wh_model,
            'AMatrixWH': a_matrix_wh,
            'BMatrixWH': b_matrix_wh,
            'UInputsWH': u_inputs_wh,
            'InitTemperaturesWH': init_temperatures_degC_wh,
            'TempNodesCountWH': n_temp_nodes_wh,
            'InputNodesCountWH': n_input_nodes_wh,
            'InjectionNodeWH': injection_node_wh,
            'WaterNode': water_node,
            'TempLowerBoundWH': temperature_lower_bound_degC,
            'TempUpperBoundWH': temperature_upper_bound_degC,
            'ComfortTempLimitWH': comfort_temp_limit_degC,
            'WHComfortValue': comfort_WH_value_usd_per_degC,
            'WaterHeaterTechs': wh_techs
            }
        ## Uncomment the following and run a scenario to get an updated modelinputs.json for creating Julia system image
        # import json
        # json.dump(test_xl, open("C:/Users/xli1/Documents/PROJECTS/_FY21/Nova/debug/modelinputs_f2.json", "w"))

        self.reopt_inputs_bau = {
            'Tech': reopt_techs_bau,
            'TechToLocation': tech_to_location_bau,
            'MaxSizesLocation': max_sizes_location_bau,
            'TechClass': self.available_tech_classes,
            'NMILRegime': NMIL_regime_bau,
            'TurbineDerate': derate_bau,
            'MaxSize': max_sizes_bau,
            'TechClassMinSize': tech_class_min_size_bau,
            'MinTurndown': min_turn_down_bau,
            'LevelizationFactor': levelization_factor_bau,
            'pwf_e': pwf_e_bau,
            'pwf_om': pwf_om_bau,
            'pwf_fuel': pwf_fuel_by_tech_bau,
            'two_party_factor': two_party_factor_bau,
            'pwf_prod_incent': pwf_prod_incent_bau,
            'MaxProdIncent': max_prod_incent_bau,
            'MaxSizeForProdIncent': max_size_for_prod_incent_bau,
            'CapCostSlope': cap_cost_slope_bau,
            'CapCostX': cap_cost_x_bau,
            'CapCostYInt': cap_cost_yint_bau,
            'r_tax_owner': sf.owner_tax_pct,
            'r_tax_offtaker': sf.offtaker_tax_pct,
            'StorageCostPerKW': storage_power_cost,
            'StorageCostPerKWH': storage_energy_cost,
            'OMperUnitSize': om_cost_us_dollars_per_kw_bau,
            'OMcostPerUnitProd': om_cost_us_dollars_per_kwh_bau,
            'OMcostPerUnitHourPerSize': om_cost_us_dollars_per_hr_per_kw_rated_bau,
            'analysis_years': int(sf.analysis_years),
            'NumRatchets': tariff_args.demand_num_ratchets,
            'FuelBinCount': tariff_args.energy_tiers_num,
            'DemandBinCount': tariff_args.demand_tiers_num,
            'DemandMonthsBinCount': tariff_args.demand_month_tiers_num,
            'DemandRatesMonth': tariff_args.demand_rates_monthly,
            'DemandRates': tariff_args.demand_rates_tou,
            'TimeStepRatchets': tariff_args.demand_ratchets_tou,
            'MaxDemandInTier': tariff_args.demand_max_in_tiers,
            'MaxUsageInTier': tariff_args.energy_max_in_tiers,
            'MaxDemandMonthsInTier': tariff_args.demand_month_max_in_tiers,
            'FixedMonthlyCharge': tariff_args.fixed_monthly_charge,
            'AnnualMinCharge': tariff_args.annual_min_charge,
            'MonthlyMinCharge': tariff_args.min_monthly_charge,
            'DemandLookbackMonths': tariff_args.demand_lookback_months,
            'DemandLookbackRange': tariff_args.demand_lookback_range,
            'DemandLookbackPercent': tariff_args.demand_lookback_percent,
            'TimeStepRatchetsMonth': tariff_args.demand_ratchets_monthly,
            'TimeStepCount': self.n_timesteps,
            'TimeStepScaling': self.steplength,
            'AnnualElecLoadkWh': self.load.annual_kwh,
            'StorageMinChargePcent': self.storage.soc_min_pct,
            'InitSOC': self.storage.soc_init_pct,
            'NMILLimits': NMILLimits_bau,
            'TechToNMILMapping': TechToNMILMapping_bau,
            'CapCostSegCount': n_segments_bau,
            'CoincidentPeakLoadTimeSteps': self.elec_tariff.coincident_peak_load_active_timesteps,
            'CoincidentPeakRates': self.elec_tariff.coincident_peak_load_charge_us_dollars_per_kw,
            'CoincidentPeakPeriodCount': self.elec_tariff.coincident_peak_num_periods,
	        'FuelCost': fuel_costs_bau,
	        'ElecRate': tariff_args.energy_costs_bau,
	        'GridExportRates': export_rates_bau,
	        'FuelBurnSlope': fuel_burn_slope_bau,
	        'FuelBurnYInt': fuel_burn_intercept_bau,
	        'ProductionIncentiveRate': production_incentive_rate_bau,
	        'ProductionFactor': production_factor_bau,
	        'ElecLoad': non_cooling_electric_load_bau,
	        'FuelLimit': fuel_limit_bau,
	        'ChargeEfficiency': charge_efficiency_bau,
	        'GridChargeEfficiency': grid_charge_efficiency,
	        'DischargeEfficiency': discharge_efficiency_bau,
	        'StorageMinSizeEnergy': [0.0 for _ in storage_techs],
	        'StorageMaxSizeEnergy': [0.0 for _ in storage_techs],
	        'StorageMinSizePower': [0.0 for _ in storage_techs],
	        'StorageMaxSizePower': [0.0 for _ in storage_techs],
	        'StorageMinSOC': [0.0 for _ in storage_techs],
	        'StorageInitSOC': [0.0 for _ in storage_techs],
            'StorageCanGridCharge': self.storage.canGridCharge,
            'SegmentMinSize': segment_min_size_bau,
            'SegmentMaxSize': segment_max_size_bau,
            'Storage': storage_techs,
            'FuelType': fuel_types_bau,
            'Subdivision': subdivisions,
            'PricingTierCount': tariff_args.energy_tiers_num,
            'ElecStorage': [],
            'SubdivisionByTech': subdivisions_by_tech_bau,
            'SegByTechSubdivision': seg_by_tech_subdivision_bau,
            'TechsInClass': techs_in_class_bau,
            'TechsByFuelType': techs_by_fuel_type_bau,
            'ElectricTechs': electric_techs_bau,
            'FuelBurningTechs': fb_techs_bau,
            'TechsNoTurndown': techs_no_turndown_bau,
            'ExportTiers': export_tiers_bau,
            'TimeStepsWithGrid': time_steps_with_grid,
            'TimeStepsWithoutGrid': time_steps_without_grid,
            'ExportTiersByTech': rates_by_tech_bau,
            'TechsByExportTier': [techs_by_export_tier_bau[k] for k in export_tiers_bau],
            'ExportTiersBeyondSiteLoad':  ["EXC"],
            'ElectricDerate': electric_derate_bau,
            'TechsByNMILRegime': TechsByNMILRegime_bau,
            'TechsCannotCurtail': techs_cannot_curtail_bau,
            'TechsByNMILRegime': TechsByNMILRegime_bau,
            'HeatingLoad': heating_load,
            'CoolingLoad': cooling_load,
            'ThermalStorage': thermal_storage_techs,
            'HotTES': hot_tes_techs,
            'ColdTES': cold_tes_techs,
            'CHPTechs': chp_techs_bau,
            'ElectricChillers': electric_chillers_bau,
            'AbsorptionChillers': absorption_chillers_bau,
            'CoolingTechs': cooling_techs_bau,
            'HeatingTechs': heating_techs_bau,
            'BoilerTechs': boiler_techs_bau,
            'BoilerEfficiency': boiler_efficiency,
            'ElectricChillerCOP': elec_chiller_cop,
            'AbsorptionChillerCOP': absorp_chiller_cop,
            'AbsorptionChillerElecCOP': absorp_chiller_elec_cop,
            'CHPThermalProdSlope': chp_thermal_prod_slope_bau,
            'CHPThermalProdIntercept': chp_thermal_prod_intercept_bau,
            'FuelBurnYIntRate': chp_fuel_burn_intercept_bau,
            'CHPThermalProdFactor': chp_thermal_prod_factor_bau,
            'CHPDoesNotReduceDemandCharges': tariff_args.chp_does_not_reduce_demand_charges,
            'CHPStandbyCharge': tariff_args.chp_standby_rate_us_dollars_per_kw_per_month,
            'StorageDecayRate': storage_decay_rate,
            'AddSOCIncentive': self.add_soc_incentive,
            # Flex loads
            'FlexTechs': flex_techs_bau,
            'HVACTechs': ["AC", "HP"],
            'UseFlexLoadsModel': self.rc.use_flexloads_model_bau,
            'AMatrix': a_matrix_bau,
            'BMatrix': b_matrix_bau,
            'UInputs': u_inputs_bau,
            'SHR': shr,
            'InitTemperatures': self.rc.init_temperatures,
            'TempNodesCount': n_temp_nodes_bau,
            'InputNodesCount': n_input_nodes_bau,
            'InjectionNode': self.rc.injection_node,
            'SpaceNode': self.rc.space_node,
            'TempLowerBound': self.rc.temperature_lower_bound,
            'TempUpperBound': self.rc.temperature_upper_bound,
            'ComfortTempLimitHP': self.rc.comfort_temp_lower_bound_degC,
            'ComfortTempLimitAC': self.rc.comfort_temp_upper_bound_degC,
            'HVACComfortValue': self.rc.comfort_HVAC_value_usd_per_degC,
            'FlexTechsCOP': flex_techs_cop_bau,
            'DSE': dse,
            'FanPowerRatio': fan_power_ratio,
            'MaxElecPenalty': max_elec_penalty_bau,
            # Water heater
            'UseWaterHeaterModel': use_wh_model,
            'AMatrixWH': a_matrix_wh,
            'BMatrixWH': b_matrix_wh,
            'UInputsWH': u_inputs_wh,
            'InitTemperaturesWH': init_temperatures_degC_wh,
            'TempNodesCountWH': n_temp_nodes_wh,
            'InputNodesCountWH': n_input_nodes_wh,
            'InjectionNodeWH': injection_node_wh,
            'WaterNode': water_node,
            'TempLowerBoundWH': temperature_lower_bound_degC,
            'TempUpperBoundWH': temperature_upper_bound_degC,
            'ComfortTempLimitWH': comfort_temp_limit_degC,
            'WHComfortValue': comfort_WH_value_usd_per_degC,
            'WaterHeaterTechs': wh_techs_bau
        }
