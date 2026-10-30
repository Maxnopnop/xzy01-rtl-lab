#!/bin/tcsh -f
source "/usr/eelocal/cadence/xcelium2303hf/.cshrc"
if ($status != 0) exit 90
rehash
xrun -version >& tool_version.log
if ($status != 0) exit 91
xrun -access +r -sequdp_nba_delay -64bit -sv -nospecify -top tb testbench.sv netlist.v observer.sv -v /staff/ee/dept/public/course_PDK/nangate/freepdk-45nm/lib/NangateOpenCellLibrary_PDKv1_3_v2010_12/Front_End/Verilog/NangateOpenCellLibrary.v +incdir+/staff/ee/dept/public/course_PDK/nangate/freepdk-45nm/lib/NangateOpenCellLibrary_PDKv1_3_v2010_12/Front_End/Verilog +nonce=95155aecb47045128c1943b3804e3d6d -input run.tcl -l xrun.log
set sim_rc = $status
echo $sim_rc > simulate.exit
exit $sim_rc
