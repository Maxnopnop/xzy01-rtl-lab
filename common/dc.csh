#!/bin/tcsh -f
source "/usr/eelocal/synopsys/syn-vx2025.06-sp2/.cshrc"
if ($status != 0) exit 90
rehash
which dc_shell > tool_path.txt
if ($status != 0) exit 91
dc_shell -version >& tool_version.log
dc_shell -f synthesis.tcl
set rc = $status
echo $rc > simulate.exit
exit $rc
