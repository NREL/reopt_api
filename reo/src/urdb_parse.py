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
import calendar
import numpy
import logging
log = logging.getLogger(__name__)

cum_days_in_yr = numpy.cumsum(calendar.mdays)


class REoptArgs:

    def __init__(self, big_number):

        # these vars are passed to DFM as REopt params, written to dats
        self.demand_rates_monthly = 12 * [0.0]
        """
        demand_ratchets_monthly == TimeStepRatchetsMonth in mosel
        It is not only used for demand rates, but also for summing the energy use in each month for rates with energy
        tiers.
        """
        self.demand_ratchets_monthly = [[] for i in range(12)]  # initialize empty lists to fill with timesteps
        for month in range(12):
            for hour in range(24 * cum_days_in_yr[month]+1, 24 * cum_days_in_yr[month+1]+1):
                self.demand_ratchets_monthly[month].append(hour)
        self.demand_rates_tou = []
        self.demand_ratchets_tou = []
        self.demand_num_ratchets = 0
        self.demand_tiers_num = 1
        self.demand_month_tiers_num = 1
        self.demand_max_in_tiers = 1 * [big_number]
        self.demand_month_max_in_tiers = 1 * [big_number]
        self.demand_lookback_months = []
        self.demand_lookback_percent = 0.0
        self.demand_lookback_range = 0
        self.demand_min = 0

        self.energy_tiers_num = 1
        self.energy_max_in_tiers = 1 * [big_number]

        self.energy_costs = []
        self.energy_costs_bau = []
        self.grid_export_rates = []
        self.grid_export_rates_bau = []

        self.fixed_monthly_charge = 0
        self.annual_min_charge = 0
        self.min_monthly_charge = 0

        self.chp_standby_rate_us_dollars_per_kw_per_month = 0
        self.chp_does_not_reduce_demand_charges = 0


class RateData:

    def __init__(self, rate):

        possible_URDB_keys = (
            'utility',
            'rate',
            'sector',
            'label',
            'uri',
            'startdate',
            'enddate',
            'description',
            'usenetmetering',
            'source',
            # demand charges
            'peakkwcapacitymin',
            'peakkwcapacitymax',
            'peakkwcapacityhistory',
            'flatdemandunit',
            'flatdemandstructure',
            'flatdemandmonths',
            'demandrateunit',
            'demandratestructure',
            'demandunits',
            'demandweekdayschedule',
            'demandweekendschedule',
            'demandwindow',
            'demandreactivepowercharge',
            # lookback demand charges
            'lookbackMonths',
            'lookbackPercent',
            'lookbackRange',
            # coincident rates
            'coincidentrateunit',
            'coincidentratestructure',
            'coincidentrateschedule',
            # energy charges
            'peakkwhusagemin',
            'peakkwhusagemax',
            'peakkwhusagehistory',
            'energyratestructure',
            'energyweekdayschedule',
            'energyweekendschedule',
            'energycomments',
            # other charges
            'fixedchargefirstmeter',
            'fixedchargeunits',
            'mincharge',
            'minchargeunits',
            'fixedmonthlycharge',
            'minmonthlycharge',
            'annualmincharge',
        )

        for k in possible_URDB_keys:
            if k in rate:
                setattr(self, k, rate.get(k))
            else:
                setattr(self, k, list())

        if self.demandunits == 'hp': #convert hp to KW, assume PF is 1 so no need to convert kVA to kW, as of 01/28/2020 only 3 rates in URDB with hp units
            for period in self.demandratestructure:
                for tier in period:
                    if tier.get('rate') or False != False:
                        tier['rate'] = float(tier['rate']) * 0.7457
                    if tier.get('adj') or False != False:
                        tier['adj'] = float(tier['adj']) * 0.7457

        if self.demandunits == 'hp': #convert hp to KW, assume PF is 1 so no need to convert kVA to kW, as of 01/28/2020 only 3 rates in URDB with hp units
            for period in self.demandratestructure:
                for tier in period:
                    if tier.get('rate') or False != False:
                        tier['rate'] = float(tier['rate']) * 0.7457
                    if tier.get('adj') or False != False:
                        tier['adj'] = float(tier['adj']) * 0.7457


