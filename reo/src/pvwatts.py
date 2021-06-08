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
import requests
import json
import keys
import logging
from reo.exceptions import PVWattsDownloadError
log = logging.getLogger(__name__)


def check_pvwatts_response_data(resp):
    """
    If we can load the response data then return it,
    else raise an exception
    :param resp: requests.get result
    :return: dict of resp.text
    """
    try:
        data = json.loads(resp.text)
    except:
        message = ("Error parsing PVWatts response. "
                   "Status code: {}. Text: {}".format(resp.status_code, resp.text))
        raise_pvwatts_exception(message)
    else:
        return data


def raise_pvwatts_exception(message):
    """
    Raise PVWattsDownloadError
    :param message: str
    :return: None
    """
    log.error("pvwatts.py raising error: " + message)
    pvwatts_error = PVWattsDownloadError(task="pvwatts.py", message=message)
    raise pvwatts_error


class PVWatts:

    def __init__(self,
                 url_base="https://developer.nrel.gov/api/pvwatts/v6.json",
                 key=keys.developer_nrel_gov_key,
                 azimuth=180,
                 system_capacity=1,
                 losses=0.14,
                 array_type=0,
                 module_type=0,
                 timeframe='hourly',
                 gcr=0.4,
                 dc_ac_ratio=1.1,
                 inv_eff=0.96,
                 radius=100,
                 dataset="nsrdb",
                 latitude=None,
                 longitude=None,
                 tilt=None,
                 time_steps_per_hour=1,
                 offline=False,
                 verify=True,
                 **kwargs):
        """
        WARNING: the __init__ method calls PVWatts API
        :param url_base: str
        :param key: str
        :param azimuth: float
        :param system_capacity: float
        :param losses: float
        :param array_type: int
        :param module_type: int
        :param timeframe: str
        :param gcr: float
        :param dc_ac_ratio: float
        :param inv_eff: float
        :param radius: float
        :param dataset: str
        :param latitude: float
        :param longitude: float
        :param tilt: float
        :param time_steps_per_hour: int
        :param offline: bool
        :param verify: bool
        :param kwargs: dict
        """
        self.url_base = url_base
        self.key = key
        self.azimuth = azimuth
        self.system_capacity = system_capacity
        self.losses = losses
        self.array_type = array_type
        self.module_type = module_type
        self.timeframe = timeframe
        self.gcr = gcr
        self.dc_ac_ratio = dc_ac_ratio
        self.inv_eff = inv_eff
        self.radius = radius
        self.dataset = dataset
        self.latitude = latitude
        self.longitude = longitude
        self.tilt = tilt
        self.time_steps_per_hour = time_steps_per_hour
        self.offline = offline  # used for testing
        self.verify = verify  # used for testing
        self.response = None
        self.response = self.data  # store response so don't hit API multiple times
        if self.tilt is None:
            # if the site is in the southern hemisphere, and no tilt has been specified,
            # then set the tilt to the positive latitude value and change the azimuth to zero
            if self.latitude < 0:
                self.tilt = self.latitude * -1
                self.azimuth = 0
            else:
                # if the site is in the norther hemisphere, and no tilt has been specified,
                # then set the tilt to the latitude value
                self.tilt = self.latitude

    @property
    def url(self):
        url = self.url_base + "?api_key=" + self.key + "&azimuth=" + str(self.azimuth) + \
              "&system_capacity=" + str(self.system_capacity) + "&losses=" + str(self.losses*100) + \
              "&array_type=" + str(self.array_type) + "&module_type=" + str(self.module_type) + \
              "&timeframe=" + self.timeframe + "&gcr=" + str(self.gcr) +  "&dc_ac_ratio=" + str(self.dc_ac_ratio) + \
              "&inv_eff=" + str(self.inv_eff*100) + "&radius=" + str(int(self.radius)) + "&dataset=" + self.dataset + \
              "&lat=" + str(self.latitude) + "&lon=" + str(self.longitude) + "&tilt=" + str(self.tilt)
        return url

    @property
    def data(self):
        if self.response is None:
            # Check if point is beyond the bounds of the NRSDB dataset, if so use the international dataset and double the radius
            if self.latitude < -59.5 or self.latitude > 60.01 or self.longitude > -22.37 or self.longitude < -179.58 :
                self.dataset = 'intl'
                self.radius = self.radius *2
            resp = requests.get(self.url, verify=self.verify)
            log.info("PVWatts API query successful.")
            data = check_pvwatts_response_data(resp)
            self.response = data
        return self.response

    @property
    def pv_prod_factor(self):

        if not self.offline:

            outputs = self.response['outputs']
            ac_hourly = outputs.get('ac')

            if ac_hourly is None:
                ac_hourly = [0] * 8760

            dc_nameplate = self.system_capacity * 1000  # W
            prod_factor = []

            # subhourly (i.e 15 minute data)
            if self.time_steps_per_hour >= 1:
                timesteps = []
                timesteps_base = range(0, 8760)
                for ts_b in timesteps_base:
                    for step in range(0, self.time_steps_per_hour):
                       timesteps.append(ts_b)

            # downscaled run (i.e 288 steps per year)
            else:
                timesteps = range(0, 8760, int(1 / self.time_steps_per_hour))

            for hour in timesteps:
                # degradation (levelization factor) applied in mosel model
                prod_factor.append(round(ac_hourly[hour]/ dc_nameplate, 4))

        else:
            prod_factor_original = list()
            import os
            with open(os.path.join('reo', 'tests', 'offline_pv_prod_factor.txt'), 'r') as f:
                for line in f:
                    prod_factor_original.append(float(line.strip('\n')))

            # offline_pv_prod_factor.txt has 8760 rows, thus modifying prod_factor list
            # to have 8760 * time_steps_per_hour values
            prod_factor = [val for val in prod_factor_original for _ in range(self.time_steps_per_hour)]

        return prod_factor
