from tastypie import fields
from tastypie.authorization import Authorization
from tastypie.resources import Resource
from tastypie.bundle import Bundle

import library
import random


# We need a generic object to shove data in and to get data from.
class REoptObject(object):
    def __init__(self, id=None, analysis_period=None, latitude=None, longitude=None, load_size=None, pv_om=None, batt_cost_kw=None, batt_cost_kwh=None,
                 load_profile=None, pv_cost=None, owner_discount_rate=None, offtaker_discount_rate=None, lcc=None, utility_kwh=None, pv_kw=None, batt_kw=None, batt_kwh=None):
        self.id = id

        self.analysis_period = analysis_period
        self.latitude = latitude
        self.longitude = longitude
        self.load_size = load_size
        self.pv_om = pv_om
        self.batt_cost_kw = batt_cost_kw
        self.batt_cost_kwh = batt_cost_kwh
        self.load_profile = load_profile
        self.pv_cost = pv_cost
        self.owner_discount_rate = owner_discount_rate
        self.offtaker_discount_rate = offtaker_discount_rate

        #outputs
        self.lcc = lcc
        self.utility_kwh = utility_kwh
        self.pv_kw = pv_kw
        self.batt_kw = batt_kw
        self.batt_kwh = batt_kwh


class REoptRunResource(Resource):
    # Just like a Django ``Form`` or ``Model``, we're defining all the
    # fields we're going to handle with the API here.

    # inputs
    analysis_period = fields.IntegerField(attribute='analysis_period', null=True)
    latitude = fields.FloatField(attribute='latitude', null=True)
    longitude = fields.FloatField(attribute='longitude', null=True)
    load_size = fields.FloatField(attribute='load_size')
    pv_om = fields.FloatField(attribute='pv_om', null=True)
    batt_cost_kw = fields.FloatField(attribute='batt_cost_kw', null=True)
    batt_cost_kwh = fields.FloatField(attribute='batt_cost_kwh', null=True)
    load_profile = fields.CharField(attribute='load_profile', null=True)
    pv_cost = fields.FloatField(attribute='pv_cost', null=True)
    owner_discount_rate = fields.FloatField(attribute='owner_discount_rate', null=True)
    offtaker_discount_rate = fields.FloatField(attribute='offtaker_discount_rate', null=True)

    # internally generated
    id = fields.IntegerField(attribute='id')

    #outputs
    lcc = fields.FloatField(attribute="lcc", null=True)
    utility_kwh = fields.FloatField(attribute="utility_kwh", null=True)
    pv_kw = fields.FloatField(attribute="pv_kw", null=True)
    batt_kw = fields.FloatField(attribute="batt_kw", null=True)
    batt_kwh = fields.FloatField(attribute="batt_kwh", null=True)

    class Meta:
        resource_name = 'reopt'
        allowed_methods = ['get']
        object_class = REoptObject
        authorization = Authorization()


    def detail_uri_kwargs(self, bundle_or_obj):
        kwargs = {}

        if isinstance(bundle_or_obj, Bundle):
            kwargs['pk'] = bundle_or_obj.obj.id
        else:
            kwargs['pk'] = bundle_or_obj['id']

        return kwargs

    def get_object_list(self, request):
        # note, running process is from reopt_api head
        # i.e, C:\Nick\Projects\api\env\src\reopt_api

        # generate a unique id for this run
        run_id = random.randint(0, 1000000)

        analysis_period = request.GET.get("analysis_period")
        latitude = request.GET.get("latitude")
        longitude = request.GET.get("longitude")
        load_size = request.GET.get("load_size")
        pv_om = request.GET.get("pv_om")
        batt_cost_kw = request.GET.get("batt_cost_kw")
        batt_cost_kwh = request.GET.get("batt_cost_kwh")
        load_profile = request.GET.get("load_profile")
        pv_cost = request.GET.get("pv_cost")
        owner_discount_rate = request.GET.get("owner_discount_rate")
        offtaker_discount_rate = request.GET.get("offtaker_discount_rate")

        path_xpress = "Xpress"
        run_set = library.dat_library(run_id, path_xpress, analysis_period, latitude, longitude, load_size, pv_om, batt_cost_kw, batt_cost_kwh, load_profile, pv_cost, owner_discount_rate, offtaker_discount_rate)
        outputs = run_set.run()

        lcc = 0
        utility_kwh = 0
        pv_kw = 0
        batt_kw = 0
        batt_kwh = 0

        if 'lcc' in outputs:
            lcc = outputs['lcc']
        if 'utility_kwh' in outputs:
            utility_kwh = outputs['utility_kwh']
        if 'pv_kw' in outputs:
            pv_kw = outputs['pv_kw']
        if 'batt_kw' in outputs:
            batt_kw = outputs['batt_kw']
        if 'batt_kwh' in outputs:
            batt_kwh = outputs['batt_kwh']

        results = []
        new_obj = REoptObject(run_id, analysis_period, latitude, longitude, load_size, pv_om, batt_cost_kw,
                              batt_cost_kwh, load_profile, pv_cost, owner_discount_rate, offtaker_discount_rate, lcc,
                              utility_kwh, pv_kw, batt_kw, batt_kwh)
        results.append(new_obj)
        return results

    def obj_get_list(self, bundle, **kwargs):
        # filtering disabled for brevity
        return self.get_object_list(bundle.request)

