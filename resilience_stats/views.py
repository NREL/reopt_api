import uuid
import sys
from django.http import JsonResponse
from reo.models import ScenarioModel, PVModel, StorageModel, LoadProfileModel, GeneratorModel
from models import ResilienceModel
from outage_simulator import simulate_outage
from reo.exceptions import UnexpectedError
from django.forms.models import model_to_dict


def resilience_stats(request, run_uuid):
    """
    Run outage simulator for given run_uuid
    :param request:
    :param run_uuid:
    :return: {"resilience_by_timestep",
              "resilience_hours_min",
              "resilience_hours_max",
              "resilience_hours_avg",
              "outage_durations",
              "probs_of_surviving",
             }
    """

    try:
        uuid.UUID(run_uuid)  # raises ValueError if not valid uuid

    except ValueError as e:
        if e.message == "badly formed hexadecimal UUID string":
            return JsonResponse({"Error": str(e.message)}, status=400)
        else:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            err = UnexpectedError(exc_type, exc_value, exc_traceback, task='resilience_stats', run_uuid=run_uuid)
            err.save_to_db()
            return JsonResponse({"Error": str(err.message)}, status=400)

    try:  # to run outage simulator
        scenario = ScenarioModel.objects.get(run_uuid=run_uuid)

        try:  # see if ResilienceModel already created
            rm = ResilienceModel.objects.get(scenariomodel=scenario)
            results = model_to_dict(rm)
            # remove items that user does not need
            del results['scenariomodel']
            del results['id']

        except:
            rm = ResilienceModel.create(scenariomodel=scenario)

            gen = GeneratorModel.objects.filter(run_uuid=scenario.run_uuid).first()
            batt = StorageModel.objects.filter(run_uuid=scenario.run_uuid).first()
            pv = PVModel.objects.filter(run_uuid=scenario.run_uuid).first()
            load_profile = LoadProfileModel.objects.filter(run_uuid=scenario.run_uuid).first()

            batt_roundtrip_efficiency = batt.internal_efficiency_pct \
                                        * batt.inverter_efficiency_pct \
                                        * batt.rectifier_efficiency_pct

            results = simulate_outage(
                batt_kwh=batt.size_kwh or 0,
                batt_kw=batt.size_kw or 0,
                pv_kw_ac_hourly=pv.year_one_power_production_series_kw,
                init_soc=batt.year_one_soc_series_pct,
                critical_loads_kw=load_profile.critical_load_series_kw,
                batt_roundtrip_efficiency=batt_roundtrip_efficiency,
                diesel_kw=gen.size_kw,
                fuel_available=gen.fuel_avail_gal,
                b=gen.fuel_intercept_gal_per_hr,
                m=gen.fuel_slope_gal_per_kwh,
                diesel_min_turndown=gen.min_turn_down_pct
            )

            ResilienceModel.objects.filter(id=rm.id).update(**results)

        response = JsonResponse(results)
        return response

    except Exception as e:

        if type(e).__name__ == 'DoesNotExist':
            msg = "Scenario {} does not exist.".format(run_uuid)
            return JsonResponse({"Error": msg}, content_type='application/json', status=404)
        else:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            err = UnexpectedError(exc_type, exc_value, exc_traceback, task='resilience_stats', run_uuid=run_uuid)
            err.save_to_db()
            return JsonResponse({"Error": err.message}, status=500)
