#!/bin/tcsh -f
source "/usr/eelocal/cadence/xcelium2303hf/.cshrc"
if ($status != 0) exit 90
rehash
xrun -version >& tool_version.log
if ($status != 0) exit 91
xrun -64bit -sv -top tb testbench.sv reference.sv dut.sv -input run.tcl -l xrun.log
set sim_rc = $status
echo $sim_rc > simulate.exit
exit $sim_rc
