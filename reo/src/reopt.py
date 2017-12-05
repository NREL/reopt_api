from __future__ import absolute_import, unicode_literals
import os
import subprocess32 as sp
from shlex import split
from reo.log_levels import log
from celery import shared_task, Task
from reo.models import ModelManager


class REopt(Task):

    name = 'reopt'
    max_retries = 0

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """
        log a bunch of stuff for debugging
        save message: error and outputs: Scenario: status
        need to stop rest of chain!?
        :param exc: The exception raised by the task.
        :param task_id: Unique id of the failed task. (not the run_uuid)
        :param args: Original arguments for the task that failed.
        :param kwargs: Original keyword arguments for the task that failed.
        :param einfo: ExceptionInfo instance, containing the traceback.

        :return: None, The return value of this handler is ignored.
        """
        data = kwargs['data']
        data["messages"]["errors"] = einfo
        data["outputs"]["Scenario"]["status"] = \
            "Error caught in REopt: {}".format(exc)
        ModelManager.update_scenario_and_messages(data, run_uuid=data['outputs']['Scenario']['run_uuid'])
    

def create_run_command(output_path, paths, xpress_model, DATs, cmd_line_args, bau_string, cmd_file):

    log("DEBUG", "Current Directory: " + os.getcwd())

    # RE case
    header = 'exec '
    xpress_model_path = os.path.join(paths['xpress'], xpress_model)

    # Command line constants and Dat file overrides
    outline = ''

    for constant in cmd_line_args:
        outline = ' '.join([outline, constant.strip('\n')])

    for dat_file in DATs:
        if dat_file is not None:
            outline = ' '.join([outline, dat_file.strip('\n')])

    outline.replace('\n', '')

    cmd = r"mosel %s '%s' %s OutputDir='%s' ScenarioPath='%s' BaseString='%s'" \
             % (header, xpress_model_path, outline, output_path, paths['inputs'], bau_string)

    log("DEBUG", "Returning Process Command " + cmd)

    # write a cmd file for easy debugging
    with open(cmd_file, 'w') as f:
        f.write(cmd)

    return cmd


@shared_task(bind=True, base=REopt)
def reopt(self, dfm, paths, data, bau=False):

    self.data = data

    timeout = data['inputs']['Scenario']['timeout_seconds']
    xpress_model = "REopt_API.mos"

    file_cmd = os.path.join(paths['inputs'], "cmd.log")
    file_cmd_bau = os.path.join(paths['inputs'], "cmd_bau.log")

    if bau:
        output_path = paths['outputs_bau']
        run_command = create_run_command(output_path, paths, xpress_model, dfm['DAT_bau'],
                                         dfm['command_line_args_bau'], bau_string='Base',
                                         cmd_file=file_cmd_bau)
    else:
        output_path = paths['outputs']
        run_command = create_run_command(output_path, paths, xpress_model, dfm['DAT'],
                                         dfm['command_line_args'], bau_string='', cmd_file=file_cmd)

    log("INFO", "Running REopt")

    try:
        status = sp.check_output(split(run_command), stderr=sp.STDOUT, timeout=timeout)  # fails if returncode != 0

    except sp.CalledProcessError as e:
        msg = "REopt failed to start. Error code {}.\n{}".format(e.returncode, e.output)
        log("ERROR", msg)
        raise RuntimeError('REopt', msg)

    except sp.TimeoutExpired:
        raise RuntimeError('REopt', "Optimization exceeded timeout: {} seconds, please email reopt@nrel.gov \
                                     for support".format(timeout))
    log("INFO", "REopt run successfully. Status {}".format(status))

    if status.strip() != 'optimal':
        raise RuntimeError('REopt', "Could not find an optimal solution for these inputs.")
