from tastypie.validation import Validation
from tastypie.exceptions import BadRequest
from api_definitions import *
from api_input_validation import *
from log_levels import log

class REoptResourceValidation(Validation):

    def check_individual(self, input_dictionary, errors):

        for key, value in input_dictionary.items():

            if key not in inputs(full_list=True):
                errors = self.append_errors(errors, key, 'This key name does not match a valid input.')
                logstring = "Key: '" + str(key) + "' does not match a valid input!"
                log("ERROR", logstring)
                raise BadRequest(logstring)

            if value is None and key in inputs(just_required=True).keys():
                if not self.swaps_exists(input_dictionary.keys(), key):
                    errors = self.append_errors(errors, key, 'This input is required and cannot be null.')
                    logstring = "Value for key: " + str(key) + " is required and cannot be null!"
                    log("ERROR", logstring)
                    raise BadRequest(logstring)

            else:
                field_def = inputs(full_list=True)[key]
                format_errors = self.check_input_format(key,value,field_def)
                if not format_errors:
                    if 'max' in field_def and field_def['max'] is not None:
                        max_value = field_def['max']
                        # handle case that one input depends upon another
                        if type(field_def['max']) == str and field_def['max'] in input_dictionary:
                            field_def_depend = inputs(full_list=True)[field_def['max']]
                            max_value = field_def_depend['default']
                            if input_dictionary[field_def['max']] is not None:
                                max_value = input_dictionary[field_def['max']]

                        format_errors += self.check_max(key, value, field_def, max_value)

                    if 'min' in field_def and field_def['min'] is not None:
                        format_errors += self.check_min(key, value, field_def)

                    if 'restrict_to' in field_def and field_def['restrict_to'] is not None:
                        format_errors += self.check_restrict_to(key, value, field_def['restrict_to'])

                    if 'length' in field_def and field_def['length'] is not None:
                        format_errors += self.check_length(key, value, field_def['length'])

                #specific_errors 
                if format_errors:
                    errors = self.append_errors(errors, key, format_errors)
                    raise BadRequest(format_errors)

        return errors

    def is_valid(self, bundle, request=None):

        errors = {}

        missing_required = self.missing_required(bundle.data.keys())

        if missing_required:
            message = [self.get_missing_required_message(m) for  m in missing_required]
            errors = self.append_errors(errors,"Missing_Required",message)

        missing_dependencies = self.missing_dependencies(bundle.data, exclude=missing_required)
        if missing_dependencies:
            message = [self.get_missing_dependency_message(m) for m in missing_dependencies]
            errors = self.append_errors(errors, "Missing_Dependencies", message)

        errors = self.check_individual(bundle.data, errors)

        return errors

    def check_input_format(self,key,value,field_definition):

        invalid_msg = 'Invalid format: Expected %s, got %s for %s'\
                      % (str(field_definition['type']).split(" ")[-1][0:-1], str(type(value)).split(" ")[-1][0:-1], key)
        
        try:
            
            new_value = field_definition['type'](value)
            
            if value not in [new_value]:
                return [invalid_msg]

            return []

        except Exception as e:
            if value is None:
                return []
            else:
                return [invalid_msg]

    def check_min(self, key, value, fd):
        new_value = value
        if fd.get('pct') is True:
            if value > 1:
                new_value = value*0.01

        if new_value < fd['min'] and value is not None:
            if not fd.get('pct'):
                return ['Invalid value: %s: %s is less than the minimum, %s' % (key, value, fd['min'])]
            else:
                return ['Invalid value: %s: %s is less than the minimum, %s %%' % (key, value, fd['min'] * 100)]
        return []

    def check_max(self, key, value, fd, max_value):
        new_value = value
        if fd.get('pct') is True:
            if value > 1:
                new_value = value * 0.01

        if new_value > fd['max'] and value is not None:
            if not fd.get('pct'):
                return ['Invalid value: %s: %s is greater than the  maximum, %s' % (key, value, fd['max'])]
            else:
                return ['Invalid value: %s: %s is greater than the  maximum, %s %%' % (key, value, fd['max']*100)]
        return []

    def check_restrict_to(self, key, value, range):
        if value not in range and value is not None:
            return ['Invalid value: %s: %s is not in %s' % (key, value, range)]
        return []

    def append_errors(self, errors, key, value):
        if 'Errors' in errors.keys():
            if key not in errors["Errors"].keys():
                errors["Errors"][key] = value
            else:
                errors["Errors"][key] += value
        else:
            errors['Errors']  =  {key: value}
        return errors

    def get_missing_required_message(self, input):
        definition_values = inputs(full_list=True)[input]
        swap = definition_values.get('swap_for')
        message = input
        if swap is not None:
            message +=  " (OR %s)" % (" and ".join(definition_values['swap_for']))
        return message

    def get_missing_dependency_message(self, input):
        definition_values = inputs(full_list=True)[input]

        dependency_of = []
        for k, v in inputs(full_list=True).items():
            value = v.get('depends_on')
            if value is not None:
                if input in value:
                    dependency_of.append(k)
        return "%s (%s depend(s) on this input.)" % (input, "  and ".join(dependency_of))

    def missing_dependencies(self, bundle, exclude=[]):
        # Check if field depends on non-required fields
        missing = []
        for f, v in bundle.items():  # all possible inputs

            if v is not None:  # if the value is None we don't care about dependencies

                if not self.swaps_exists(bundle.keys(), f):  # if a swap exists we don't care about dependencies
                    dependent = inputs(full_list=True)[f].get('depends_on')

                    if dependent is not None and f not in exclude:
                        for d in dependent:
                            if d not in bundle.keys() and not self.swaps_exists(bundle.keys(), d):
                                # dependencies can have swaps too (eg. load_size for load_monthly_kwh)
                                missing.append(d)
        return missing

    def swaps_exists(self, key_list, f):
        swap = inputs(full_list=True)[f].get('swap_for')
        swap_exists = False

        if swap is not None and any(s in key_list for s in swap):
            swap_exists = True
        return swap_exists

    def missing_required(self,key_list):
        missing = list(set(inputs(just_required=True)) - set(key_list))
        output = []
        for field in missing:  # Check if field can be swappedout for others
            if not self.swaps_exists(key_list, field):
                output.append(field)

        return output

    def check_length(self, key, value, correct_length):
        if len(value) != correct_length:
            return ['Invalid number of values for %s: entered %s values, %s required' % (key, len(value), correct_length)]
        return []
