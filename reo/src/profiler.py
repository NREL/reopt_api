import time

class Profiler:

    keys_allowed = ['pre_setup_scenario',
                    'setup_scenario',
                    'reopt',
                    'reopt_bau',
                    'parse_run_outputs'
                    ]


    def __init__(self, uuid):
        self.uuid = uuid
        self.profile = dict()

    def profileStart(self, profileDescription):
        if profileDescription in self.keys_allowed:
            self.profile[profileDescription] = dict()
            self.profile[profileDescription]['start'] = time.time()

    def profileEnd(self, profileDescription):
        if profileDescription in self.keys_allowed:
            self.profile[profileDescription]['end'] = time.time()

            if 'start' in self.profile[profileDescription]:
                self.profile[profileDescription]['duration'] = self.profile[profileDescription]['end'] - \
                                                               self.profile[profileDescription]['start']
    def getKeys(self):
        return self.profile.keys()

    def getDuration(self, profileDescription):
        return self.profile[profileDescription]['duration']