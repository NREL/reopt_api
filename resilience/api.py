from tastypie import fields
from tastypie.authorization import Authorization
from tastypie.resources import Resource
from tastypie.bundle import Bundle
from tastypie.serializers import Serializer
from tastypie.exceptions import ImmediateHttpResponse
from tastypie.http import HttpApplicationError
from tastypie.resources import ModelResource
from models import ResilienceCase

import random
import os
from api_definitions import *
from validators import ResilienceCaseValidation

def get_current_api():
    return "Resilience v 0.0.1"


class ResilienceCaseResource(ModelResource):

    class Meta:
        queryset = ResilienceCase.objects.all()
        resource_name = 'resilience'
        allowed_methods = ['post']
        object_class = ResilienceCase
        authorization = Authorization()
        serializer = Serializer(formats=['json'])
        always_return_data = True
        validation = ResilienceCaseValidation()

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

        self.is_valid(bundle)
        if bundle.errors:
            raise ImmediateHttpResponse(response=self.error_response(bundle.request, bundle.errors))

        model_inputs = dict({k: bundle.data.get(k) for k in inputs(full_list=True).keys() if k in bundle.data.keys() and bundle.data.get(k) is not None })
        model_inputs['api_version'] = get_current_api()

        bundle.obj, bundle.data = ResilienceCase.run(model_inputs, bundle)

        return self.full_hydrate(bundle)


