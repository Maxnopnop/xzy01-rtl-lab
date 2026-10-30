#!/bin/tcsh -f
# Run ONE case on the logged-in ECE VDI host. No scheduler or SSH required.
cd "$0:h"
rm -f verdict.txt compile.exit simulate.exit
if (! $?XCELIUM_SETUP) setenv XCELIUM_SETUP /usr/eelocal/cadence/xcelium2303hf/.cshrc
source "$XCELIUM_SETUP"
if ($status != 0) exit 2
rehash
xrun -version >& tool_version.log
xrun -64bit -sv -top tb testbench.sv dut.sv +nonce=6dba1ca0b95543b5b8d78a3300b5e880 -input run.tcl -l xrun.log
set sim_rc = $status
echo $sim_rc > simulate.exit
exit $sim_rc
