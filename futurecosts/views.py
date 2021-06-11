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
import uuid
import sys
import traceback as tb
from reo.views import make_error_resp
from django.http import JsonResponse
from reo.exceptions import UnexpectedError
from futurecosts.models import FutureCostsJob


def results(request, run_uuid):
    try:
        uuid.UUID(run_uuid)  # raises ValueError if not valid uuid

    except ValueError as e:
        if e.args[0] == "badly formed hexadecimal UUID string":
            resp = make_error_resp(e.args[0])
            return JsonResponse(resp, status=400)
        else:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            err = UnexpectedError(exc_type, exc_value.args[0], tb.format_tb(exc_traceback), task='futurecosts_results',
                                  run_uuid=run_uuid)
            err.save_to_db()
            return JsonResponse({"Error": str(err.args[0])}, status=400)

    try:
        fcjob = FutureCostsJob.objects.get(run_uuid=run_uuid)
        fcjob.update_status()
        resp_dict = fcjob.dict
        resp_dict["messages"] = [
            "GET the detailed results for each future_scenarioX_id at developer.nrel.gov/stable/job/<id>/results."
        ]
        return JsonResponse(resp_dict)

    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        err = UnexpectedError(exc_type, exc_value.args[0], tb.format_tb(exc_traceback), task='reo.futurecosts.results',
                              run_uuid=run_uuid)
        err.save_to_db()
        resp = make_error_resp(err.message)
        return JsonResponse(resp, status=500)

