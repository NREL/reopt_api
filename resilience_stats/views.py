from django.http import JsonResponse
from reo.models import ScenarioModel, SiteModel, PVModel, StorageModel, LoadProfileModel
from models import ResilienceModel 
from reo.utilities import API_Error
from outage_simulator import simulate_outage


def resilience_stats(request):
   
    uuid = request.GET.get('run_uuid')
 
    try:
        scenario = ScenarioModel.objects.get(run_uuid=uuid)
    
    except Exception as e:
        return API_Error(e).response

    rm = ResilienceModel.create(scenariomodel=scenario)
    site = SiteModel.objects.filter(run_uuid=scenario.run_uuid).first()
    batt = StorageModel.objects.filter(run_uuid=scenario.run_uuid).first()
    pv = PVModel.objects.filter(run_uuid=scenario.run_uuid).first()
    load_profile = LoadProfileModel.objects.filter(run_uuid=scenario.run_uuid).first()

    batt_roundtrip_efficiency = batt.internal_efficiency_pct \
                                * batt.inverter_efficiency_pct \
                                * batt.rectifier_efficiency_pct
    results = simulate_outage(
        pv_kw=pv.size_kw or 0,
        batt_kwh=batt.size_kwh or 0,
        batt_kw=batt.size_kw or 0,
        load=load_profile.year_one_electric_load_series_kw,
        pv_kw_ac_hourly=pv.year_one_power_production_series_kw,
        init_soc=batt.year_one_soc_series_pct,
        crit_load_factor=load_profile.critical_load_pct,
        batt_roundtrip_efficiency=batt_roundtrip_efficiency,
    )

    ResilienceModel.objects.filter(id=rm.id).update(**results)
    
    response = JsonResponse(results)
    return response
