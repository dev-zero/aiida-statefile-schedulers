[![Build Status](https://github.com/dev-zero/aiida-statefile-schedulers/workflows/ci/badge.svg?branch=master)](https://github.com/dev-zero/aiida-statefile-schedulers/actions)
[![Coverage Status](https://coveralls.io/repos/github/dev-zero/aiida-statefile-schedulers/badge.svg?branch=master)](https://coveralls.io/github/dev-zero/aiida-statefile-schedulers?branch=master)
[![Docs status](https://readthedocs.org/projects/aiida-statefile-schedulers/badge)](http://aiida-statefile-schedulers.readthedocs.io/)
[![PyPI version](https://badge.fury.io/py/aiida-statefile-schedulers.svg)](https://badge.fury.io/py/aiida-statefile-schedulers)

# aiida-statefile-schedulers

Simple statefile driven task schedulers: Currently AiiDA relies mostly on full fledged task schedulers to run jobs
in complex workflows. Running such workflows with the direct solver often means that many processes run together
even when running the workflow directly (e.g. not by the daemon), overloading a single node.

This scheduler does not run any jobs. Instead, it creates *state files* of the form `$jobid.QUEUED` in the directory
`${AIIDA_STATE_DIR}` (an environment variable you have to set in your `.profile/.bash_profile` of the target machine),
waiting for some script to pick the jobs up and run them.

This **runner script** should create a file `$jobid.DONE` when done. As intermediate steps it can also create a file `$jobid.RUNNING` to
signal AiiDA that it picked up a job. The initial state file contains lines of the form `key=value` with the following keys:

* `cwd`: the working directory for this job
* `cmd`: the command to run there (usually via `bash -e ...`)

The state files can also be renamed instead of created. A sample runner can be found in `scripts/`.

## Features

  ```

## Installation

```shell
pip install aiida-statefile-scheduler
verdi quicksetup  # better to set up a new profile
verdi plugin list aiida.schedulers  # should now show your calculation plugins
```


## Development

```shell
git clone https://github.com/dev-zero/aiida-statefile-schedulers .
cd aiida-statefile-schedulers
pip install -e .[pre-commit,testing]  # install extra dependencies
pre-commit install  # install pre-commit hooks
pytest -v  # discover and run all tests
```

See the [developer guide](http://aiida-statefile-schedulers.readthedocs.io/en/latest/developer_guide/index.html) for more information.

## License

MIT

## Contact

tm@dev-zero.ch
