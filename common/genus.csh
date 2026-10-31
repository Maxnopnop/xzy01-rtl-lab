#!/bin/tcsh -f
source "/usr/eelocal/cadence/genus211/.cshrc"
if ($status != 0) exit 90
rehash
which genus > tool_path.txt
if ($status != 0) exit 91
genus -version >& tool_version.log
genus -no_gui -abort_on_error -files synthesis.tcl
set rc = $status
echo $rc > simulate.exit
exit $rc
