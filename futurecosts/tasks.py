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
import json
import copy
from celery import shared_task
from reo.api import Job
from reo.views import results
from celery.utils.log import get_task_logger
from futurecosts.models import cost_forecasts, FutureCostsJob
from reo.models import ScenarioModel  # used in exec
from tastypie.exceptions import ImmediateHttpResponse
log = get_task_logger(__name__)


@shared_task(ignore_result=True)
def setup_jobs(run_uuid):
    """
    POST 10 jobs to main API and connect them to the FutureCostsJob model
    :param run_uuid: UUID of scenario from current year with "optimal" status. Used as base for all inputs except
        the future costs of Wind, PV, and Storage
    :return: None
    """

    fcjob = FutureCostsJob.objects.get(run_uuid=run_uuid)

    # 1. Get results for original scenario
    base_results = results(None, run_uuid)
    d = json.loads(base_results.content)
    d = scrub_urls_from_dict(d)

    # 2 Create future inputs and post them
    for i, year in enumerate(range(fcjob.base_year+2, fcjob.base_year+22, 2)):
        new_post = fill_in_future_costs(d["inputs"], year=year)
        # TODO make post_job a task and have it retry_on_failure?
        resp = post_job(new_post)
        exec("fcjob.future_scenario{} = ScenarioModel.objects.get(run_uuid=resp['run_uuid'])".format(i+1))
        exec("fcjob.future_year{} = year".format(i+1))

    fcjob.status = "Optimizing..."
    fcjob.save(force_update=True)


def post_job(data: dict) -> dict:
    job = Job()
    try:
        job.obj_create(bundle=copy.deepcopy(data))
    except ImmediateHttpResponse as resp:
        resp = json.loads(resp.response.content.decode('utf-8'))
        if "run_uuid" in resp.keys():
            return resp
        else:
            log.warning("could not create job:", resp["messages"]["error"])
            return resp["messages"]
    # TODO handle problems from posting jobs
    return {}


def scrub_urls_from_dict(d: dict) -> dict:
    for k, v in d.items():
        if isinstance(v, dict):
            scrub_urls_from_dict(v)
        if isinstance(v, str):
            if "http://" in v or "https://" in v:
                d[k] = "url removed"
    return d


def fill_in_future_costs(d: dict, year: int) -> dict:
    d["Scenario"]["Site"]["Wind"]["installed_cost_us_dollars_per_kw"] = \
        cost_forecasts.wind(
            year,
            type="capital_cost_dollars_per_kw",
            size_class=d["Scenario"]["Site"]["Wind"].get("size_class") or "commercial"
        )
    d["Scenario"]["Site"]["Wind"]["om_cost_us_dollars_per_kw"] = \
        cost_forecasts.wind(
            year,
            type="fixed_om_dollars_per_kw_per_yr",
            size_class=d["Scenario"]["Site"]["Wind"].get("size_class") or "commercial"
        )
    d["Scenario"]["Site"]["PV"]["installed_cost_us_dollars_per_kw"] = \
        cost_forecasts.pv(year, type="capital_cost_dollars_per_kw")

    d["Scenario"]["Site"]["PV"]["om_cost_us_dollars_per_kw"] = \
        cost_forecasts.pv(year, type="fixed_om_dollars_per_kw_per_yr")

    d["Scenario"]["Site"]["Storage"]["installed_cost_us_dollars_per_kw"] = \
        cost_forecasts.storage(year, type="installed_cost_us_dollars_per_kw")

    d["Scenario"]["Site"]["Storage"]["installed_cost_us_dollars_per_kwh"] = \
        cost_forecasts.storage(year, type="installed_cost_us_dollars_per_kwh")
    return d
