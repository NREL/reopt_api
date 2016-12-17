from tastypie import fields
from tastypie.authorization import Authorization
from tastypie.resources import Resource
from tastypie.bundle import Bundle
from tastypie.serializers import Serializer
from tastypie.exceptions import ImmediateHttpResponse
from tastypie.http import HttpApplicationError
from tastypie.resources import ModelResource
from tastypie.resources import csrf_exempt
from models import RunInput

import library
import random
import os
from api_definitions import *
from validators import  *

def get_current_api():
    return "version 0.0.1"

class RunInputResource(ModelResource):
    class Meta:
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

    def wrap_view(self, view):
        @csrf_exempt
        def wrapper(request, *args, **kwargs):
            request.format = kwargs.pop('format', None)
            wrapped_view = super(RunInputResource, self).wrap_view(view)
            return wrapped_view(request, *args, **kwargs)
        return wrapper

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
      
        output_obj = run.create_output(model_inputs.keys())
        bundle.obj = output_obj
        bundle.data = output_obj.to_dictionary()
        
        return self.full_hydrate(bundle)
       

