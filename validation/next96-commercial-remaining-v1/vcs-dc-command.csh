#!/bin/tcsh -f
source "/usr/eelocal/synopsys/vcs-vx2025.06-sp1/.cshrc"
if ($status != 0) exit 90
rehash
vcs -ID >& tool_version.log
if ($status != 0) exit 91
vcs -full64 -sverilog +define+TETRAMAX +nospecify +notimingcheck -top tb testbench.sv reference.sv netlist.v -v "/staff/ee/dept/public/course_PDK/nangate/freepdk-45nm/lib/NangateOpenCellLibrary_PDKv1_3_v2010_12/Front_End/Verilog/NangateOpenCellLibrary.v" +incdir+"\staff\ee\dept\public\course_PDK\nangate\freepdk-45nm\lib\NangateOpenCellLibrary_PDKv1_3_v2010_12\Front_End\Verilog" -o simv -l compile.log
set compile_rc = $status
echo $compile_rc > compile.exit
if ($compile_rc != 0) exit $compile_rc
./simv -l simulate.log
set sim_rc = $status
echo $sim_rc > simulate.exit
exit $sim_rc
