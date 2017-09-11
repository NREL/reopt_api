from reo.src.dat_file_manager import DatFileManager, big_number
from reo.src.pvwatts import PVWatts
from reo.src.incentives import Incentives


class Tech(object):
    """
    base class for REopt energy generation technology
    """

    def __init__(self, min_kw=0, max_kw=big_number, cost_dollars_per_kw=0, om_dollars_per_kw=0, degradation_rate=1,
                 *args, **kwargs):

        self.min_kw = min_kw
        self.max_kw = max_kw
        self.cost_dollars_per_kw = cost_dollars_per_kw
        self.om_dollars_per_kw = om_dollars_per_kw
        self.degradation_rate = degradation_rate

        self.loads_served = ['retail', 'wholesale', 'export', 'storage']
        self.nmil_regime = None
        self.reopt_class = ""
        self.is_grid = False
        self.derate = 1
        self.acres_per_kw = None  # for land constraints
        self.kw_per_square_foot = None  # for roof constraints

        # self._check_inputs()
        self.kwargs = kwargs

    def _check_inputs(self):

        assert self.max_kw >= self.min_kw,\
                "max_kw must be greater than or equal to min_kw."

    @property
    def prod_factor(self):
        """
        Production Factor.  Combination of resource, efficiency, and availability.
        :return: prod_factor
        """
        return None

    def can_serve(self, load):
        if load in self.loads_served:
            return True
        return False


class Util(Tech):

    def __init__(self, outage_start=None, outage_end=None, **kwargs):
        super(Util, self).__init__(max_kw=12000000, **kwargs)

        self.outage_start = outage_start
        self.outage_end = outage_end
        self.loads_served = ['retail', 'storage']
        self.is_grid = True
        self.derate = 0

        DatFileManager().add_util(self)

    @property
    def prod_factor(self):

        grid_prod_factor = [1.0 for _ in range(8760)]

        if self.outage_start and self.outage_end:  # "turn off" grid resource
            grid_prod_factor[self.outage_start:self.outage_end] = [0]*(self.outage_end - self.outage_start)
        return grid_prod_factor


class PV(Tech):

    def __init__(self, acres_per_kw=6e-3, kw_per_square_foot=0.01, **kwargs):
        super(PV, self).__init__(min_kw=kwargs.get('pv_kw_min'),
                                 max_kw=kwargs.get('pv_kw_max'),
                                 om_dollars_per_kw=kwargs.get('pv_om'),
                                 cost_dollars_per_kw=kwargs.get('pv_cost'),
                                 degradation_rate=kwargs.get('pv_degradation_rate'),
                                 **kwargs)
        self.nmil_regime = 'BelowNM'
        self.reopt_class = 'PV'
        self.acres_per_kw = acres_per_kw
        self.kw_per_square_foot = kw_per_square_foot
        self.degradation_rate = kwargs.get('pv_degradation_rate')
        self.incentives = Incentives(kwargs, tech='pv', macrs_years=kwargs.get('pv_macrs_schedule'),
                                     macrs_bonus_fraction=kwargs.get('pv_macrs_bonus_fraction'),
                                     macrs_itc_reduction=kwargs.get('pv_macrs_itc_reduction', 0.5),
                                     include_production_based=True
)
        self.pvwatts = None
        DatFileManager().add_pv(self)

    @property
    def prod_factor(self):
        if self.pvwatts is None:
            self.pvwatts = PVWatts(**self.kwargs)
        return self.pvwatts.pv_prod_factor
