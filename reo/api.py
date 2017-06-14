from tastypie import fields
from tastypie.authorization import Authorization
from tastypie.resources import Resource
from tastypie.bundle import Bundle
from tastypie.serializers import Serializer
from tastypie.exceptions import ImmediateHttpResponse
from tastypie.http import HttpApplicationError
from tastypie.resources import ModelResource
from models import RunInput, RunOutput
from IPython import embed
from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS

import logging
from log_levels import log

import library
import random
import os
from api_definitions import *
from validators import  *

def get_current_api():
    return "version 0.0.1"

def setup_logging():
    file_logfile = os.path.join(os.getcwd(), "log", "reopt_api.log")
    logging.basicConfig(filename=file_logfile,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        datefmt='%m/%d/%Y %I:%M%S %p',
                        level=logging.INFO)
    log("INFO", "Logging setup")

class RunInputResource(ModelResource):

    class Meta:
        setup_logging()
        queryset = RunInput.objects.all()
        resource_name = 'reopt'
        allowed_methods = ['get', 'post']
        object_class = RunInput
        authorization = Authorization()
        serializer = Serializer(formats=['json'])
        always_return_data = True
        validation = REoptResourceValidation()

    def detail_uri_kwargs(self, bundle_or_obj):
        kwargs = {}

        if isinstance(bundle_or_obj, Bundle):
            kwargs['pk'] = bundle_or_obj.obj.id
        else:
            kwargs['pk'] = bundle_or_obj['id']

        return kwargs

    def get_object_list(self, request):
        return [request]

    def obj_get_list(self, bundle, **kwargs):
        return self.get_object_list(bundle.request)

    def obj_create(self, bundle, **kwargs):

        #Validate Inputs
        self.is_valid(bundle)
        if bundle.errors:
            raise ImmediateHttpResponse(response=self.error_response(bundle.request, bundle.errors))

        # Format  and  Save Inputs
        model_inputs = dict({k: bundle.data.get(k) for k in inputs(full_list=True).keys() if k in bundle.data.keys() and bundle.data.get(k) is not None })
        model_inputs['api_version'] = get_current_api()       
        run = RunInput(**model_inputs)
        run.save()

        # Return  Results
        output_obj = run.create_output(model_inputs.keys(), bundle.data)
         
        if hasattr(output_obj, 'keys'):
            if "ERROR" in [i.upper() for i in output_obj.keys()]:
                raise ImmediateHttpResponse(response=self.error_response(bundle.request, output_obj))
        
        bundle.obj = output_obj
        bundle.data = output_obj.to_dictionary()
        
        return self.full_hydrate(bundle)

class ReslienceInputResource(ModelResource):
    class Meta:
        queryset = RunOutput.objects.all()
        resource_name = 'resilience_input'
        allowed_methods = ['get']
        fields = ['run_input_id']
        filtering = {'run_input_id':ALL}

    def dehydrate(self, bundle):
        print "A"
        field_maps = {'run_input_id':None,'pv_kw':'pv_kw','batt_kw':'batt_kw','batt_kwh':'batt_kwh','load_8760_kw':'load','crit_load_factor':'crit_load_factor','batt_efficiency':'batt_roundtrip_efficiency','batt_soc_init':'init_soc','prod_factor':'prod_factor'}

        for k,v in field_maps.items():
            if v is not None:
                bundle.data[v] = getattr(bundle.obj, k)

        return bundle
