from reo.models import ErrorModel
from reo.log_levels import log
"""
ErrorModel(django.db.models.Model)
    task = models.TextField(blank=True, default='')
    name = models.TextField(blank=True, default='')
    run_uuid = models.TextField(blank=True, default='')
    message = models.TextField(blank=True, default='')
    traceback = models.TextField(blank=True, default='')
"""


class REoptError(Exception):
    """
    Base class for exceptions in reo app.
    call to super().__init__ will save ErrorModel to database.

    """

    def __init__(self, task='', name='', run_uuid='', message='', traceback=''):
        """

        :param task: task where error occurred, e.g. scenario_setup, reopt, process_results
        :param name: name of error class, e.g. SubprocessTimeout
        :param run_uuid:
        :param message: message that is sent back to user in messages: errors
        :param traceback: sys.exc_info()[2]
        """
        msg_with_email = " Please email reopt@nrel.gov with your run_uuid ({}) for support.".format(run_uuid)
        ErrorModel.create(task=task, name=name, run_uuid=run_uuid, message=message, traceback=traceback)
        self.message = message + msg_with_email  # msg_with_email included in messages: error response, but not in error table
        self.task = task
        self.run_uuid = run_uuid
        self.traceback = traceback


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

    def __init__(self, task='reopt', run_uuid='', traceback='', status=''):
        """

        :param task: task where error occurred
        :param run_uuid:
        :param traceback: saved to database for debugging
        """
        log("INFO", "WHAT?!?!?!")
        msg = "REopt could not find an optimal solution for these inputs."
        if status == 'infeasible':
            msg += " The problem is likely due to constraints that make a solution infeasible, " \
                   + "such as a grid outage without enough resources to meet the load during the outage."
        super(NotOptimal, self).__init__(task, self.__name__, run_uuid, message=msg, traceback="status: " + status)


class UnexpectedException(REoptError):
    """
    REopt catch-all exception class

    Attributes:
        message - explanation of the error
    """

    def __init__(self, exc_type, exc_value, exc_traceback):

        self.exc_type = exc_type
        self.exc_value = exc_value
        self.exc_traceback = exc_traceback
