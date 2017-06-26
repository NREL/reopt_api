from django.db import models
from django.contrib.postgres.fields import *
from tastypie.exceptions import ImmediateHttpResponse
from outage_simulator import simulate_outage
from urls import get_current_api
from api_definitions import inputs, outputs


class ResilienceCase(models.Model):

    #Inputs
    pv_kw = models.FloatField(null=True, blank=True)
    batt_kw = models.FloatField(null=True, blank=True)
    batt_kwh = models.FloatField(null=True, blank=True)
    load = ArrayField(models.FloatField(blank=True), null=True, blank=True, default=[])
    pv_kw_ac_hourly = ArrayField(models.FloatField(blank=True), null=True, blank=True, default=[])
    init_soc = ArrayField(models.FloatField(blank=True), null=True, blank=True, default=[])
    crit_load_factor = models.FloatField(null=True, blank=True)
    batt_roundtrip_efficiency = models.FloatField(null=True, blank=True)
    api_version = models.TextField(blank=True, default='', null=False)

    #Outputs
    resilience_by_timestep = ArrayField(models.FloatField(blank=True, null=True), null=True, blank=True, default=[])
    resilience_hours_min = models.FloatField(blank=True, null=True)
    resilience_hours_max = models.FloatField(blank=True, null=True)
    resilience_hours_avg = models.FloatField(blank=True, null=True)

    @staticmethod
    def run(bundle):

        data = dict({k: bundle.data.get(k) for k in inputs(full_list=True).keys() if k in bundle.data.keys() and bundle.data.get(k) is not None })

        model_results = simulate_outage(**data)
        
        if "ERROR" in model_results.keys():
            raise ImmediateHttpResponse(response=ResilienceCase.error_response(bundle.request, model_results))

        else:

            for k in model_results.keys():
                data[k] = model_results[k]
            
            data['api_version'] = get_current_api()
            
            output_obj = ResilienceCase(**data)
            output_obj.save()

        return output_obj

    @staticmethod
    def append_resilience_stats(data):

        resilience_params = ResilienceCase().inputs_from_reo_output(data)
        resilience_results = simulate_outage(**resilience_params)

        resilience_case = ResilienceCase(**resilience_results)
        resilience_case.save()

        for k in outputs().keys():
            data[k] = resilience_results[k]

        return data


    @staticmethod
    def inputs_from_reo_output(data):

        output = {}

        translator = {'load':'year_one_electric_load_series', 'init_soc':'year_one_battery_soc_series'}

        res_inputs = inputs()

        for res_k in res_inputs.keys():

            if res_k in translator.keys():
                reo_k = translator[res_k]
            else:
                reo_k = res_k

            if res_k == 'batt_roundtrip_efficiency':
                value = data['batt_efficiency'] * data['batt_inverter_efficiency'] * data['batt_rectifier_efficiency']
            else:
                value = data.get(reo_k)

            output[res_k] = value

        return output
