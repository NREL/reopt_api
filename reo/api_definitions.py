from tastypie import fields
import os

def null_input_values()
  return ['null']

def inputs(filter='',full_list=False,just_required=False):

    output = {
      'user_id': {'req': True, 'type': str, 'null': False, 'pct': False, "needed_for": [], 'default':None
                  ,"description": "User ID", "units":None},

      # Required
      'analysis_period': {'req': False, 'type': int, 'null': True, 'pct': False, "needed_for": ['economics'],
                          'default': 25, 'min': 0, 'max': None,
                          "description": "Period of Analysis", "units": 'years'},
                          
      'latitude': {'req': True, 'type': float, 'null': False, 'pct': False,
                   "needed_for": ['economics', 'gis', 'loads', 'pvwatts'],
                   "description": "Site Latitude", "units": 'degrees'},

      'longitude': {'req': True, 'type': float, 'null': False, 'pct': False,
                    "needed_for": ['economics', 'gis', 'loads', 'pvwatts'],
                    "description": "Site Longitude", "units": 'degrees'},

      'pv_cost': {'req': True, 'type': float, 'null': False, 'pct': False, "needed_for": ['economics'], 'min': 0,
                  'max': None, 'default': 2160,
                  "description": "Nominal PV Cost", "units": 'dollars per kilowatt'},

      'pv_om': {'req': True, 'type': float, 'null': False, 'pct': False, "needed_for": ['economics'], 'min': 0,
                'max': None, 'default': 20,
                "description": "Nominal PV Operation and Maintenance Cost", "units": 'dollars per kilowatt-year'},

      'batt_cost_kw': {'req': True, 'type': float, 'null': False, 'pct': False, "needed_for": ['economics'], 'min': 0,
                       'max': None, 'default': 1600,
                       "description": "Nominal Battery Inverter Cost", "units": 'dollars per kilowatt'},

      'batt_cost_kwh': {'req': True, 'type': float, 'null': False, 'pct': False, "needed_for": ['economics'], 'min': 0,
                        'max': None, 'default': 500,
                        "description": "Nominal Battery Cost", "units": 'dollars per kilowatt-hour'},

      'owner_discount_rate': {'req': True, 'type': float, 'null': False, 'pct': True, "needed_for": ['economics'],
                              'min': 0, 'max': 1, 'default': 0.08,
                              "description": "Owner Discount Rate", "units": 'decimal percent'},

      'offtaker_discount_rate': {'req': True, 'type': float, 'null': False, 'pct': True, "needed_for": ['economics'],
                                 'min': 0, 'max': 1, 'default': 0.08,
                                 "description": "Offtaker Discount Rate", "units": 'decimal percent'},

      'blended_utility_rate': {'req': True, 'depends_on': ['demand_charge'], 'swap_for': ['urdb_rate'], 'type': list,
                               'null': False, 'pct': False, "needed_for": ['economics', 'utility'],
                                "description": "Blended Utility Rate", "units": '$/kWh'},


      'demand_charge': {'req': True, 'depends_on': ['blended_utility_rate'], 'swap_for': ['urdb_rate'], 'type': list,
                        'null': False, 'pct': False, "needed_for": ['economics', 'utility'],
                        "description": "Demand Charge", "units": '$/kW'},

      'urdb_rate': {'req': True, 'swap_for': ['demand_charge', 'blended_utility_rate'], 'type': dict, 'null': False,
                    'pct': False, "needed_for": ['economics']},

      # Not Required
      'load_profile_name': {'req': False, 'type': str, 'null': True, 'pct': False, "needed_for": ['economics'],
                       "description": "Generic Load Profile Type",
                       'restrict_to': default_load_profiles()+[None]},

      'load_size': {'req': False, 'type': float, 'null': True, 'pct': False, "needed_for": ['economics'], 'min': 0,
                    'max': None,
                    "description": "Annual Load Size", "units": 'kWh'},

      'load_8760_kw': {'req': False, 'type': list, 'null': True, 'pct': False, "needed_for": ['economics'],
                       "description": "Hourly Power Demand", "units": 'kW'},

      'load_monthly_kwh': {'req': False, 'type': list, 'null': True, 'pct': False, "needed_for": ['economics'],
                           "description": "Monthly Energy Demand", "units": 'kWh'},

      'utility_name': {'req': False, 'type': str, 'null': True, 'pct': False, "needed_for": ['economics', 'utility'],
                       "description": "Utility Name"},

      'rate_name': {'req': False, 'type': str, 'null': True, 'pct': False, "needed_for": ['economics', 'utility'],
                    "description": "Rate Name"},

      'rate_degradation': {'req': False, 'type': float, 'null': False, 'pct': True, "needed_for": ['economics'],
                           'min': 0, 'max': 1, 'default': 0.005,
                           "description": "Annual Degredation for Solar PV Panels", "units": 'decimal percent'},

      'rate_inflation': {'req': False, 'type': float, 'null': False, 'pct': True, "needed_for": ['economics'], 'min': 0,
                         'max': 1, 'default': 0.02,
                         "description": "Annual Inflation Rate", "units": 'decimal percent per year'},

      'rate_escalation': {'req': False, 'type': float, 'null': False, 'pct': True, "needed_for": ['economics'],
                          'min': -1, 'max': 1, 'default': 0.0039,
                          "description": "Annual Cost of  Electricity Escalation Rate", "units": 'decimal percent per year'},

      'rate_tax': {'req': False, 'type': float, 'null': True, 'pct': False, "needed_for": ['economics'], 'min': 0,
                   'max': 1, 'default': 0.35,
                   "description": "Tax Rate", "units": 'decimal percent'},

      'rate_itc': {'req': False, 'type': float, 'null': True, 'pct': False, "needed_for": ['economics'], 'min': 0,
                   'max': 1, 'default': 0.30,
                   "description": "Investment Tax Credit rate", "units": 'decimal percent'},

      'batt_replacement_cost_kw': {'req': False, 'type': float, 'null': False, 'pct': False,
                                   "needed_for": ['economics'], 'min': 0, 'max': None, 'default': 200,
                                   "description": "Battery Inverter Replacement Cost", "units": '$/kW'},

      'batt_replacement_cost_kwh': {'req': False, 'type': float, 'null': False, 'pct': False,
                                    "needed_for": ['economics'], 'min': 0, 'max': None, 'default': 200,
                                    "description": "Battery Replacement Cost", "units": '$/kWh'},

      'batt_replacement_year': {'req': False, 'type': int, 'null': False, 'pct': False, "needed_for": ['economics'],
                                'min': 0, 'max': None, 'default': 10,
                                "description": "Battery Replacement Year", "units": 'year'},

      'flag_macrs': {'req': False, 'type': bool, 'null': False, 'pct': False, "needed_for": ['economics'], 'default': 1,
                     'min': 0, 'max': 1,
                     "description": "Use Modified Advanced  Cost Recovery System (MACRS) Deductions", "units": 'boolean'},

      'flag_itc': {'req': False, 'type': bool, 'null': False, 'pct': False, "needed_for": ['economics'], 'default': 1,
                   'min': 0, 'max': 1,
                   "description": "Use Investment Tax Credit Deductions", "units": 'boolean'},

      'flag_bonus': {'req': False, 'type': bool, 'null': False, 'pct': False, "needed_for": ['economics'], 'default': 1,
                     'min': 0, 'max': 1,
                     "description": "Use Bonus Deductions", "units": 'boolean'},

      'flag_replace_batt': {'req': False, 'type': bool, 'null': False, 'pct': False, "needed_for": ['economics'],
                            'default': 1, 'min': 0, 'max': 1,
                            "description": "Use Battery Replacement Scheme", "units": 'boolean'},

      'macrs_years': {'req': False, 'type': int, 'null': False, 'pct': False, "needed_for": ['economics'], 'default': 5,
                      'min': 5, 'max': 7, 'restrict_to': [5, 7],
                      "description": "MACRS depreciation timeline for Solar and Storage", "units": 'years'},

      'macrs_itc_reduction': {'req': False, 'type': float, 'null': False, 'pct': True, "needed_for": ['economics'],
                              'default': 0.5, 'min': 0, 'max': 1,
                              "description": "If ITC is taken with MACRS, the depreciable value is reduced by this fraction of the ITC", "units": 'decimal percent'},

      'bonus_fraction': {'req': False, 'type': float, 'null': False, 'pct': True, "needed_for": ['economics'],
                         'default': 0.5, 'min': 0, 'max': 1,
                         "description": "This fraction of the depreciable value is taken in year 1 in addition to MACRS",
                         "units": 'decimal percent'},

      'dataset': {'req': False, 'type': str, 'null': False, 'pct': False, "needed_for": ['pvwatts'], 'default': "tmy3",
                  'restrict_to': ['tmy2', 'tmy3', 'intl', 'IN'], "description": "Climate Dataset",},

      'inv_eff': {'req': False, 'type': float, 'null': False, 'pct': True, "needed_for": ['pvwatts'], 'default': 0.92,
                  'min': 0.9, 'max': 0.995, "description": "Inverter Efficiency at Rated Power",
                  "units": "decimal percent"},

      'dc_ac_ratio': {'req': False, 'type': float, 'null': False, 'pct': False, "needed_for": ['pvwatts'],
                      'default': 1.1, 'min': 0, 'max': None, "description": "DC to AC ratio"},

      'azimuth': {'req': False, 'type': float, 'null': False, 'pct': False, "needed_for": ['pvwatts'], 'default': 180,
                  'min': 0, 'max': 360, "description": "Azimuth Angle", "units": "degrees"},

      'system_capacity': {'req': False, 'type': float, 'null': False, 'pct': False, "needed_for": ['pvwatts'],
                          'default': 1, 'min': 0.05, 'max': 500000, "description": "Nameplate capacity", "units": "kW"},

      'array_type': {'req': False, 'type': int, 'null': False, 'pct': False, "needed_for": ['pvwatts'], 'default': 0,
                     'restrict_to': [0, 1, 2, 3, 4], "description": "Fixed or Axis Type"},  # fixed open rack

      'module_type': {'req': False, 'type': int, 'null': False, 'pct': False, "needed_for": ['pvwatts'], 'default': 0,
                      'restrict_to': [0, 1, 2], "description": "Module Type"},  # standard

      'timeframe': {'req': False, 'type': str, 'null': False, 'pct': False, "needed_for": ['pvwatts'],
                    'default': 'hourly', 'restrict_to': ['hourly', 'monthly'],
                    "description": "Granularity of Output Response"},

      'losses': {'req': False, 'type': float, 'null': False, 'pct': True, "needed_for": ['pvwatts'], 'default': 0.14,
                 'min': -0.05, 'max': 0.99, "description": "System Losses type", "units": "decimal percent"},

      'radius': {'req': False, 'type': float, 'null': False, 'pct': False, "needed_for": ['pvwatts'], 'default': 0,
                 'min': 0, 'max': None, "description": "Search Distance to  Nearest Climate Data  Station",
                 "units": "miles"},

      'tilt': {'req': False, 'type': float, 'null': False, 'pct': False, "needed_for": ['pvwatts'], 'default': None,
               'min': 0, 'max': 90, "description": "Tilt Angle", "units": "degrees"},

      'gcr': {'req': False, 'type': float, 'null': False, 'pct': False, "needed_for": ['pvwatts'], 'default': 0.4,
              'min': 0, 'max': 3, "description": "Ground  Cover Ratio",},
    }

    if full_list:
        return output

    if filter != '':
        output = {k:v for k, v in output.items() if filter in v['needed_for'] }

    if just_required:
        output = dict((k, v) for k, v in output.items() if v['req'])
    return output

