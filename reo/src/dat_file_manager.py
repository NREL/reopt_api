import os
import copy
from reo.src.urdb_parse import UrdbParse
from reo.utilities import annuity, annuity_degr, slope, intercept, insert_p_after_u_bp, insert_p_bp, \
    insert_u_after_p_bp, insert_u_bp, setup_capital_cost_incentive

big_number = 1e10
squarefeet_to_acre = 2.2957e-5


def _write_var(f, var, dat_var):
    f.write(dat_var + ": [\n")
    if isinstance(var, list):
        for v in var:
            if isinstance(v, list):  # elec_tariff contains list of lists
                f.write('[')
                for i in v:
                    f.write(str(i) + ' ')
                f.write(']\n')
            else:
                f.write(str(v) + "\n")
    else:
        f.write(str(var) + "\n")
    f.write("]\n")


def write_to_dat(path, var, dat_var, mode='w'):
    cmd_line_vars = (
        'DemandBinCount',
        'FuelBinCount',
        'NumRatchets',
    )
    with open(path, mode) as f:
        if dat_var in cmd_line_vars:
            f.write(dat_var + '=' + str(var) + '\n')
        else:
            _write_var(f, var, dat_var)


class Singleton(type):
    """
    metaclass for DatFileManager
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        else:
            # if passing a new run_id, replace old DFM with new one
            # probably only used when running tests, but could have application for parallel runs
            if 'run_id' in kwargs:
                    if kwargs['run_id'] != cls._instances.values()[0].run_id:
                        cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class DatFileManager:
    """
    writes dat files and creates command line strings for dat file paths
    """

    __metaclass__ = Singleton
    DAT = [None] * 20
    DAT_bau = [None] * 20
    pv = None
    pvnm = None
    util = None
    storage = None
    site = None
    elec_tariff = None

    available_techs = ['pv', 'pvnm', 'util']  # order is critical for REopt!
    available_tech_classes = ['PV', 'UTIL']  # this is a REopt 'class', not a python class
    available_loads = ['retail', 'wholesale', 'export', 'storage']  # order is critical for REopt!
    bau_techs = ['util']
    NMILRegime = ['BelowNM', 'NMtoIL', 'AboveIL']
    command_line_args = list()
    command_line_args_bau = list()
    
    def __init__(self, run_id, paths, n_timesteps=8760):
        self.run_id = run_id
        self.paths = paths
        self.n_timesteps = n_timesteps
        file_tail = str(run_id) + '.dat'
        file_tail_bau = str(run_id) + '_bau.dat'
        
        self.file_constant = os.path.join(paths.inputs, 'constant_' + file_tail)
        self.file_constant_bau = os.path.join(paths.inputs, 'constant_' + file_tail_bau)
        self.file_economics = os.path.join(paths.inputs, 'economics_' + file_tail)
        self.file_economics_bau = os.path.join(paths.inputs, 'economics_' + file_tail_bau)
        self.file_load_profile = os.path.join(paths.inputs, 'Load8760_' + file_tail)
        self.file_load_size = os.path.join(paths.inputs, 'LoadSize_' + file_tail)
        self.file_gis = os.path.join(paths.inputs, "GIS_" + file_tail)
        self.file_gis_bau = os.path.join(paths.inputs, "GIS_" + file_tail_bau)
        self.file_storage = os.path.join(paths.inputs, 'storage_' + file_tail)
        self.file_storage_bau = os.path.join(paths.inputs, 'storage_' + file_tail_bau)
        self.file_max_size = os.path.join(paths.inputs, 'maxsizes_' + file_tail)
        self.file_max_size_bau = os.path.join(paths.inputs, 'maxsizes_' + file_tail_bau)
        self.file_NEM = os.path.join(paths.inputs, 'NMIL_' + file_tail)
        self.file_NEM_bau = os.path.join(paths.inputs, 'NMIL_' + file_tail_bau)

        self.file_demand_periods = os.path.join(paths.utility, 'TimeStepsDemand.dat')
        self.file_demand_rates = os.path.join(paths.utility, 'DemandRate.dat')
        self.file_demand_rates_monthly = os.path.join(paths.utility, 'DemandRateMonth.dat')
        self.file_demand_ratchets_monthly = os.path.join(paths.utility, 'TimeStepsDemandMonth.dat')
        self.file_demand_lookback = os.path.join(paths.utility, 'LookbackMonthsAndPercent.dat')
        self.file_demand_num_ratchets = os.path.join(paths.utility, 'NumRatchets.dat')
        self.file_energy_rates = os.path.join(paths.utility, 'FuelCost.dat')
        self.file_energy_rates_bau = os.path.join(paths.utility, 'FuelCostBase.dat')
        self.file_energy_tiers_num = os.path.join(paths.utility, 'bins.dat')
        self.file_energy_burn_rate = os.path.join(paths.utility, 'FuelBurnRate.dat')
        self.file_energy_burn_rate_bau = os.path.join(paths.utility, 'FuelBurnRateBase.dat')
        self.file_max_in_tiers = os.path.join(paths.utility, 'UtilityTiers.dat')
        self.file_export_rates = os.path.join(paths.utility, 'ExportRates.dat')
        self.file_export_rates_bau = os.path.join(paths.utility, 'ExportRatesBase.dat')
        
        self.DAT[0] = "DAT1=" + "'" + self.file_constant + "'"
        self.DAT_bau[0] = "DAT1=" + "'" + self.file_constant_bau + "'"
        self.DAT[1] = "DAT2=" + "'" + self.file_economics + "'"
        self.DAT_bau[1] = "DAT2=" + "'" + self.file_economics_bau + "'"
        self.DAT[2] = "DAT3=" + "'" + self.file_load_size + "'"
        self.DAT_bau[2] = self.DAT[2]
        self.DAT[3] = "DAT4=" + "'" + self.file_load_profile + "'"
        self.DAT_bau[3] = self.DAT[3]
        self.DAT[4] = "DAT5=" + "'" + self.file_gis + "'"
        self.DAT_bau[4] = "DAT5=" + "'" + self.file_gis_bau + "'"
        self.DAT[5] = "DAT6=" + "'" + self.file_storage + "'"
        self.DAT_bau[5] = "DAT6=" + "'" + self.file_storage_bau + "'"
        self.DAT[6] = "DAT7=" + "'" + self.file_max_size + "'"
        self.DAT_bau[6] = "DAT7=" + "'" + self.file_max_size_bau + "'"
        self.DAT[16] = "DAT17=" + "'" + self.file_NEM + "'"
        self.DAT_bau[16] = "DAT17=" + "'" + self.file_NEM_bau + "'"

        DatFileManager.command_line_args.append("ScenarioNum=" + str(run_id))
        DatFileManager.command_line_args_bau.append("ScenarioNum=" + str(run_id))

    def _check_complete(self):
        if any(d is None for d in self.DAT) or any(d is None for d in self.DAT_bau):
            return False
        return True

    def add_load(self, load): 
        #  fill in W, X, S bins
        for _ in range(8760 * 3):
            load.load_list.append(big_number)
                              
        write_to_dat(self.file_load_profile, load.load_list, "LoadProfile")
        write_to_dat(self.file_load_size, load.annual_kwh, "AnnualElecLoad")

    def add_pv(self, pv):
        self.pv = pv
        self.pvnm = copy.deepcopy(pv)
        self.pvnm.nmil_regime = 'NMtoIL'

    def add_util(self, util):
        self.util = util

    def add_site(self, site):
        self.site = site

    def add_net_metering(self, net_metering_limit, interconnection_limit):

        # constant.dat contains NMILRegime
        # NMIL.dat contains NMILLimits and TechToNMILMapping

        TechToNMILMapping = self._get_REopt_techToNMILMapping(self.available_techs)
        TechToNMILMapping_bau = self._get_REopt_techToNMILMapping(self.bau_techs)

        write_to_dat(self.file_NEM,
                              [net_metering_limit, interconnection_limit, interconnection_limit*10],
                              'NMILLimits')
        write_to_dat(self.file_NEM, TechToNMILMapping, 'TechToNMILMapping', mode='a')

        write_to_dat(self.file_NEM_bau,
                              [net_metering_limit, interconnection_limit, interconnection_limit*10],
                              'NMILLimits')
        write_to_dat(self.file_NEM_bau, TechToNMILMapping_bau, 'TechToNMILMapping', mode='a')

    def add_storage(self, storage):
        self.storage = storage

        batt_level_coef = list()
        for batt_level in range(storage.level_count):
            for coef in storage.level_coefs:
                batt_level_coef.append(coef)

        # storage_bau.dat gets same definitions as storage.dat so that initializations don't fail in bau case
        # however, storage is typically 'turned off' by having max size set to zero in maxsizes_bau.dat
        write_to_dat(self.file_storage, batt_level_coef, 'BattLevelCoef')
        write_to_dat(self.file_storage_bau, batt_level_coef, 'BattLevelCoef')

        write_to_dat(self.file_storage, storage.soc_min, 'StorageMinChargePcent', mode='a')
        write_to_dat(self.file_storage_bau, storage.soc_min, 'StorageMinChargePcent', mode='a')

        write_to_dat(self.file_storage, storage.soc_init, 'InitSOC', mode='a')
        write_to_dat(self.file_storage_bau, storage.soc_init, 'InitSOC', mode='a')

        # efficiencies are defined in finalize method because their arrays depend on which Techs are defined

    def add_elec_tariff(self, elec_tariff):
        self.elec_tariff = elec_tariff
            
    def _get_REopt_pwfs(self, techs):

        sf = self.site.financials
        pwf_owner = annuity(sf.analysis_period, 0, sf.owner_discount_rate_nominal) # not used in REopt
        pwf_offtaker = annuity(sf.analysis_period, 0, sf.offtaker_discount_rate_nominal)  # not used in REopt
        pwf_om = annuity(sf.analysis_period, sf.rate_inflation, sf.owner_discount_rate_nominal)
        pwf_e = annuity(sf.analysis_period, sf.rate_escalation_nominal, sf.offtaker_discount_rate_nominal)
        # pwf_op = annuity(sf.analysis_period, sf.rate_escalation_nominal, sf.owner_discount_rate_nominal)

        if pwf_owner == 0 or sf.owner_tax_rate == 0:
            two_party_factor = 0
        else:
            two_party_factor = (pwf_offtaker * sf.offtaker_tax_rate) \
                                / (pwf_owner * sf.owner_tax_rate)

        levelization_factor = list()
        production_incentive_levelization_factor = list()

        for tech in techs:

            if eval('self.' + tech) is not None:

                if tech != 'util':

                    #################
                    # NOTE: economics.py uses real rates to calculate pv_levelization_factor and
                    #       pv_levelization_factor_production_incentive, need to change to nominal for consistency,
                    #       which may break some tests.
                    ################
                    levelization_factor.append(
                        round(
                            annuity_degr(sf.analysis_period, sf.rate_escalation,
                                         sf.offtaker_discount_rate,
                                         -eval('self.' + tech + '.degradation_rate')) / pwf_e
                            , 5
                        )
                    )
                    production_incentive_levelization_factor.append(
                        round(
                            annuity_degr(eval('self.' + tech + '.incentives.production_based.years'),
                                         sf.rate_escalation, sf.offtaker_discount_rate,
                                         -eval('self.' + tech + '.degradation_rate')) / \
                            annuity(eval('self.' + tech + '.incentives.production_based.years'),
                                    sf.rate_escalation_nominal, sf.offtaker_discount_rate_nominal)
                            , 5
                        )
                    )
                    #################
                    ################
                elif tech == 'util':

                    levelization_factor.append(self.util.degradation_rate)
                    production_incentive_levelization_factor.append(1.0)

        return levelization_factor, production_incentive_levelization_factor, pwf_e, pwf_om, two_party_factor

    def _get_REopt_production_incentives(self, techs):

        sf = self.site.financials
        pwf_prod_incent = list()
        prod_incent_rate = list()
        max_prod_incent = list()
        max_size_for_prod_incent = list()

        for tech in techs:

            if eval('self.' + tech) is not None:
                
                if tech != 'util':
    
                    pwf_prod_incent.append(
                        annuity(eval('self.' + tech + '.incentives.production_based.years'),
                                sf.rate_escalation_nominal, sf.offtaker_discount_rate_nominal)
                    )
                    max_prod_incent.append(
                        eval('self.' + tech + '.incentives.production_based.max_us_dollars_per_kw')
                    )
                    max_size_for_prod_incent.append(
                        eval('self.' + tech + '.incentives.production_based.max_kw')
                    )
    
                    for load in self.available_loads:
                        prod_incent_rate.append(
                            eval('self.' + tech + '.incentives.production_based.us_dollars_per_kw')
                        )
    
                elif tech == 'util':
    
                    pwf_prod_incent.append(0)
                    max_prod_incent.append(0)
                    max_size_for_prod_incent.append(0)
    
                    for load in self.available_loads:
                        prod_incent_rate.append(0)
                    
        return pwf_prod_incent, prod_incent_rate, max_prod_incent, max_size_for_prod_incent
        
    def _get_REopt_cost_curve(self, techs):

        regions = ['utility', 'state', 'federal', 'combined']
        cap_cost_slope = list()
        cap_cost_x = list()
        cap_cost_yint = list()

        for tech in techs:

            if eval('self.' + tech) is not None and tech != 'util':
                
                tech_incentives = dict()
                
                for region in regions[:-1]:
                    tech_incentives[region] = dict()
                    tech_incentives[region]['%'] = eval('self.' + tech + '.incentives.' + region + '.itc')
                    tech_incentives[region]['%_max'] = eval('self.' + tech + '.incentives.' + region + '.itc_max')
                    tech_incentives[region]['rebate'] = eval('self.' + tech + '.incentives.' + region + '.rebate')
                    tech_incentives[region]['rebate_max'] = eval('self.' + tech + '.incentives.' + region + '.rebate_max')

                # Cost curve
                xp_array_incent = dict()
                xp_array_incent['utility'] = [0.0, float(big_number/1e2)]  # kW
                yp_array_incent = dict()
                yp_array_incent['utility'] = [0.0, float(big_number/1e2 * eval('self.' + tech + '.cost_dollars_per_kw'))]  # $
                
                for r in range(len(regions)-1):
        
                    region = regions[r]
                    next_region = regions[r + 1]
        
                    # Apply incentives, initialize first value
                    xp_array_incent[next_region] = [0]
                    yp_array_incent[next_region] = [0]
        
                    # percentage based incentives
                    p = float(tech_incentives[region]['%'])
                    p_cap = float(tech_incentives[region]['%_max'])
        
                    # rebates, for some reason called 'u' in REopt
                    u = float(tech_incentives[region]['rebate'])
                    u_cap = float(tech_incentives[region]['rebate_max'])
        
                    # check discounts
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
                        u_xbp = 0
                        u_ybp = 0
                        p_xbp = 0
                        p_ybp = 0
        
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
                                        insert_u_bp(xp_array_incent, yp_array_incent, region, u_xbp, u_ybp, p, u_cap)
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
                                        insert_u_bp(xp_array_incent, yp_array_incent, region, u_xbp, u_ybp, p, u_cap)
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
                                            insert_u_after_p_bp(xp_array_incent, yp_array_incent, region, u_xbp, u_ybp, p, p_cap, u_cap)
                                    switch_rebate = True
                                else:
                                    if u * xp != u_cap:
                                        xp_array_incent, yp_array_incent = \
                                            insert_u_bp(xp_array_incent, yp_array_incent, region, u_xbp, u_ybp, p, u_cap)
                                    switch_rebate = True
                                    if p * yp != p_cap:
                                        xp_array_incent, yp_array_incent = \
                                            insert_p_after_u_bp(xp_array_incent, yp_array_incent, region, p_xbp, p_ybp, u, u_cap, p_cap)
                                    switch_percentage = True
                            elif switch_rebate and not switch_percentage:
                                if p * yp != p_cap:
                                    xp_array_incent, yp_array_incent = \
                                        insert_p_after_u_bp(xp_array_incent, yp_array_incent, region, p_xbp, p_ybp, u, u_cap, p_cap)
                                switch_percentage = True
                            elif switch_percentage and not switch_rebate:
                                if u * xp != u_cap:
                                    xp_array_incent, yp_array_incent = \
                                        insert_u_after_p_bp(xp_array_incent, yp_array_incent, region, u_xbp, u_ybp, p, p_cap, u_cap)
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
        
                # clean up any duplicates
                for region in regions:
                    for i in range(1, len(xp_array_incent[region])):
                        if xp_array_incent[region][i] == xp_array_incent[region][i - 1]:
                            xp_array_incent[region] = xp_array_incent[region][0:i]
                            yp_array_incent[region] = yp_array_incent[region][0:i]
                            break
        
                # compute cost curve
                cost_curve_bp_x = xp_array_incent['combined']
                cost_curve_bp_y = yp_array_incent['combined']

                tmp_cap_cost_slope = list()
                tmp_cap_cost_yint = list()
                tmp_cap_cost_x = cost_curve_bp_x

                for seg in range(1, len(cost_curve_bp_x)):
                    tmp_slope = round((cost_curve_bp_y[seg] - cost_curve_bp_y[seg - 1]) /
                                      (cost_curve_bp_x[seg] - cost_curve_bp_x[seg - 1]), 0)
                    tmp_y_int = round(cost_curve_bp_y[seg] - tmp_slope * cost_curve_bp_x[seg], 0)
        
                    tmp_cap_cost_slope.append(tmp_slope)
                    tmp_cap_cost_yint.append(tmp_y_int)
        
                cap_cost_segments = len(tmp_cap_cost_slope)
                cap_cost_points = cap_cost_segments + 1
        
                # include MACRS
                updated_cap_cost_slope = list()
                updated_y_intercept = list()
        
                for s in range(cap_cost_segments):
                    
                    initial_unit_cost = 0
                    if cost_curve_bp_x[s + 1] > 0:
                        initial_unit_cost = ((tmp_cap_cost_yint[s] + tmp_cap_cost_slope[s] * cost_curve_bp_x[s + 1]) /
                                             ((1 - eval('self.' + tech + '.incentives.federal.itc')) 
                                              * cost_curve_bp_x[s + 1]))
                    sf = self.site.financials
                    updated_slope = setup_capital_cost_incentive(initial_unit_cost,
                                                                 0,
                                                                 sf.analysis_period,
                                                                 sf.owner_discount_rate_nominal,
                                                                 sf.owner_tax_rate,
                                                                 eval('self.' + tech + '.incentives.federal.itc'),
                                                                 eval('self.' + tech + '.incentives.macrs_schedule'),
                                                                 eval('self.' + tech + '.incentives.macrs_bonus_fraction'),
                                                                 eval('self.' + tech + '.incentives.macrs_itc_reduction'),
                                                                 )
                    updated_cap_cost_slope.append(updated_slope)
        
                for p in range(1, cap_cost_points):
                    cost_curve_bp_y[p] = cost_curve_bp_y[p - 1] + updated_cap_cost_slope[p - 1] * \
                                                                  (cost_curve_bp_x[p] - cost_curve_bp_x[p - 1])
                    updated_y_intercept.append(cost_curve_bp_y[p] - updated_cap_cost_slope[p - 1] * cost_curve_bp_x[p])
        
                tmp_cap_cost_slope = updated_cap_cost_slope
                tmp_cap_cost_yint = updated_y_intercept

                for seg in range(cap_cost_segments):

                    cap_cost_slope.append(tmp_cap_cost_slope[seg])
                    cap_cost_yint.append(tmp_cap_cost_yint[seg])

                for seg in range(cap_cost_segments + 1):

                    cap_cost_x.append(tmp_cap_cost_x[seg])

            elif eval('self.' + tech) is not None and tech == 'util':

                if len(techs) == 1:  # only util (usually BAU case)
                    cap_cost_segments = 1

                for seg in range(cap_cost_segments or 1):
                    cap_cost_slope.append(0)
                    cap_cost_yint.append(0)

                for seg in range(cap_cost_segments + 1):
                    x = 0
                    if len(cap_cost_x) > 0 and cap_cost_x[-1] == 0:
                        x = big_number
                    cap_cost_x.append(x)

        return cap_cost_slope, cap_cost_x, cap_cost_yint, cap_cost_segments

    def _get_REopt_techToNMILMapping(self, techs):
        TechToNMILMapping = list()

        for tech in techs:

            if eval('self.' + tech) is not None:

                tech_regime = eval('self.' + tech + '.nmil_regime')

                for regime in self.NMILRegime:
                    if regime == tech_regime:
                        TechToNMILMapping.append(1)
                    else:
                        TechToNMILMapping.append(0)
        return TechToNMILMapping

    def _get_REopt_array_tech_load(self, techs):
        """
        Many arrays are built from Tech and Load. As many as possible are defined here to reduce for-loop iterations
        :param techs: list of strings, eg. ['pv', 'pvnm', 'util']
        :return: prod_factor, tech_to_load, tech_is_grid, derate, etaStorIn, etaStorOut
        """
        prod_factor = list()
        tech_to_load = list()
        tech_is_grid = list()
        derate = list()
        eta_storage_in = list()
        eta_storage_out = list()
        om_dollars_per_kw = list()

        for tech in techs:

            if eval('self.' + tech) is not None:

                tech_is_grid.append(int(eval('self.' + tech + '.is_grid')))
                derate.append(eval('self.' + tech + '.derate'))
                om_dollars_per_kw.append(eval('self.' + tech + '.om_dollars_per_kw'))

                for load in self.available_loads:
                    
                    eta_storage_in.append(self.storage.roundtrip_efficiency if load == 'storage' else 1)
                    eta_storage_out.append(self.storage.roundtrip_efficiency if load == 'storage' else 1)
                    # only eta_storage_in is used in REopt currently

                    if eval('self.' + tech + '.can_serve(' + '"' + load + '"' + ')'):

                        for pf in eval('self.' + tech + '.prod_factor'):
                            prod_factor.append(pf)

                        tech_to_load.append(1)

                    else:

                        for _ in range(self.n_timesteps):
                            prod_factor.append(0)

                        tech_to_load.append(0)

                    # By default, util can serve storage load.
                    # However, if storage is being modeled it can override grid-charging
                    if tech == 'util' and load == 'storage' and self.storage is not None:
                        tech_to_load[-1] = int(self.storage.can_grid_charge)

        # In BAU case, storage.dat must be filled out for REopt initializations, but max size is set to zero

        return prod_factor, tech_to_load, tech_is_grid, derate, eta_storage_in, eta_storage_out, om_dollars_per_kw

    def _get_REopt_techs(self, techs):
        reopt_techs = list()
        for tech in techs:

            if eval('self.' + tech) is not None:

                reopt_techs.append(tech.upper() if tech is not 'util' else tech.upper() + '1')

        return reopt_techs

    def _get_REopt_tech_classes(self, techs):
        """
        
        :param techs: list of strings, eg. ['pv', 'pvnm', 'util']
        :return: tech_classes, tech_class_min_size, tech_to_tech_class
        """
        tech_classes = list()
        tech_class_min_size = list()
        tech_to_tech_class = list()
        for tech in techs:

            if eval('self.' + tech) is not None:

                for tc in self.available_tech_classes:

                    if tech.upper() == tc:
                        tech_classes.append(tc)
                        tech_class_min_size.append(eval('self.' + tech + '.min_kw'))

                    if eval('self.' + tech + '.reopt_class').upper() == tc.upper():
                        tech_to_tech_class.append(1)
                    else:
                        tech_to_tech_class.append(0)

        return tech_classes, tech_class_min_size, tech_to_tech_class

    def _get_REopt_tech_max_sizes(self, techs):
        max_sizes = list()
        for tech in techs:

            if eval('self.' + tech) is not None:

                site_kw_max = eval('self.' + tech + '.max_kw')
                
                if eval('self.' + tech + '.acres_per_kw') is not None:

                    if self.site.roof_squarefeet is not None and self.site.land_acres is not None:
                        # don't restrict unless they specify both land_area and roof_area,
                        # otherwise one of them is "unlimited" in UI
                        acres_available = self.site.roof_squarefeet * squarefeet_to_acre \
                                          + self.site.land_acres
                        site_kw_max = acres_available / eval('self.' + tech + '.acres_per_kw')

                max_sizes.append(min(eval('self.' + tech + '.max_kw'), site_kw_max))

        return max_sizes

    def finalize(self):
        """
        necessary for writing out parameters that depend on which Techs are defined
        eg. in REopt ProdFactor: array (Tech,Load,TimeStep).
        Note: whether or not a given Tech can serve a given Load can also be controlled via TechToLoadMatrix
        :return: None
        """

        reopt_techs = self._get_REopt_techs(self.available_techs)
        reopt_techs_bau = self._get_REopt_techs(self.bau_techs)

        load_list = ['1R', '1W', '1X', '1S']  # same for BAU

        reopt_tech_classes, tech_class_min_size, tech_to_tech_class = self._get_REopt_tech_classes(self.available_techs)
        reopt_tech_classes_bau, tech_class_min_size_bau, tech_to_tech_class_bau = self._get_REopt_tech_classes(self.bau_techs)
        reopt_tech_classes_bau = ['PV', 'UTIL']  # not sure why bau needs PV tech class?

        prod_factor, tech_to_load, tech_is_grid, derate, eta_storage_in, eta_storage_out, om_dollars_per_kw = \
            self._get_REopt_array_tech_load(self.available_techs)
        prod_factor_bau, tech_to_load_bau, tech_is_grid_bau, derate_bau, eta_storage_in_bau, eta_storage_out_bau, \
            om_dollars_per_kw_bau = \
            self._get_REopt_array_tech_load(self.bau_techs)
        
        max_sizes = self._get_REopt_tech_max_sizes(self.available_techs)
        max_sizes_bau = self._get_REopt_tech_max_sizes(self.bau_techs)

        levelization_factor, production_incentive_levelization_factor, pwf_e, pwf_om, two_party_factor \
            = self._get_REopt_pwfs(self.available_techs)
        levelization_factor_bau, production_incentive_levelization_factor_bau, pwf_e_bau, pwf_om_bau, two_party_factor_bau \
            = self._get_REopt_pwfs(self.bau_techs)
        
        pwf_prod_incent, prod_incent_rate, max_prod_incent, max_size_for_prod_incent \
            = self._get_REopt_production_incentives(self.available_techs)
        pwf_prod_incent_bau, prod_incent_rate_bau, max_prod_incent_bau, max_size_for_prod_incent_bau \
            = self._get_REopt_production_incentives(self.bau_techs)
        
        cap_cost_slope, cap_cost_x, cap_cost_yint, cap_cost_segments = self._get_REopt_cost_curve(self.available_techs)
        DatFileManager.command_line_args.append("CapCostSegCount=" + str(cap_cost_segments))
        cap_cost_slope_bau, cap_cost_x_bau, cap_cost_yint_bau, cap_cost_segments_bau = self._get_REopt_cost_curve(self.bau_techs)
        DatFileManager.command_line_args_bau.append("CapCostSegCount=" + str(cap_cost_segments_bau))

        sf = self.site.financials
        StorageCostPerKW = setup_capital_cost_incentive(self.storage.us_dollar_per_kw,
                                                        self.storage.replace_us_dollar_per_kw,
                                                        self.storage.replace_kw_years,
                                                        sf.owner_discount_rate_nominal,
                                                        sf.owner_tax_rate,
                                                        self.storage.incentives.federal.itc,
                                                        self.storage.incentives.macrs_schedule,
                                                        self.storage.incentives.macrs_bonus_fraction,
                                                        self.storage.incentives.macrs_itc_reduction,
                                                        )
        StorageCostPerKWH = setup_capital_cost_incentive(self.storage.us_dollar_per_kwh,
                                                         self.storage.replace_us_dollar_per_kwh,
                                                         self.storage.replace_kwh_years,
                                                         sf.owner_discount_rate_nominal,
                                                         sf.owner_tax_rate,
                                                         self.storage.incentives.federal.itc,
                                                         self.storage.incentives.macrs_schedule,
                                                         self.storage.incentives.macrs_bonus_fraction,
                                                         self.storage.incentives.macrs_itc_reduction,
                                                         )

        # DAT1 = constant.dat, contains parameters that others depend on for initialization
        write_to_dat(self.file_constant, reopt_techs, 'Tech')
        write_to_dat(self.file_constant, tech_is_grid, 'TechIsGrid', mode='a')
        write_to_dat(self.file_constant, load_list, 'Load', mode='a')
        write_to_dat(self.file_constant, tech_to_load, 'TechToLoadMatrix', mode='a')
        write_to_dat(self.file_constant, reopt_tech_classes, 'TechClass', mode='a')
        write_to_dat(self.file_constant, self.NMILRegime, 'NMILRegime', mode='a')
        write_to_dat(self.file_constant, derate, 'TurbineDerate', mode='a')
        write_to_dat(self.file_constant, tech_to_tech_class, 'TechToTechClassMatrix', mode='a')

        write_to_dat(self.file_constant_bau, reopt_techs_bau, 'Tech')
        write_to_dat(self.file_constant_bau, tech_is_grid_bau, 'TechIsGrid', mode='a')
        write_to_dat(self.file_constant_bau, load_list, 'Load', mode='a')
        write_to_dat(self.file_constant_bau, tech_to_load_bau, 'TechToLoadMatrix', mode='a')
        write_to_dat(self.file_constant_bau, reopt_tech_classes_bau, 'TechClass', mode='a')
        write_to_dat(self.file_constant_bau, self.NMILRegime, 'NMILRegime', mode='a')
        write_to_dat(self.file_constant_bau, derate_bau, 'TurbineDerate', mode='a')
        write_to_dat(self.file_constant_bau, tech_to_tech_class_bau, 'TechToTechClassMatrix', mode='a')

        # ProdFactor stored in GIS.dat
        write_to_dat(self.file_gis, prod_factor, "ProdFactor")
        write_to_dat(self.file_gis_bau, prod_factor_bau, "ProdFactor")

        # storage.dat
        write_to_dat(self.file_storage, eta_storage_in, 'EtaStorIn', mode='a')
        write_to_dat(self.file_storage, eta_storage_out, 'EtaStorOut', mode='a')
        write_to_dat(self.file_storage_bau, eta_storage_in_bau, 'EtaStorIn', mode='a')
        write_to_dat(self.file_storage_bau, eta_storage_out_bau, 'EtaStorOut', mode='a')

        # maxsizes.dat
        write_to_dat(self.file_max_size, max_sizes, 'MaxSize')
        write_to_dat(self.file_max_size, self.storage.min_kw, 'MinStorageSizeKW', mode='a')
        write_to_dat(self.file_max_size, self.storage.max_kw, 'MaxStorageSizeKW', mode='a')
        write_to_dat(self.file_max_size, self.storage.min_kwh, 'MinStorageSizeKWH', mode='a')
        write_to_dat(self.file_max_size, self.storage.max_kwh, 'MaxStorageSizeKWH', mode='a')
        write_to_dat(self.file_max_size, tech_class_min_size, 'TechClassMinSize', mode='a')

        write_to_dat(self.file_max_size_bau, max_sizes_bau, 'MaxSize')
        write_to_dat(self.file_max_size_bau, 0, 'MinStorageSizeKW', mode='a')
        write_to_dat(self.file_max_size_bau, 0, 'MaxStorageSizeKW', mode='a')
        write_to_dat(self.file_max_size_bau, 0, 'MinStorageSizeKWH', mode='a')
        write_to_dat(self.file_max_size_bau, 0, 'MaxStorageSizeKWH', mode='a')
        write_to_dat(self.file_max_size_bau, tech_class_min_size_bau, 'TechClassMinSize', mode='a')
        
        # economics.dat
        write_to_dat(self.file_economics, levelization_factor, 'LevelizationFactor')
        write_to_dat(self.file_economics, production_incentive_levelization_factor, 'LevelizationFactorProdIncent', mode='a')
        write_to_dat(self.file_economics, pwf_e, 'pwf_e', mode='a')
        write_to_dat(self.file_economics, pwf_om, 'pwf_om', mode='a')
        write_to_dat(self.file_economics, two_party_factor, 'two_party_factor', mode='a')
        write_to_dat(self.file_economics, pwf_prod_incent, 'pwf_prod_incent', mode='a')
        write_to_dat(self.file_economics, prod_incent_rate, 'ProdIncentRate', mode='a')
        write_to_dat(self.file_economics, max_prod_incent, 'MaxProdIncent', mode='a')
        write_to_dat(self.file_economics, max_size_for_prod_incent, 'MaxSizeForProdIncent', mode='a')
        write_to_dat(self.file_economics, cap_cost_slope, 'CapCostSlope', mode='a')
        write_to_dat(self.file_economics, cap_cost_x, 'CapCostX', mode='a')
        write_to_dat(self.file_economics, cap_cost_yint, 'CapCostYInt', mode='a')
        write_to_dat(self.file_economics, sf.owner_tax_rate, 'r_tax_owner', mode='a')
        write_to_dat(self.file_economics, sf.offtaker_tax_rate, 'r_tax_offtaker', mode='a')
        write_to_dat(self.file_economics, StorageCostPerKW, 'StorageCostPerKW', mode='a')
        write_to_dat(self.file_economics, StorageCostPerKWH, 'StorageCostPerKWH', mode='a')
        write_to_dat(self.file_economics, om_dollars_per_kw, 'OMperUnitSize', mode='a')
        write_to_dat(self.file_economics, sf.analysis_period, 'analysis_period', mode='a')

        write_to_dat(self.file_economics_bau, levelization_factor_bau, 'LevelizationFactor')
        write_to_dat(self.file_economics_bau, production_incentive_levelization_factor_bau, 'LevelizationFactorProdIncent', mode='a')
        write_to_dat(self.file_economics_bau, pwf_e_bau, 'pwf_e', mode='a')
        write_to_dat(self.file_economics_bau, pwf_om_bau, 'pwf_om', mode='a')
        write_to_dat(self.file_economics_bau, two_party_factor_bau, 'two_party_factor', mode='a')
        write_to_dat(self.file_economics_bau, pwf_prod_incent_bau, 'pwf_prod_incent', mode='a')
        write_to_dat(self.file_economics_bau, prod_incent_rate_bau, 'ProdIncentRate', mode='a')
        write_to_dat(self.file_economics_bau, max_prod_incent_bau, 'MaxProdIncent', mode='a')
        write_to_dat(self.file_economics_bau, max_size_for_prod_incent_bau, 'MaxSizeForProdIncent', mode='a')
        write_to_dat(self.file_economics_bau, cap_cost_slope_bau, 'CapCostSlope', mode='a')
        write_to_dat(self.file_economics_bau, cap_cost_x_bau, 'CapCostX', mode='a')
        write_to_dat(self.file_economics_bau, cap_cost_yint_bau, 'CapCostYInt', mode='a')
        write_to_dat(self.file_economics_bau, sf.owner_tax_rate, 'r_tax_owner', mode='a')
        write_to_dat(self.file_economics_bau, sf.offtaker_tax_rate, 'r_tax_offtaker', mode='a')
        write_to_dat(self.file_economics_bau, StorageCostPerKW, 'StorageCostPerKW', mode='a')
        write_to_dat(self.file_economics_bau, StorageCostPerKWH, 'StorageCostPerKWH', mode='a')
        write_to_dat(self.file_economics_bau, om_dollars_per_kw_bau, 'OMperUnitSize', mode='a')
        write_to_dat(self.file_economics_bau, sf.analysis_period, 'analysis_period', mode='a')

        # elec_tariff args
        parser = UrdbParse(paths=self.paths, big_number=big_number, elec_tariff=self.elec_tariff,
                           techs=[tech for tech in self.available_techs if eval('self.' + tech) is not None],
                           bau_techs=[tech for tech in self.bau_techs if eval('self.' + tech) is not None],
                           loads=self.available_loads)

        tariff_args = parser.parse_rate(self.elec_tariff.utility_name, self.elec_tariff.rate_name)

        DatFileManager.command_line_args.append('NumRatchets=' + str(tariff_args.demand_num_ratchets))
        DatFileManager.command_line_args.append('FuelBinCount=' + str(tariff_args.energy_tiers_num))
        DatFileManager.command_line_args.append('DemandBinCount=' + str(tariff_args.demand_tiers_num))

        DatFileManager.command_line_args_bau.append('NumRatchets=' + str(tariff_args.demand_num_ratchets))
        DatFileManager.command_line_args_bau.append('FuelBinCount=' + str(tariff_args.energy_tiers_num))
        DatFileManager.command_line_args_bau.append('DemandBinCount=' + str(tariff_args.demand_tiers_num))

        ta = tariff_args
        write_to_dat(self.file_demand_rates_monthly, ta.demand_rates_monthly, 'DemandRatesMonth')
        write_to_dat(self.file_demand_rates, ta.demand_rates_tou, 'DemandRates')
        # write_to_dat(self.file_demand_rates, ta.demand_min, 'MinDemand', 'a')  # not used in REopt
        write_to_dat(self.file_demand_periods, ta.demand_ratchets_tou, 'TimeStepRatchets')
        write_to_dat(self.file_demand_num_ratchets, ta.demand_num_ratchets, 'NumRatchets')
        write_to_dat(self.file_max_in_tiers, ta.demand_max_in_tiers, 'MaxDemandInTier')
        write_to_dat(self.file_max_in_tiers, ta.energy_max_in_tiers, 'MaxUsageInTier', 'a')
        write_to_dat(self.file_energy_rates, ta.energy_rates, 'FuelRate')
        # write_to_dat(self.file_energy_rates, ta.energy_avail, 'FuelAvail', 'a')  # not used in REopt
        write_to_dat(self.file_energy_rates_bau, ta.energy_rates_bau, 'FuelRate')
        # write_to_dat(self.file_energy_rates_bau, ta.energy_avail_bau, 'FuelAvail', 'a')  # not used in REopt
        write_to_dat(self.file_export_rates, ta.export_rates, 'ExportRates')
        write_to_dat(self.file_export_rates_bau, ta.export_rates_bau, 'ExportRates')
        write_to_dat(self.file_demand_lookback, ta.demand_lookback_months, 'DemandLookbackMonths')
        write_to_dat(self.file_demand_lookback, ta.demand_lookback_percent, 'DemandLookbackPercent', 'a')
        write_to_dat(self.file_demand_ratchets_monthly, ta.demand_ratchets_monthly, 'TimeStepRatchetsMonth')
        write_to_dat(self.file_energy_tiers_num, ta.energy_tiers_num, 'FuelBinCount')
        write_to_dat(self.file_energy_tiers_num, ta.demand_tiers_num, 'DemandBinCount', 'a')
        write_to_dat(self.file_energy_burn_rate, ta.energy_burn_rate, 'FuelBurnRateM')
        write_to_dat(self.file_energy_burn_rate_bau, ta.energy_burn_rate_bau, 'FuelBurnRateM')
