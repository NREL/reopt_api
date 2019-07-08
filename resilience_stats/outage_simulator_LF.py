#!usr/bin/python
import copy
from math import floor


def simulate_outage(batt_kwh, batt_kw, pv_kw_ac_hourly, init_soc, critical_loads_kw, wind_kw_ac_hourly=None,
                    batt_roundtrip_efficiency=0.829, diesel_kw=0, fuel_available=0, b=0, m=0, diesel_min_turndown=0.3):
    """
    :param batt_kwh: float, battery storage capacity
    :param batt_kw: float, battery inverter capacity
    :param pv_kw_ac_hourly: list of floats, AC production of PV system
    :param init_soc: list of floats between 0 and 1 inclusive, initial state-of-charge
    :param critical_loads_kw: list of floats
    :param wind_kw_ac_hourly: list of floats, AC production of wind turbine
    :param batt_roundtrip_efficiency: roundtrip battery efficiency
    :param diesel_kw: float, diesel generator capacity
    :param fuel_available: float, gallons of diesel fuel available
    :param b: float, diesel fuel burn rate intercept coefficient (y = m*x + b*rated_capacity)  [gal/kwh/kw]
    :param m: float, diesel fuel burn rate slope (y = m*x + b*rated_capacity)  [gal/kWh]
    :param diesel_min_turndown: minimum generator turndown in fraction of generator capacity (0 to 1)
    :return: list of hours survived for outages starting at every time step, plus min,max,avg of list
    """

    n_timesteps = len(critical_loads_kw)
    n_steps_per_hour = n_timesteps / 8760  # type: int

    r = [0] * n_timesteps

    # NOTE: not making hourly load assumptions: a kW is not equivalent to a kWh!!!

    if batt_kw == 0 or batt_kwh == 0:
        init_soc = [0] * n_timesteps  # default is None

        if pv_kw_ac_hourly in [None, []] and diesel_kw == 0:  # no pv, generator, nor battery --> no resilience

            return {"resilience_by_timestep": r,
                    "resilience_hours_min": 0,
                    "resilience_hours_max": 0,
                    "resilience_hours_avg": 0,
                    "outage_durations": None,
                    "probs_of_surviving": None,
                    }

    if pv_kw_ac_hourly in [None, []]:
        pv_kw_ac_hourly = [0] * n_timesteps
    if wind_kw_ac_hourly in [None, []]:
        wind_kw_ac_hourly = [0] * n_timesteps

    class generator():
        def __init__(self, diesel_kw, fuel_available, b, m, diesel_min_turndown):
            self.kw = diesel_kw
            self.fuel_available = fuel_available if self.kw > 0 else 0
            self.b = b * self.kw
            self.m = m
            self.min_turndown = diesel_min_turndown
            self.genmin = self.min_turndown * self.kw
        
        def genavail(self, n_steps_per_hour):  # kW
            if self.fuel_available - self.b > 0:
                return min((self.fuel_available * n_steps_per_hour - self.b) / self.m, self.kw)
            else:
                return 0

        def fuelConsume(self, gen_output, n_steps_per_hour):  # kW
            if self.genavail(n_steps_per_hour) >= self.genmin and gen_output > 0:
                gen_output = max(self.genmin, min(gen_output, self.genavail(n_steps_per_hour)))
                fuel_consume = (self.b + self.m * gen_output) / n_steps_per_hour 
                self.fuel_available -= min(self.fuel_available, fuel_consume)
            else:
                gen_output = 0
            return gen_output
    
    class battery():
        def __init__(self, batt_kwh, batt_kw, batt_roundtrip_efficiency, soc=0.5):
            self.kw = batt_kw
            self.size = batt_kwh if self.kw > 0 else 0
            self.soc = soc
            self.roundtrip_efficiency = batt_roundtrip_efficiency

        def battavail(self, n_steps_per_hour):  # kW
            return min(self.size * self.soc * n_steps_per_hour, self.kw)

        def battDischarge(self, discharge, n_steps_per_hour):  # kW
            discharge = min(self.battavail(n_steps_per_hour), discharge)
            self.soc -= min(discharge / self.size / n_steps_per_hour, self.soc)
            return discharge

        def battCharge(self, charge, n_steps_per_hour):  # kw
            room = (1 - self.soc)   # if there's room in the battery
            charge = min(room * n_steps_per_hour * self.size / self.roundtrip_efficiency, charge, self.kw / self.roundtrip_efficiency)
            chargesoc = charge * self.roundtrip_efficiency / self.size / n_steps_per_hour
            self.soc += chargesoc
            return charge

    def loadFollowing(critical_load, pv, wind, generator, battery, n_steps_per_hour):
        """
        Dispatch strategy for one time step
        """

        # distributed generation minus load is the burden on battery
        unmatch = (critical_load - pv - wind)  # kw
        discharge = 0
        gen_output = 0
        charge = 0
        
        if unmatch < 0:    # pv + wind> critical_load
            # excess PV power to charge battery
            charge = battery.battCharge(-unmatch, n_steps_per_hour)
            unmatch = 0 

        elif generator.genmin <= generator.genavail(n_steps_per_hour) and 0 < generator.kw:
            gen_output = generator.fuelConsume(unmatch, n_steps_per_hour)
            # charge battery with excess energy if unmatch < genmin
            charge = battery.battCharge(max(gen_output-unmatch, 0), n_steps_per_hour)  # prevent negative charge
            discharge = battery.battDischarge(max(unmatch-gen_output, 0), n_steps_per_hour)  # prevent negative discharge
            unmatch -= (gen_output + discharge - charge)

            # unmatch > genavail & (unmatch - genavail) <= battavail
            if unmatch <= generator.genavail(n_steps_per_hour):   # diesel can meet balance
                unmatch = 0

        elif unmatch <= battery.battavail(n_steps_per_hour):   # battery can carry balance
            discharge = battery.battDischarge(unmatch, n_steps_per_hour)
            unmatch = 0
        
        # else: battery + generator cannot survive outage --> unmatch > 0

        stat = (gen_output, discharge, charge)

        return unmatch, stat, generator, battery

    '''
    Simulation starts here
    '''
    GEN = generator(diesel_kw, fuel_available, b, m, diesel_min_turndown)
    BATT = battery(batt_kwh, batt_kw, batt_roundtrip_efficiency)

    for time_step in range(n_timesteps):
        gen = copy.deepcopy(GEN)
        batt = copy.deepcopy(BATT)
        # outer loop: do simulation starting at each time step
        batt.soc = init_soc[time_step]   # reset battery for each simulation

        for i in range(n_timesteps):    # the i-th time step of simulation
            # inner loop: step through all possible surviving time steps
            # break inner loop if can not survive
            t = (time_step + i) % n_timesteps

            unmatch, stat, gen, batt = loadFollowing(
                        critical_loads_kw[t], pv_kw_ac_hourly[t], wind_kw_ac_hourly[t], gen, batt, n_steps_per_hour)

            if unmatch > 0:  # cannot survive
                r[time_step] = float(i) / float(n_steps_per_hour)
                break

    r_min = min(r)
    r_max = max(r)
    r_avg = round((float(sum(r)) / float(len(r))), 2)

    x_vals = range(1, int(floor(r_max)+1))
    y_vals = list()

    for hrs in x_vals:
        y_vals.append(round(float(sum([1 if h >= hrs else 0 for h in r])) / float(n_timesteps), 4))

    return {"resilience_by_timestep": r,
            "resilience_hours_min": r_min,
            "resilience_hours_max": r_max,
            "resilience_hours_avg": r_avg,
            "outage_durations": x_vals,
            "probs_of_surviving": y_vals,
            }