def outputs():
    return {'lcc': {'type': float, 'null': True,'pct': False,
                    "description": "Lifecycle Cost", "units":'dollars'},

           'npv': {'type': float, 'null': True,'pct': False,
                   "description": "Net Present  Value of System", "units":'dollars'},

           'utility_kwh': {'type': float, 'null': True,'pct': False,
                           "description": "Energy Supplied from the Grid", "units": 'kWh'},

           'pv_kw': {'type': float, 'null': True,'pct': False,
                     "description": "Recommned PV System Size", "units": 'kW'},

           'batt_kw': {'type': float, 'null': True,'pct': False,
                       "description": "Recommended Battery Inverter Size", "units": 'kW'},

           'batt_kwh': {'type': float, 'null': True,'pct': False,
                        "description": "Recommended Battery Size", "units": 'kWh'}
            }

# default load profiles
def default_load_profiles():
    return  ['FastFoodRest', 'Flat', 'FullServiceRest', 'Hospital', 'LargeHotel', 'LargeOffice',
                         'MediumOffice', 'MidriseApartment', 'Outpatient', 'PrimarySchool', 'RetailStore',
                         'SecondarySchool', 'SmallHotel', 'SmallOffice', 'StripMall', 'Supermarket', 'Warehouse']

def default_building():
    return "Hospital"

