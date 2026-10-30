#!/bin/tcsh -f
source "/usr/eelocal/cadence/xcelium2303hf/.cshrc"
if ($status != 0) exit 90
rehash
xrun -version >& tool_version.log
if ($status != 0) exit 91
xrun -access +r +define+TETRAMAX -64bit -sv -nospecify -top tb testbench.sv netlist.v observer.sv -v /staff/ee/dept/public/course_PDK/nangate/freepdk-45nm/lib/NangateOpenCellLibrary_PDKv1_3_v2010_12/Front_End/Verilog/NangateOpenCellLibrary.v +incdir+/staff/ee/dept/public/course_PDK/nangate/freepdk-45nm/lib/NangateOpenCellLibrary_PDKv1_3_v2010_12/Front_End/Verilog +nonce=724a807172574606943b923b9f8f0208 -input run.tcl -l xrun.log
set sim_rc = $status
echo $sim_rc > simulate.exit
exit $sim_rc
