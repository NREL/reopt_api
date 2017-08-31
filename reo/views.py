from api_definitions import inputs, outputs
from django.shortcuts import render
import json
from django.http import HttpResponse
from validators import REoptResourceValidation
from django.http import JsonResponse
from src.load_profile import BuiltInProfile
from models import URDBError


def index(request):
    api_inputs = {}
    reference = inputs(full_list=True)
    for k, v in reference.items():
        api_inputs[k] = {'req':bool(reference[k].get('req'))}
        api_inputs[k]['type'] = reference[k].get('type').__name__
        api_inputs[k]['description'] = reference[k].get('description')

        units = reference[k].get('units')
        if units:
            api_inputs[k]['description'] = "%s (%s)" % (api_inputs[k]['description'], units)

        api_inputs[k]['validations'] = "min: %s \n max: %s \n restrict to: %s" % (reference[k].get('min'),
                                                                                  reference[k].get('max'),
                                                                                  reference[k].get('restrict_to'))

    api_outputs = outputs()
    return render(request, 'template.html', {'api_inputs': api_inputs, 'api_outputs': api_outputs})


def check_inputs(request):

    checker = REoptResourceValidation()
    errors = {"Errors": {}}

    bdy = unicode(request.body, 'latin-1')
    parsed_request = json.loads(bdy)
    
    scrubbed_request = {}
    for k,v in parsed_request.items():
        if k in inputs(full_list=True).keys():
            scrubbed_request[k] = v
        else:
            errors["Errors"][k] = ["Not  Valid Input Name"]
    
    errors = checker.check_individual(scrubbed_request, errors)

    if errors == {}:
        return HttpResponse(json.dumps({"Errors": {}}), content_type='application/json')
    else:
        return HttpResponse(json.dumps(errors), content_type='application/json')


def invalid_urdb(request):

    try:
        invalid_set = list(set([i.label for i in URDBError.objects.filter(type='Error')]))
        response = JsonResponse( {"Invalid IDs": invalid_set} )
        
    except Exception as e:
        response = JsonResponse(
            {'Error': str(e)},
        )
    return response

def annual_kwh(request):

    try:
        kwargs = {k:v for k,v in request.GET.dict().items() if k in ['latitude', 'longitude', 'load_profile_name']}

        b = BuiltInProfile(**kwargs)
        
        response = JsonResponse(
            {'annual_kwh': b.annual_kwh},
        )
    except Exception as e:
        response = JsonResponse(
            {'Error': str(e)},
        )
    return response
