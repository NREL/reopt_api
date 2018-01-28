import json
import os
import sys
import traceback as tb
from models import ProForma, ScenarioModel
from django.http import HttpResponse
from wsgiref.util import FileWrapper
from reo.log_levels import log


def proforma(request):
    uuid = request.GET.get('run_uuid')

    if uuid is None:
        return HttpResponse(json.dumps({"Bad Request": "No run_uuid provided"}),
                            content_type='application/json', status=400)
    try:
        scenario = ScenarioModel.objects.get(run_uuid=uuid)

        try:
            pf = ProForma.objects.get(scenariomodel=scenario)
        except:
            pf = ProForma.create(scenariomodel=scenario)

        pf.generate_spreadsheet()
        pf.save()

        wrapper = FileWrapper(file(pf.output_file))
 
        response = HttpResponse(wrapper, content_type='application/vnd.ms-excel.sheet.macroEnabled.12')
        response['Content-Length'] = os.path.getsize(pf.output_file)
        response['Content-Disposition'] = 'attachment; filename=%s' % (pf.output_file_name)
        return response

    except Exception as e:

        if type(e).__name__ == 'DoesNotExist':
            msg = "Scenario {} does not exist.".format(uuid)
            return HttpResponse(json.dumps({type(e).__name__: msg}),
                                content_type='application/json', status=404)
        else:

            exc_type, exc_value, exc_traceback = sys.exc_info()
            debug_msg = "exc_type: {}; exc_value: {}; exc_traceback: {}".format(exc_type, exc_value,
                                                                                tb.format_tb(exc_traceback))
            log("ERROR", debug_msg)
            return HttpResponse(json.dumps({"Unexpected error": "Unexpected Error. Please contact reopt@nrel.gov."}),
                                content_type='application/json', status=500)