# default locations
def default_cities():
    return ['Miami', 'Houston', 'Phoenix', 'Atlanta', 'LosAngeles', 'SanFrancisco', 'LasVegas', 'Baltimore',
                'Albuquerque', 'Seattle', 'Chicago', 'Boulder', 'Minneapolis', 'Helena', 'Duluth', 'Fairbanks']

# default latitudes
def default_latitudes():
    return [25.761680, 29.760427, 33.448377, 33.748995, 34.052234, 37.774929, 36.114707, 39.290385,
                     35.085334, 47.606209, 41.878114, 40.014986, 44.977753, 46.588371, 46.786672, 64.837778]

# default longitudes
def default_longitudes():
    return [-80.191790, -95.369803, -112.074037, -84.387982, -118.243685, -122.419416, -115.172850,
                      -76.612189, -106.605553, -122.332071, -87.629798, -105.270546, -93.265011, -112.024505,
                      -92.100485, -147.716389]
def default_blended_rate():
    return [0.05066,0.05066,0.05066,0.05066,0.05066,0.05066,0.05066,0.05066,0.05066,0.05066,0.05066,0.05066]

def default_demand_charge():
    return [10.00,10.00,10.00,10.00,10.00,10.00,10.00,10.00,10.00,10.00,10.00,10.00]

