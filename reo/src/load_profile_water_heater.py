# from reo.src.load_profile import BuiltInProfile
import pandas as pd
import numpy as np
from datetime import datetime


class LoadProfileWaterHeater(object):
    """
    Contains information relevant to construct a hot water draw profile,
    Presently just takes 8760, so not much to do
    """
    
    annual_gal = {}
    
    def __init__(self, dfm, lp, annual_fraction=None, monthly_fraction=None, loads_fraction=None, latitude=None, longitude=None, time_steps_per_hour=None, doe_reference_name=None, nearest_city=None, year=None, percent_share_list=None, **kwargs):
        self.time_steps_per_hour = time_steps_per_hour
        self.load_list = lp

        # if annual_fraction is not None:
        #     self.load_list = [annual_fraction * gal for gal in lp.unmodified_load_list]
        #
        # elif monthly_fraction is not None:
        #     month_series = pd.date_range(datetime(lp.year,1,1), datetime(lp.year+1,1,1), periods=8760*time_steps_per_hour)
        #     self.load_list = [lp.unmodified_load_list[i] * monthly_fraction[month-1]  for i, month in enumerate(month_series.month)]
        #
        # elif loads_fraction is not None:
        #     self.load_list = list(np.array(loads_fraction) * np.array(lp.unmodified_load_list))

        self.annual_gal = sum(self.load_list)
        dfm.add_load_water_heater(self)
