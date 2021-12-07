#!/bin/bash

set -euo pipefail

while true ; do
    qfile=$(command ls -1rt -- *.QUEUED 2>/dev/null | head -1 || true)

    if [ -z "${qfile}" ] ; then
        echo "No *.QUEUED file found in the current directory, waiting (press ctrl+c to terminate)..."
        sleep 5
        continue
    fi

    echo "Found new file: ${qfile}"

    rfile="${qfile/.QUEUED/.RUNNING}"
    dfile="${qfile/.QUEUED/.DONE}"

    mv -v "${qfile}" "${rfile}"
    # use a subshell to isolate it
    (
        set -eux
        # shellcheck source=SCRIPTDIR/sample-statedir/feb1-d203-4542-a49c-ded53dcd38a5.QUEUED
        source "${rfile}"
        cd "${cwd}"
        # shellcheck source=/dev/null
        source "${cmd}"
    ) || true  # ignore the subshells result
    mv -v "${rfile}" "${dfile}"
done