class UrdbParse:
    """
    Sub-function of DataManager.
    """
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    def __init__(self, big_number, elec_tariff, techs, bau_techs):

        self.urdb_rate = elec_tariff.urdb_response
        self.year = elec_tariff.load_year
        self.time_steps_per_hour = elec_tariff.time_steps_per_hour
        self.ts_per_year = 8760 * self.time_steps_per_hour
        self.zero_array = [0.0] * self.ts_per_year
        self.wholesale_rate = elec_tariff.wholesale_rate
        self.excess_rate = elec_tariff.wholesale_rate_above_site_load
        self.max_demand_rate = 0.0
        self.big_number = big_number
        self.reopt_args = REoptArgs(big_number)
        self.techs = techs
        self.bau_techs = bau_techs
        self.chp_standby_rate_us_dollars_per_kw_per_month = elec_tariff.chp_standby_rate_us_dollars_per_kw_per_month
        self.chp_does_not_reduce_demand_charges = elec_tariff.chp_does_not_reduce_demand_charges
        self.custom_tou_energy_rates = elec_tariff.tou_energy_rates
        self.add_tou_energy_rates_to_urdb_rate = elec_tariff.add_tou_energy_rates_to_urdb_rate
        self.override_urdb_rate_with_tou_energy_rates = elec_tariff.override_urdb_rate_with_tou_energy_rates

        self.energy_rates_summary = []
        self.demand_rates_summary = []
        self.energy_costs = []
        self.has_fixed_demand = "no"
        self.has_tou_demand = "no"
        self.has_demand_tiers = "no"
        self.has_tou_energy = "no"
        self.has_energy_tiers = "no"

        # Count the leap day
        self.is_leap_year = False
        if calendar.isleap(self.year):
            self.is_leap_year = True

        self.last_hour_in_month = []
        for month in range(0, 12):
            days_elapsed = sum(self.days_in_month[0:month + 1])
            self.last_hour_in_month.append((days_elapsed * 24))  # last_hour_in_month is one indexed (for Julia)

    def parse_rate(self, utility, rate):
        log.info("Processing: " + utility + ", " + rate)

        current_rate = RateData(self.urdb_rate)

        if self.override_urdb_rate_with_tou_energy_rates:
            self.has_tou_energy = "yes"  # all that we need from prepare_summary
            self.demand_rates_summary = self.ts_per_year * [0]  # all that we need from prepare_demand_periods
            self.energy_costs = self.custom_tou_energy_rates  # all that we need from prepare_energy_costs
            # assume no fixed charges
        else:
            self.prepare_summary(current_rate)
            self.prepare_demand_periods(current_rate)  # makes demand rates too
            self.prepare_energy_costs(current_rate)
            self.prepare_fixed_charges(current_rate)

        self.reopt_args.energy_costs, \
        self.reopt_args.grid_export_rates, \
        self.reopt_args.chp_standby_rate_us_dollars_per_kw_per_month, \
        self.reopt_args.chp_does_not_reduce_demand_charges, \
        = self.prepare_techs_and_loads(self.techs)

        self.reopt_args.energy_costs_bau, \
        self.reopt_args.grid_export_rates_bau, \
        self.reopt_args.chp_standby_rate_us_dollars_per_kw_per_month_bau, \
        self.reopt_args.chp_does_not_reduce_demand_charges_bau, \
        = self.prepare_techs_and_loads(self.bau_techs)

        return self.reopt_args

    def prepare_summary(self, current_rate):

        if len(current_rate.energyratestructure) > 0:
            if len(current_rate.energyratestructure[0]) > 1:
                self.has_energy_tiers = "yes"
            # tou energy only if greater than one period
            if len(current_rate.energyratestructure) > 1:
                self.has_tou_energy = "yes"

        if len(current_rate.demandratestructure) > 0:
            if len(current_rate.demandratestructure[0]) > 1:
                self.has_demand_tiers = "yes"
            if len(current_rate.energyratestructure) > 1:
                self.has_tou_demand = "yes"

        if len(current_rate.flatdemandstructure) > 0:
            self.has_fixed_demand = "yes"
            if len(current_rate.flatdemandstructure[0]) > 1:
                self.has_demand_tiers = "yes"

        max_demand_rate = 0.0
        for period in current_rate.demandratestructure:
            for tier in period:
                if 'rate' in tier:
                    rate = float(tier['rate'])
                    if 'adj' in tier:
                        rate += float(tier['adj'])
                    if rate > max_demand_rate:
                        max_demand_rate = rate
        for period in range(0, len(current_rate.flatdemandstructure)):
            for tier in range(0, len(current_rate.flatdemandstructure[period])):
                if 'rate' in current_rate.flatdemandstructure[period][tier]:
                    rate = float(current_rate.flatdemandstructure[period][tier]['rate'])
                    if 'adj' in current_rate.flatdemandstructure[period][tier]:
                        rate += float(current_rate.flatdemandstructure[period][tier]['adj'])
                    if rate > max_demand_rate:
                        max_demand_rate = rate

        self.max_demand_rate = max_demand_rate

    def prepare_energy_costs(self, current_rate):

        n_periods = len(current_rate.energyratestructure)
        if n_periods == 0:
            return

        # parse energy tiers
        energy_tiers = []
        for energy_rate in current_rate.energyratestructure:
            energy_tiers.append(len(energy_rate))

        period_with_max_tiers = energy_tiers.index(max(energy_tiers))
        energy_tier_set = set(energy_tiers)

        if len(energy_tier_set) > 1:
            log.warning("Warning: energy periods contain different numbers of tiers, using limits of period with most tiers")

        self.reopt_args.energy_tiers_num = max(energy_tier_set)

        average_rates = False
        rates = []
        rate_average = 0

        # set energy rate tier(bin) limits
        self.reopt_args.energy_max_in_tiers = []

        for energy_tier in current_rate.energyratestructure[period_with_max_tiers]:
            # energy_tier is a dictionary, eg. {'max': 1000, 'rate': 0.07531, 'adj': 0.0119, 'unit': 'kWh'}
            energy_tier_max = self.big_number

            if 'max' in energy_tier:
                if energy_tier['max'] is not None:
                    energy_tier_max = float(energy_tier['max'])

            if 'rate' in energy_tier or 'adj' in energy_tier:
                self.reopt_args.energy_max_in_tiers.append(energy_tier_max)

            # deal with complex units (can't model exactly, must make average)
            if 'unit' in energy_tier:
                energy_tier_unit = str(energy_tier['unit'])
                # average the prices if we have exotic max usage units
                if energy_tier_unit != 'kWh':
                    average_rates = True

            if 'rate' in energy_tier:
                rates.append(float(energy_tier['rate']))
                if 'adj' in energy_tier:
                    rates[-1] += float(energy_tier['adj'])
            # people put adj but no rate in some rates
            elif 'adj' in energy_tier:
                rates.append(float(energy_tier['adj']))

        if average_rates:
            rate_average = float(sum(rates)) / max(len(rates), 1)
            self.reopt_args.energy_tiers_num = 1
            self.reopt_args.energy_max_in_tiers = []
            self.reopt_args.energy_max_in_tiers.append(self.big_number)
            log.warning("Cannot handle max usage units of " + energy_tier_unit + "! Using average rate")

        for tier in range(0, self.reopt_args.energy_tiers_num):
            hour_of_year = 0
            for month in range(0, 12):
                for day in range(0, self.days_in_month[month]):

                    if calendar.weekday(self.year, month + 1, day + 1) < 5:
                        is_weekday = True
                    else:
                        is_weekday = False

                    energy_ts_per_hour = int(len(current_rate.energyweekdayschedule[0])/24)
                    simulation_time_steps_per_rate_time_step = int(self.time_steps_per_hour / energy_ts_per_hour)
                    for hour in range(0, 24):
                        energy_ts = hour * energy_ts_per_hour
                        for ts in range(energy_ts_per_hour):
                            if is_weekday:
                                period = int(current_rate.energyweekdayschedule[month][energy_ts])
                            else:
                                period = int(current_rate.energyweekendschedule[month][energy_ts])

                            # workaround for cases where there are different numbers of tiers in periods
                            n_tiers_in_period = len(current_rate.energyratestructure[period])

                            if n_tiers_in_period == 1:
                                tier_use = 0  # use the first and only tier in the period
                            elif tier > n_tiers_in_period-1:  # 'tier' is indexed on zero
                                tier_use = n_tiers_in_period-1  # use last tier in current period, which has less tiers than the maximum tiers for any period
                            else:
                                tier_use = tier

                            if average_rates:
                                rate = rate_average
                            else:
                                rate = float(current_rate.energyratestructure[period][tier_use].get('rate') or 0)

                            adj = float(current_rate.energyratestructure[period][tier_use].get('adj') or 0)
                            total_rate = rate + adj

                            for step in range(0, simulation_time_steps_per_rate_time_step):
                                if self.add_tou_energy_rates_to_urdb_rate:
                                    idx = hour_of_year  # len(self.custom_tou_energy_rates) == 8760:
                                    if len(self.custom_tou_energy_rates) == 35040:
                                        idx = hour_of_year * 4 + step
                                    total_rate = rate + adj + self.custom_tou_energy_rates[idx]
                                self.energy_costs.append(total_rate)
                            energy_ts += 1
                        hour_of_year += 1

    def prepare_techs_and_loads(self, techs):

        energy_costs = [round(cost, 5) for cost in self.energy_costs]
        # len(self.energy_costs) = self.ts_per_year * self.reopt_args.energy_tiers_num

        start_index = len(energy_costs) - self.ts_per_year
        self.energy_rates_summary = energy_costs[start_index:len(energy_costs)]  # MOVE ELSEWHERE

        """
        ExportRate should be lowest energy cost for tiered rates. Otherwise, ExportRate can be > FuelRate, which
        leads REopt to export all PV energy produced.
        """
        tier_with_lowest_energy_cost = 0
        if self.reopt_args.energy_tiers_num > 1:
            annual_energy_charge_sums = []
            for i in range(0, len(energy_costs), self.ts_per_year):
                annual_energy_charge_sums.append(
                    sum(energy_costs[i:i+self.ts_per_year])
                )
            tier_with_lowest_energy_cost = annual_energy_charge_sums.index(min(annual_energy_charge_sums))

        negative_energy_costs = [cost * -0.999 for cost in
                                 energy_costs[tier_with_lowest_energy_cost*self.ts_per_year:(tier_with_lowest_energy_cost+1)*self.ts_per_year]]

        # wholesale and excess rates can be either scalar (floats or ints) or lists of floats
        if len(self.wholesale_rate) == 1:
            negative_wholesale_rate_costs = self.ts_per_year * [-1.0 * self.wholesale_rate[0]]
        else:
            negative_wholesale_rate_costs = [-1.0 * x for x in self.wholesale_rate]
        if len(self.excess_rate) == 1:
            negative_excess_rate_costs = self.ts_per_year * [-1.0 * self.excess_rate[0]]
        else:
            negative_excess_rate_costs = [-1.0 * x for x in self.excess_rate]

        grid_export_rates = list()
        if len(techs) > 0:  # TODO eliminate hard-coded 3 "sales tiers" (really export tiers)
            grid_export_rates.append(negative_energy_costs)
            grid_export_rates.append(negative_wholesale_rate_costs)
            grid_export_rates.append(negative_excess_rate_costs)

        # CHP-specific parameters
        chp_standby_rate = self.chp_standby_rate_us_dollars_per_kw_per_month
        chp_does_not_reduce_demand_charges = self.chp_does_not_reduce_demand_charges

        return energy_costs, grid_export_rates, chp_standby_rate, chp_does_not_reduce_demand_charges

    def prepare_demand_periods(self, current_rate):

        n_flat = len(current_rate.flatdemandstructure)
        n_tou = len(current_rate.demandratestructure)
        n_rates = n_flat + n_tou

        self.demand_rates_summary = self.ts_per_year * [0]

        if n_rates == 0:
            return
        if n_flat > 0:
            self.prepare_demand_tiers(current_rate, n_flat, True)
            self.prepare_flat_demand(current_rate)
        if n_tou > 0:
            self.prepare_demand_tiers(current_rate, n_tou, False)
            self.prepare_tou_demand(current_rate)

        self.prepare_demand_lookback(current_rate)
        self.prepare_demand_rate_summary()

    def prepare_demand_lookback(self, current_rate):
        """
        URDB lookback fields:
            lookbackMonths
            Type: array
            Array of 12 booleans, true or false, indicating months in which lookbackPercent applies.
                If any of these is true, lookbackRange should be zero.

            lookbackPercent
            Type: decimal
            Lookback percentage. Applies to either lookbackMonths with value=1, or a lookbackRange.

            lookbackRange
            Type: integer
            Number of months for which lookbackPercent applies. If not 0, lookbackMonths values should all be 0.
        """
        if current_rate.lookbackPercent in [None, 0, []]:
            reopt_lookback_months = []
            lookback_percentage = 0
            lookback_range = 0
        else:
            lookback_percentage = current_rate.lookbackPercent or 0.0
            lookback_months = current_rate.lookbackMonths  # defaults to empty list
            lookback_range = current_rate.lookbackRange or 0
            reopt_lookback_months = []
            if lookback_range != 0 and len(lookback_months) == 12:
                for month in range(1, 13):
                    if lookback_months[month] == 1:
                        reopt_lookback_months.append(month)

        self.reopt_args.demand_lookback_months = reopt_lookback_months
        self.reopt_args.demand_lookback_percent = float(lookback_percentage)
        self.reopt_args.demand_lookback_range = lookback_range

    def prepare_demand_tiers(self, current_rate, n_periods, monthly):

        # use same method for monthly and tou tiers, just different names
        if monthly:
            demand_rate_structure = current_rate.flatdemandstructure
            self.reopt_args.demand_month_max_in_tiers = []
        else:
            demand_rate_structure = current_rate.demandratestructure
            self.reopt_args.demand_max_in_tiers = []

        demand_tiers = []
        for demand_rate in demand_rate_structure:
            demand_tiers.append(len(demand_rate))
        demand_tier_set = set(demand_tiers)
        period_with_max_tiers = demand_tiers.index(max(demand_tiers)) #NOTE: this takes the first period if multiple periods have the same number of (max) tiers
        n_tiers = max(demand_tier_set)

        if len(demand_tier_set) > 1:
            log.warning("Warning: multiple lengths of demand tiers, using tiers from the earliest period with the max number of tiers")

            # make the number of tiers the same across all periods by appending on identical tiers
            for r in range(n_periods):
                demand_rate = demand_rate_structure[r]
                demand_rate_new = demand_rate
                n_tiers_in_period = len(demand_rate)
                if n_tiers_in_period != n_tiers:
                    last_tier = demand_rate[n_tiers_in_period - 1]
                    for i in range(0, n_tiers - n_tiers_in_period):
                        demand_rate_new.append(last_tier)
                demand_rate_structure[r] = demand_rate_new

        demand_tiers = {} # for all periods
        demand_maxes = []

        if n_periods > 0:
            for period in range(n_periods):
                demand_max = []
                for tier in range(n_tiers):
                    demand_tier = demand_rate_structure[period][tier]
                    demand_tier_max = self.big_number
                    if 'max' in demand_tier:
                        if demand_tier['max'] is not None:
                            demand_tier_max = float(demand_tier['max'])
                    demand_max.append(demand_tier_max)
                demand_tiers[period] = demand_max
                demand_maxes.append(demand_max[-1])

        # test if the highest tier is the same across all periods
        test_demand_max = set(demand_maxes)
        if len(test_demand_max) > 1:
           log.warning("Warning: highest demand tiers do not match across periods, using max from largest set of tiers")

        if monthly:
            self.reopt_args.demand_month_max_in_tiers = demand_tiers[period_with_max_tiers]
            self.reopt_args.demand_month_tiers_num = n_tiers
        else:
            self.reopt_args.demand_max_in_tiers = demand_tiers[period_with_max_tiers]
            self.reopt_args.demand_tiers_num = n_tiers

    def prepare_flat_demand(self, current_rate):

        self.reopt_args.demand_rates_monthly = []

        for month in range(12):

            for period_idx, seasonal_period in enumerate(current_rate.flatdemandstructure):
                period_in_month = 0
                if len(current_rate.flatdemandmonths) > 0:
                    period_in_month = current_rate.flatdemandmonths[month]

                    if period_in_month == period_idx:

                        for tier in seasonal_period:
                            seasonal_rate = float(tier.get('rate') or 0)
                            seasonal_adj = float(tier.get('adj') or 0)
                            self.reopt_args.demand_rates_monthly.append(seasonal_rate + seasonal_adj)

    def prepare_demand_rate_summary(self):
        """
        adds flat demand rate for each timestep to self.demand_rates_summary
        (which is full of zeros before this step)
        :return:
        """

        for month in range(12):
            flat_rate = self.reopt_args.demand_rates_monthly[month]
            month_hours = self.get_hours_in_month(month)

            for hour in month_hours:
                self.demand_rates_summary[hour] += flat_rate

    def prepare_tou_demand(self, current_rate):
        demand_periods = []
        demand_rates = []

        if type(current_rate.peakkwcapacitymin) is int:
            self.reopt_args.demand_min = current_rate.peakkwcapacitymin

        self.reopt_args.demand_rates = []
        for month in range(12):

            for demand_period in range(len(current_rate.demandratestructure)):

                time_steps = self.get_tou_steps(current_rate, month, demand_period)

                if len(time_steps) > 0:

                    demand_periods.append(time_steps)

                    for tier in current_rate.demandratestructure[demand_period]:

                        tou_rate = float(tier.get('rate') or 0)
                        tou_adj = float(tier.get('adj') or 0)

                        demand_rates.append(tou_rate + tou_adj)

                        for step in time_steps:
                            self.demand_rates_summary[step-1] += tou_rate + tou_adj

        self.reopt_args.demand_ratchets_tou = demand_periods
        self.reopt_args.demand_rates_tou = demand_rates
        self.reopt_args.demand_num_ratchets = len(demand_periods)

    def prepare_fixed_charges(self, current_rate):
        if not isinstance(current_rate.fixedchargefirstmeter, list):      #URDB v7
            if current_rate.fixedchargeunits == '$/month': # first try $/month, then check if $/day exists, as of 1/28/2020 there were only $/day and $month entries in the URDB
                self.reopt_args.fixed_monthly_charge = current_rate.fixedchargefirstmeter
            if current_rate.fixedchargeunits == '$/day':
                self.reopt_args.fixed_monthly_charge = current_rate.fixedchargefirstmeter*30.4375 # scalar intended to approximate annual charges over 12 month period, derived from 365.25/12
        else:                                                           #URDB v3, preserve backwards compatability
            if not isinstance(current_rate.fixedmonthlycharge, list):
                self.reopt_args.fixed_monthly_charge = current_rate.fixedmonthlycharge

        if current_rate.mincharge  != []:                               #URDB v7
            if current_rate.minchargeunits == '$/month':
                self.reopt_args.min_monthly_charge = current_rate.mincharge # first try $/month, then check if $/day or $/year exists, as of 1/28/2020 these were the only unit types in the urdb
            if current_rate.minchargeunits == '$/day':
                self.reopt_args.fixed_monthly_charge = current_rate.mincharge*30.4375 # scalar intended to approximate annual charges over 12 month period, derived from 365.25/12
            if current_rate.minchargeunits == '$/year':
                self.reopt_args.annual_min_charge = current_rate.mincharge
        else:                                                           #URDB v3, preserve backwards compatability
            if not isinstance(current_rate.annualmincharge, list):
                self.reopt_args.annual_min_charge = current_rate.annualmincharge
            if not isinstance(current_rate.minmonthlycharge, list):
                self.reopt_args.min_monthly_charge = current_rate.minmonthlycharge

    def get_hours_in_month(self, month):
        hours = []
        hours.append(0)
        for m in range(12):
            hours_previous = hours[m]
            days_in_month = calendar.monthrange(self.year, m + 1)[1]
            # no leap days allowed
            if m == 1 and calendar.isleap(self.year):
                days_in_month -= 1
            hours.append(24 * days_in_month + hours_previous)

        return range(hours[month], hours[month + 1])

    def get_tou_steps(self, current_rate, month, period):
        """
        Get the TOU steps indexed on 1-8760 for hourly simulations
        :param current_rate: RateData class instance
        :param month: int
        :param period: int
        :return: list of ints
        """
        step_array = []
        start_step = 1

        demand_ts_per_hour = int(len(current_rate.demandweekdayschedule[0] or 0)/24)
        simulation_time_steps_per_rate_time_step = int(self.time_steps_per_hour / demand_ts_per_hour)

        if month > 0:
            start_step = (self.last_hour_in_month[month - 1] + 1) * self.time_steps_per_hour

        step_of_year = start_step

        for day in range(0, self.days_in_month[month]):
            if calendar.weekday(self.year, month + 1, day + 1) < 5:
                is_weekday = True
            else:
                is_weekday = False

            for hour in range(0, 24):
                demand_ts = hour * demand_ts_per_hour
                for ts in range(demand_ts_per_hour):
                    for step in range(0, simulation_time_steps_per_rate_time_step):
                        if is_weekday and current_rate.demandweekdayschedule[month][demand_ts] == period:
                            step_array.append(step_of_year)
                        elif not is_weekday and current_rate.demandweekendschedule[month][demand_ts] == period:
                            step_array.append(step_of_year)
                        step_of_year += 1
                    demand_ts += 1
        return step_array
