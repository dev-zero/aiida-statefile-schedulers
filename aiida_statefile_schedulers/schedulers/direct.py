# -*- coding: utf-8 -*-
"""
Plugin for direct execution via statefiles.
"""

from aiida.schedulers import Scheduler, SchedulerError
from aiida.schedulers.plugins.direct import DirectScheduler, DirectJobResource
from aiida.schedulers.datastructures import JobInfo, JobState

_MAP_STATUS = {  # the order of the states are important
    'UNDETERMINED': JobState.UNDETERMINED,
    'QUEUED_HELD': JobState.QUEUED_HELD,
    'QUEUED': JobState.QUEUED,
    'RUNNING': JobState.RUNNING,
    'DONE': JobState.DONE,
}

class StatefileDirectScheduler(DirectScheduler):
    """
    Support for the direct execution bypassing schedulers.
    """
    _logger = Scheduler._logger.getChild('directstatefile')  # pylint: disable=W0212

    # Query only by list of jobs and not by user
    _features = {
        'can_query_by_user': True,
    }

    _job_resource_class = DirectJobResource

    def _get_joblist_command(self, jobs=None, user=None):
        """
        The command to report full information on existing jobs.
        """

        if jobs and not isinstance(jobs, (str, tuple, list)):
            raise TypeError(
                "If provided, the 'jobs' variable must be a string or a list/tuple of strings"
            )

        command = [
            'export LC_ALL=C;',  # avoid localization effects
            'set -eu;',  # make errors fatal and abort at undefined variables
            'cd "${AIIDA_STATEFILE_DIR}";',
            'command ls -1',  # ensure we're calling POSIX ls, not some alias
        ]

        if jobs:
            joblist = [jobs] if isinstance(jobs, str) else jobs
            command += [
                f'{job}.{state}' for job in joblist for state in _MAP_STATUS
            ]

        return ' '.join(command)

    def _parse_joblist_output(self, retval, stdout, stderr):
        """
        Parse the queue output string, as returned by executing the
        command returned by _get_joblist_command command.

        Return a list of JobInfo objects, one of each job,
        each relevant parameters implemented.
        """

        if retval and any(
                msg in stderr
                for msg in ('unbound variable', 'parameter not set')):
            raise SchedulerError(
                'This scheduler requires the AIIDA_STATEFILE_DIR environment variable set on the target computer'
            )

        def map_status(state: str):
            try:
                return _MAP_STATUS[state]
            except KeyError:
                return JobState.UNDETERMINED

        def state_idx(job_state: JobState):
            return list(_MAP_STATUS.values()).index(job_state)

        def create_job(jobid: str, job_state: JobState):
            job = JobInfo()
            job.job_id = jobid
            job.job_state = job_state
            return job

        jobs = {}
        for line in stdout.split('\n'):
            if not line:  # ignore empty
                continue

            # we get full path names
            jobid, statestr = line.split('.')

            if statestr == 'KILL':
                # ignore the KILL request "state"
                self.logger.info(
                    f'ignoring the KILL pseudo-state file for: {jobid}')
                continue

            state = map_status(statestr)

            if jobid not in jobs:
                jobs[jobid] = create_job(jobid, state)
            else:
                if state_idx(state) > state_idx(jobs[jobid].job_state):
                    jobs[jobid].job_state = state  # "upgrade" the state

        for line in stderr.split('\n'):
            if not line:  # ignore empty
                continue

            cmd, path, errmsg = line.split(':')

            if cmd == 'cd':
                raise SchedulerError(
                    f'Error while accessing the AIIDA_STATEFILE_DIR at {path}: {errmsg}'
                )

            jobid, statestr = path.split('.')

            if jobid in jobs:
                # we found a state, but one of the other states is not present, this is expected
                continue

            # only when we get an error but no statefile at all we have to add an entry
            jobs[jobid] = create_job(jobid, JobState.UNDETERMINED)

        return list(jobs.values())

    def _get_submit_command(self, submit_script):
        """
        Return the string to execute to submit a given script.

        .. note:: One needs to redirect stdout and stderr to /dev/null
           otherwise the daemon remains hanging for the script to run

        :param submit_script: the path of the submit script relative to the working
            directory.
            IMPORTANT: submit_script should be already escaped.
        """

        # this runs in the calculation directory, using the pwd as jobid assumed to be safe
        submit_command = (
            f'export LC_ALL=C;'
            f'set -eu;'
            f'jobid=$(basename $(pwd));'
            f'echo -e "cwd=\'$(pwd)\'\\ncmd={submit_script}" > "${{AIIDA_STATEFILE_DIR}}/${{jobid}}.QUEUED";'
            f'echo ${{jobid}}')

        self.logger.info(f'submitting with: {submit_command}')

        return submit_command

    def _parse_submit_output(self, retval, stdout, stderr):
        """
        Parse the output of the submit command, as returned by executing the
        command returned by _get_submit_command command.

        Return a string with the JobID.
        """

        if retval:
            if any(msg in stderr
                   for msg in ('unbound variable', 'parameter not set')):
                raise SchedulerError(
                    'This scheduler requires the AIIDA_STATEFILE_DIR environment variable set on the target computer'
                )
            raise SchedulerError(
                f'Creating the QUEUED statefile failed: {stderr}')

        return stdout.strip()

    def _get_kill_command(self, jobid):
        """
        Return the command to kill the job with specified jobid.
        """
        kill_command = (f'export LC_ALL=C;'
                        f'set -eu;'
                        f'touch "${{AIIDA_STATEFILE_DIR}}/{jobid}.KILL"')

        self.logger.info(f'killing job {jobid}')

        return kill_command

    def _parse_kill_output(self, retval, stdout, stderr):
        """
        Parse the output of the kill command.

        :return: True if everything seems ok, False otherwise.
        """
        if retval != 0:
            self.logger.error(
                f'Error in _parse_kill_output: retval={retval}; stdout={stdout}; stderr={stderr}'
            )
            return False

        if stderr.strip():
            self.logger.warning(
                f'in _parse_kill_output for {str(self.transport)}: there was some text in stderr: {stderr}'
            )

        if stdout.strip():
            self.logger.warning(
                f'in _parse_kill_output for {str(self.transport)}: there was some text in stdout: {stdout}'
            )

        return True
