import traceback as tb
from reo.models import ErrorModel
from reo.log_levels import log


class REoptError(Exception):
    """
    Base class for exceptions in reo app.
    """

    def __init__(self, task='', name='', run_uuid='', message='', traceback='', user_uuid=''):
        """

        :param task: task where error occurred, e.g. scenario_setup, reopt, process_results
        :param name: name of error class, e.g. SubprocessTimeout
        :param run_uuid:
        :param user_uuid:
        :param message: message that is sent back to user in messages: errors
        :param traceback: sys.exc_info()[2]
        """
        if message == "Wind Dataset Timed Out":
            msg_with_email = ". Please try again later or email reopt@nrel.gov for support."
        elif run_uuid:
            msg_with_email = " Please email reopt@nrel.gov with your run_uuid ({}) for support.".format(run_uuid)
        elif user_uuid:
            msg_with_email = " Please email reopt@nrel.gov with your user_uuid ({}) for support.".format(user_uuid) 
        else:
            msg_with_email = " Please email reopt@nrel.gov for support."

        if 'infeasible' not in traceback:
            self.message = message + msg_with_email  # msg_with_email included in messages: error response, but not in error table
        else:
            self.message = message
        self.task = task
        self.run_uuid = run_uuid
        self.user_uuid = user_uuid
        self.traceback = traceback
        self.name = name
        log.error(traceback)

    def save_to_db(self):
        """
        ErrorModel(django.db.models.Model)
            task = models.TextField(blank=True, default='')
            name = models.TextField(blank=True, default='')
            run_uuid = models.TextField(blank=True, default='')
            user_uuid = models.TextField(blank=True, default='')
            message = models.TextField(blank=True, default='')
            traceback = models.TextField(blank=True, default='')
        """

        em = ErrorModel(task=self.task, name=self.name, run_uuid=self.run_uuid, user_uuid=self.user_uuid, message=self.message,
                        traceback=self.traceback)
        em.save()


class SubprocessTimeout(REoptError):
    """
    Exception raised when a subprocess times out

    """
    __name__ = 'SubprocessTimeout'

    def __init__(self, task='reopt', run_uuid='', message='', traceback=''):
        """

        :param task: task where error occurred
        :param run_uuid:
        :param message: message that is sent back to user in messages: errors
        :param traceback: saved to database for debugging
        """
        super(SubprocessTimeout, self).__init__(task, self.__name__, run_uuid, message, traceback)


class NotOptimal(REoptError):
    """
    Exception raised when a subprocess times out

    """
    __name__ = 'NotOptimal'

    def __init__(self, task='reopt', run_uuid='', status=''):

        msg = "REopt could not find an optimal solution for these inputs."
        if status == 'infeasible':
            msg += " An 'infeasible' status is likely due to system size constraints that prevent the load from being met during a grid outage. "\
                    + "Please adjust the selected technologies and size constraints and try again."
        super(NotOptimal, self).__init__(task, self.__name__, run_uuid, message=msg, traceback="status: " + status)


class REoptFailedToStartError(REoptError):
    """
    Exception raised when REopt fails to start (subprocess.CalledProcessError)

    """
    __name__ = 'REoptFailedToStartError'

    def __init__(self, task='reopt', run_uuid='', message='', traceback=''):
        """

        :param task: task where error occurred
        :param run_uuid:
        :param message: message that is sent back to user in messages: errors
        :param traceback: saved to database for debugging
        """
        super(REoptFailedToStartError, self).__init__(task, self.__name__, run_uuid, message, traceback)


class RequestError(REoptError):
    """
    Exception class for reo.views.results
    """
    __name__ = "RequestError"

    def __init__(self, task='reo.views.results', run_uuid='', message='', traceback=''):
        """

        :param task: task where error occurred
        :param run_uuid:
        :param message: message that is sent back to user in messages: errors
        :param traceback: saved to database for debugging
        """
        super(RequestError, self).__init__(task, self.__name__, run_uuid, message, traceback)


class UnexpectedError(REoptError):
    """
    REopt catch-all exception class

    Attributes:
        message - explanation of the error
    """

    __name__ = 'UnexpectedError'

    def __init__(self, exc_type, exc_value, exc_traceback, task='', run_uuid='', user_uuid=''):
        debug_msg = "exc_type: {}; exc_value: {}; exc_traceback: {}".format(exc_type, exc_value, tb.format_tb(exc_traceback))
        message = "Unexpected Error."
        super(UnexpectedError, self).__init__(task=task, name=self.__name__, run_uuid=run_uuid, user_uuid=user_uuid, message=message,
                                              traceback=debug_msg)


class WindDownloadError(REoptError):
    """
    REopt catch-all exception class

    Attributes:
        message - explanation of the error
    """

    __name__ = 'WindDownloadError'

    def __init__(self, task='', run_uuid='', user_uuid=''):
        message = "Wind Dataset Timed Out"
        super(WindDownloadError, self).__init__(task=task, name=self.__name__, run_uuid=run_uuid, user_uuid=user_uuid, message=message,
                                              traceback='')


class LoadProfileError(REoptError):
    """
        REopt catch-all exception class

        Attributes:
            message - explanation of the error
        """

    __name__ = 'LoadProfileError'

    def __init__(self, exc_value, exc_traceback, task='', run_uuid='', user_uuid=''):
        debug_msg = "exc_value: {}; exc_traceback: {}".format(exc_value,tb.format_tb(exc_traceback))
        message = "If the load profile is not uploaded by the user, then 'doe_reference_name' is a required input."
        super(LoadProfileError, self).__init__(task=task, name=self.__name__, run_uuid=run_uuid, user_uuid=user_uuid,
                                              message=message, traceback=debug_msg)