def default_load_monthly():
    return [100,200,250,300,350,350,400,400,350,250,250,200]

def default_load_hourly():
    return [1,1,1,1,1,1,2,2,3,4,5,6,7,6,5,4,3,3,2,2,1,1,1,1]*365

def default_urdb_rate():
    return {
    "label": "55fc81bf682bea28da64e94a",
    "uri": "http://en.openei.org/apps/USURDB/rate/view/55fc81bf682bea28da64e94a",
    "sector": "Commercial",
    "energyweekendschedule": [
      [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0
      ]
    ],
    "enddate": 1451520000,
    "flatdemandunit": "kW",
    "supersedes": "53a0b1b65257a3186f04ca17",
    "demandrateunit": "kW",
    "eiaid": 6452,
    "phasewiring": "Single and 3-Phase",
    "demandratestructure": [
      [
        {
          "rate": 0,
          "adj": 2.9
        }
      ],
      [
        {
          "rate": 9.11,
          "adj": 2.9
        }
      ]
    ],
    "peakkwcapacitymin": 500,
    "revisions": [
      1431595766,
      1431596033,
      1449833552
    ],
    "energyratestructure": [
      [
        {
          "rate": 0.03701,
          "adj": 0.00267,
          "unit": "kWh"
        }
      ],
      [
        {
          "rate": 0.06239,
          "adj": 0.00267,
          "unit": "kWh"
        }
      ]
    ],
    "startdate": 1433116800,
    "demandcomments": "Demand adjustment includes conservation, capacity charges.",
    "utility": "Florida Power & Light Co.",
    "fixedmonthlycharge": 59.51,
    "demandweekdayschedule": [
      [
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        1,
        1,
        1,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        1,
        1,
        1,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        1,
        1,
        1,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        1,
        1,
        1,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        1,
        1,
        1,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        1,
        1,
        1,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        0,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        0,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        0,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        0,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        0,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        0,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        0,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        1,
        1,
        1,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        1,
        1,
        1,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        1,
        1,
        1,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        1,
        1,
        1,
        0,
        0
      ]
    ],
    "name": "GLSDT-1 (General Service Large Demand - Time-Of-Use)",
    "source": "https://www.fpl.com/rates/pdf/June2015_Business.pdf   \r\n   https://www.fpl.com/rates/pdf/electric-tariff-section8.pdf",
    "demandweekendschedule": [
      [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0
      ]
    ],
    "energycomments": "Rate includes Energy base charge and fuel charge || Adjustment includes storm and environmental",
    "approved": True,
    "peakkwcapacitymax": 2000,
    "country": "USA",
    "energyweekdayschedule": [
      [
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        1,
        1,
        1,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        1,
        1,
        1,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        1,
        1,
        1,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        1,
        1,
        1,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        1,
        1,
        1,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        1,
        1,
        1,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        0,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        0,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        0,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        0,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        0,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        0,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        0,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        1,
        1,
        1,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        1,
        1,
        1,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        1,
        1,
        1,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        1,
        1,
        1,
        0,
        0
      ]
    ],
    "sourceparent": "http://www.fpl.com/rates/"
  }
