#!/bin/tcsh -f
source "/usr/eelocal/cadence/xcelium2303hf/.cshrc"
if ($status != 0) exit 90
rehash
xrun -version >& tool_version.log
xrun -64bit -sv -top tb testbench.sv reference.sv dut.sv -input run.tcl -l simulate.log
set rc = $status
echo $rc > simulate.exit
exit $rc
