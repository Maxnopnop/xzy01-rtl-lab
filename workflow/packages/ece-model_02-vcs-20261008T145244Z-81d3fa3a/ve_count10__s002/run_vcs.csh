#!/bin/tcsh -f
# Run ONE case on the logged-in ECE VDI host. No scheduler or SSH required.
cd "$0:h"
rm -f verdict.txt compile.exit simulate.exit
if (! $?VCS_SETUP) setenv VCS_SETUP /usr/eelocal/synopsys/vcs-vx2025.06-sp1/.cshrc
source "$VCS_SETUP"
if ($status != 0) exit 2
rehash
vcs -ID >& tool_version.log
# Read the harness timescale before modules without an explicit directive.
vcs -full64 -sverilog -top tb testbench.sv dut.sv -o simv -l compile.log
set compile_rc = $status
echo $compile_rc > compile.exit
if ($compile_rc != 0) exit $compile_rc
./simv +nonce=f25776f3c7404d80b9bd628a30c38e4f -l simulate.log
set sim_rc = $status
echo $sim_rc > simulate.exit
exit $sim_rc
