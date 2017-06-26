from datetime import datetime


def inputs(filter='', full_list=False, just_required=False):
    output = {

        'pv_kw': {'req': True,'type': float, 'null': True, 'pct': False,
                  "description": "PV System Size", "units": 'kW'},

        'batt_kw': {'req': True,'type': float, 'null': True, 'pct': False,
                    "description": "Battery Inverter Size", "units": 'kW'},

        'batt_kwh': {'req': True,'type': float, 'null': True, 'pct': False,
                     "description": "Battery Size", "units": 'kWh'},

        'load': {'req': True, 'type': list, 'null': False, 'pct': False, "needed_for": [], 'default': [0]*8760,
                 "description": "Hourly Load Profile", "units": 'kW', "tool_tip": "Hourly load profile in kW."},

        'pv_kw_ac_hourly': {'req': True, 'type': list, 'null': False, 'pct': False, "needed_for": [], 'default': [0]*8760,
                        "description": "Hourly Solar Resource Profile", "units": 'kW',
                        "tool_tip": "Hourly incoming solar profile in kw."},

        'init_soc': {'req': True, 'type': list, 'null': False, 'pct': True, "needed_for": [], 'default': [1]*8760,
                     "description": "Initial State Of Charge", "units": None,
                     "tool_tip": "Fractional initial state of charge for simulating outages."},

        'crit_load_factor': {'req': False, 'type': float, 'null': False, 'pct': True, "needed_for": ['resilience'], 'default': 0.5,
                     "min": 0, "max": 1, "description": "Critical Load Factor", "units": None,
                     "tool_tip": "Critical load factor is used to scale the load during an outage. \
                                  Value must be between zero and one, inclusive."},

        'batt_roundtrip_efficiency': {'req': True, 'type': float, 'null': False, 'pct': False, "needed_for": [], 'min': 0,
                         'max': 1, 'default': 0.829,
                         "description": "Battery roundtrip efficiency", "units": 'percent',
                         "tool_tip": 'Battery roundtrip efficiency'},

        }
    if full_list:
      return output

    return output


def outputs():
    return {'resilience_by_timestep':
                {'req': True, 'type': float, 'null': True, 'pct': False,
                 "description": "List of hours survived for outages starting at every time step", "units": 'hours'},
            'resilience_hours_min':
                {'req': True, 'type': float, 'null': True, 'pct': False,
                 "description": "Minimum hours survived", "units": 'hours'},
            'resilience_hours_max':
                {'req': True, 'type': float, 'null': True, 'pct': False,
                 "description": "Maximum hours survived", "units": 'hours'},
            'resilience_hours_avg':
                {'req': True, 'type': float, 'null': True, 'pct': False,
                 "description": "Average hours survived", "units": 'hours'},
            }
