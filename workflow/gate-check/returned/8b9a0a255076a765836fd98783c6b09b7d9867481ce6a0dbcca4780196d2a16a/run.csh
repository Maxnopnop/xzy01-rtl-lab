#!/bin/tcsh -f
source "/usr/eelocal/cadence/xcelium2303hf/.cshrc"
if ($status != 0) exit 90
rehash
xrun -version >& tool_version.log
if ($status != 0) exit 91
xrun -64bit -sv -nospecify -top tb testbench.sv netlist.v -v /staff/ee/dept/public/course_PDK/nangate/freepdk-45nm/lib/NangateOpenCellLibrary_PDKv1_3_v2010_12/Front_End/Verilog/NangateOpenCellLibrary.v +incdir+/staff/ee/dept/public/course_PDK/nangate/freepdk-45nm/lib/NangateOpenCellLibrary_PDKv1_3_v2010_12/Front_End/Verilog +nonce=e07fffacd15c44f98b148868058e6016 -input run.tcl -l xrun.log
set sim_rc = $status
echo $sim_rc > simulate.exit
exit $sim_rc
