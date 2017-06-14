#!/user/bin/python
# ==============================================================================
#  Description: download pvwatts solar resource for given lat/lon
#       and produce 'ProdFactor' for Mosel (includes utility ProdFactor)
# ==============================================================================
import requests
import json
import os, csv
import keys
from api_definitions import *
from log_levels import log


class PVWatts:

    # Input data
    latitude = None
    longitude = None
    run_id = None
    levelization_factor = None

    # Assume defaults
    #dataset = "tmy3"  # Default: tmy2 Options: tmy2 , tmy3, intl
    #inv_eff = 96?
    #dc_ac_ratio = 1.1
    #azimuth = 180
    #system_capacity = 1  # kw to get prod factor
    #array_type = 0  # fixed open rack
   # module_type = 0  # standard
  #  timeframe = "hourly"
  #  losses = 14
  #  radius = 0

    # Time
    steps_per_hour = 1

    # Output
    output_root = []
    prod_factor = []
    prod_factor_bau = []

    filename_GIS = []
    filename_GIS_bau = []

    def __init__(self, output_root, run_id, pvwatts_inputs, levelization_factor, steps_per_hour=1,
                 outage_start=None, outage_end=None):
        """

        :param output_root:
        :param run_id:
        :param pvwatts_inputs:
        :param levelization_factor:
        :param steps_per_hour:
        :param outage_start: int, min: 0, max: 8759, zero-based index for the hour that grid outage starts
        :param outage_end:  int, min: 0, max: 8759, zero-based index for the hour that grid outage ends
        """
        self.steps_per_hour = steps_per_hour
        self.output_root = output_root
        self.run_id = run_id
        self.levelization_factor = levelization_factor
        self.outage_start = outage_start
        self.outage_end = outage_end

        for k,v in pvwatts_inputs.items():
            setattr(self,k,v)

        self.download_locations()
        return self

    def api(self):
        # API specific
        return {'key' : keys.pvwatts_api_key,
        'base' : "https://developer.nrel.gov/api/pvwatts/v5.json"}

    def make_url(self):
        return self.api()['base'] + "?api_key=" + self.api()['key'] + "&azimuth=" + str(self.azimuth) + "&system_capacity=" + str(self.system_capacity) + \
                   "&losses=" + str(self.losses*100) + "&array_type=" + str(self.array_type) + "&module_type=" + str(self.module_type) + \
                   "&timeframe=" + self.timeframe +"&gcr=" + str(self.gcr) +  "&dc_ac_ratio=" + str(self.dc_ac_ratio) + "&inv_eff=" + str(self.inv_eff*100) + \
                   "&radius=" + str(self.radius) + "&dataset=" + self.dataset + "&lat=" + str(self.latitude) + "&lon=" + str(self.longitude) + "&tilt=" + str(self.tilt)

    def download_locations(self):
        url = self.make_url()
        r = requests.get(url, verify=True)
        data = json.loads(r.text)
        self.compute_prod_factor(data)
        self.write_output()

    def compute_prod_factor(self, data):
        # NEED TO DERATE 0.5%! nlaws: accounted for in LevelizationFactor, which is defined in economics.py
        outputs = data['outputs']

        ac_hourly = outputs.get('ac')

        if ac_hourly is None:
            ac_hourly = [0] * 8760

        dc_nameplate = self.system_capacity * 1000  # W
        prod_factor = []
        prod_factor_bau = []
        prod_factor_ts = []

        # subhourly (i.e 15 minute data)
        if self.steps_per_hour >= 1:
            timesteps = []
            timesteps_base = range(0, 8760)
            for ts_b in timesteps_base:
                for step in range(0, self.steps_per_hour):
                   timesteps.append(ts_b)

        # downscaled run (i.e 288 steps per year)
        else:
            timesteps = range(0, 8760, int(1 / self.steps_per_hour))

        for hour in timesteps:
            # degradation (levelization factor) applied in mosel model
            prod_factor_ts.append(round(ac_hourly[hour]/ dc_nameplate, 4))

        # build dictionary with same structure as ProdFactor in Mosel
        tech_bau = ['UTIL1']
        tech = ['PV', 'PVNM', 'UTIL1']
        load = ["1R", "1W", "1X", "1S"]
        pf_Dict = {}
        pf_Dict_bau = {}

        for t in tech:
            pf_Dict[t] = {ld: None for ld in load}

            if t is 'UTIL1':

                grid_prod_factor = [1.0 for _ in range(8760)]

                if self.outage_start and self.outage_end:  # "turn off" grid resource
                    grid_prod_factor[self.outage_start:self.outage_end] = [0]*(self.outage_end - self.outage_start)

                pf_Dict[t]['1R'] = pf_Dict[t]['1S'] = grid_prod_factor
                    # grid produces 100% of capacity, so '1's for Retail and Storage
                pf_Dict[t]['1W'] = pf_Dict[t]['1X'] = [0.0 for _ in range(
                    8760)]  # grid cannot sell back, so '0's for Wholesale and Export

            elif t is 'PV':
                pf_Dict[t]['1R'] = pf_Dict[t]['1S'] = \
                    pf_Dict[t]['1W'] = pf_Dict[t]['1X'] = [p for p in prod_factor_ts]  # PV can serve all loads
            elif t is 'PVNM':
                pf_Dict[t]['1R'] = pf_Dict[t]['1S'] = \
                    pf_Dict[t]['1W'] = pf_Dict[t]['1X'] = [p for p in prod_factor_ts]  # PV can serve all loads

        for t in tech_bau:
            pf_Dict_bau[t] = {ld: None for ld in load}
            if t is 'UTIL1':
                pf_Dict_bau[t]['1R'] = pf_Dict_bau[t]['1S'] = [1.0 for _ in range(8760)]
                pf_Dict_bau[t]['1W'] = pf_Dict_bau[t]['1X'] = [0.0 for _ in range(8760)]

        for t in tech:
            for ld in load:
                for pf in pf_Dict[t][ld]:
                    prod_factor.append(str(pf))
        for t in tech_bau:
            for ld in load:
                for pf in pf_Dict_bau[t][ld]:
                    prod_factor_bau.append(str(pf))

        self.prod_factor = prod_factor
        self.prod_factor_bau = prod_factor_bau

    def write_output(self):
        self.filename_GIS = "GIS_" + str(self.run_id) + ".dat"
        self.filename_GIS_bau = "GIS_" + str(self.run_id) + "_bau.dat"

        output = os.path.join(self.output_root, self.filename_GIS)
        output_bau = os.path.join(self.output_root, self.filename_GIS_bau)

        f = open(output, 'w')
        f_bau = open(output_bau, 'w')
        f.write("ProdFactor: [\n")
        f_bau.write("ProdFactor: [\n")
        for prod_factor in self.prod_factor:
            f.write(prod_factor + "\t,\n")
        for prod_factor in self.prod_factor_bau:
            f_bau.write(prod_factor + "\t,\n")
        f.write("]")
        f_bau.write("]")
        f.close()
        f_bau.close()
