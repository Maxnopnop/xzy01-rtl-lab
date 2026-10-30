#!/bin/tcsh -f
source "/usr/eelocal/synopsys/vcs-vx2025.06-sp1/.cshrc"
if ($status != 0) exit 90
rehash
vcs -ID >& tool_version.log
vcs -full64 -sverilog -top tb testbench.sv reference.sv dut.sv -o simv -l compile.log
if ($status != 0) exit 92
./simv -l simulate.log
set rc = $status
echo $rc > simulate.exit
exit $rc
