import logging
import os
import json
import uuid
from tastypie.authorization import ReadOnlyAuthorization
from tastypie.bundle import Bundle
from tastypie.serializers import Serializer
from tastypie.exceptions import ImmediateHttpResponse, HttpResponse
from tastypie.resources import ModelResource
from validators import REoptResourceValidation, ValidateNestedInput
from log_levels import log
from utilities import API_Error
from scenario import Scenario
from reo.models import ModelManager, BadPost
from api_definitions import inputs as flat_inputs
from reo.src.paths import Paths

api_version = "version 1.0.0"
saveToDb = True


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
        # queryset = ScenarioModel.objects.all()
        resource_name = 'reopt'
        allowed_methods = ['post']
        detail_allowed_methods = []
        # object_class = ScenarioModel
        authorization = ReadOnlyAuthorization()
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
        
        if 'Scenario' not in bundle.data.keys():
            self.is_valid(bundle)  # runs REoptResourceValidation
            output_format = 'flat'

            if bundle.errors:
                raise ImmediateHttpResponse(response=self.error_response(bundle.request, bundle.errors))

            input_validator = ValidateNestedInput(bundle.data, nested=False)

        else:  # nested input
            output_format = 'nested'
            input_validator = ValidateNestedInput(bundle.data, nested=True)

        run_uuid = uuid.uuid4()
        scenario = {'run_uuid': str(run_uuid), 'api_version': api_version}

        data = dict()
        data["inputs"] = input_validator.input_dict
        data["messages"] = input_validator.messages
        data["outputs"] = {"Scenario": scenario}
        """
        for webtool need to update data with input_validator.input_for_response (flat inputs), as well as flat outputs
        """

        if not input_validator.isValid:  # 400 Bad Request

            data["outputs"]["Scenario"]["status"] = "Invald inputs. See messages."

            if saveToDb:
                bad_post = BadPost(run_uuid=run_uuid, post=bundle.data, errors=data['messages']['errors']).create()

            raise ImmediateHttpResponse(HttpResponse(json.dumps(data),
                                                     content_type='application/json',
                                                     status=400))

        model_manager = ModelManager()

        # Return  Results
        output_model = self.create_output(input_validator, output_format, model_manager, data)

        raise ImmediateHttpResponse(HttpResponse(json.dumps(output_model), content_type='application/json', status=201))

    def create_output(self, input_validator, output_format, model_manager, data):

        run_uuid = uuid.uuid4()
        paths = Paths(run_uuid=run_uuid)
        meta = {'run_uuid': str(run_uuid), 'api_version': api_version}
      
        output_dictionary = dict()
        output_dictionary["inputs"] = input_validator.input_for_response
        output_dictionary['outputs'] = {"Scenario": meta}
        output_dictionary["messages"] = input_validator.messages
        scenario_inputs = input_validator.input_dict['Scenario']
        model_solved = False

        try:

            s = Scenario(run_uuid=run_uuid, inputs_dict=scenario_inputs, paths=vars(paths))

            # Log POST request
            s.log_post(input_validator.input_dict)

            # Run Optimization
            optimization_results = s.run()
            model_solved = True

            optimization_results['flat'].update(meta)
            optimization_results['flat']['uuid'] = meta['run_uuid']
            optimization_results['nested']['Scenario'].update(meta)
            output_dictionary['outputs'] = optimization_results[output_format]
            data['outputs'].update(optimization_results['nested'])

        except Exception as e:

            output_dictionary["messages"] = {
                    "errors": API_Error(e).response,
                    "warnings": input_validator.warnings,
                }

        if saveToDb:
            model_manager.create_and_save(data)

        if not scenario_inputs['Site']['Wind']['max_kw'] > 0:
            output_dictionary = self.remove_wind(output_dictionary, output_format, model_solved)

        if output_format == 'flat':
            # fill in outputs with inputs
            for arg, defs in flat_inputs(full_list=True).iteritems():
                output_dictionary['outputs'][arg] = output_dictionary["inputs"].get(arg) or defs.get("default")
            # backwards compatibility for webtool, copy all "outputs" to top level of response dict
            output_dictionary.update(output_dictionary['outputs'])

        return output_dictionary

    @staticmethod
    def remove_wind(output_dictionary, output_format, model_solved):
        if output_format == 'nested':
            del output_dictionary['inputs']['Scenario']['Site']["Wind"]
            if model_solved:
                del output_dictionary['outputs']['Scenario']['Site']["Wind"]
        
        if output_format == 'flat':
            for key in ['wind_cost', 'wind_om', 'wind_kw_max', 'wind_kw_min', 'wind_itc_federal', 'wind_ibi_state',
                        'wind_ibi_utility', 'wind_itc_federal_max', 'wind_ibi_state_max', 'wind_ibi_utility_max',
                        'wind_rebate_federal', 'wind_rebate_state', 'wind_rebate_utility', 'wind_rebate_federal_max',
                        'wind_rebate_state_max', 'wind_rebate_utility_max', 'wind_pbi', 'wind_pbi_max',
                        'wind_pbi_years', 'wind_pbi_system_max', 'wind_macrs_schedule', 'wind_macrs_bonus_fraction']:
                if key in output_dictionary['inputs'].keys():
                    del output_dictionary['inputs'][key]
                if model_solved:
                    if key in output_dictionary['outputs'].keys():
                        del output_dictionary['outputs'][key]

        return output_dictionary
