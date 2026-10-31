# One manually selected design; libraries stay on the school host.
if {[catch {
file mkdir reports outputs WORK
set_db library [list "/staff/ee/dept/public/course_PDK/nangate/freepdk-45nm/lib/NangateOpenCellLibrary_PDKv1_3_v2010_12/Front_End/Liberty/NLDM/NangateOpenCellLibrary_typical.lib"]
read_hdl -sv dut.sv
elaborate TopModule
read_sdc constraints.sdc
check_design -unresolved > reports/check_design.rpt
syn_generic
syn_map
syn_opt
report_area > reports/area.rpt
report_timing > reports/timing.rpt
write_hdl > outputs/netlist.v
write_sdc > outputs/constraints.sdc
foreach artifact {outputs/netlist.v outputs/constraints.sdc reports/area.rpt reports/timing.rpt} {
  if {![file exists $artifact] || [file size $artifact] == 0} {error "Missing output: $artifact"}
}
set receipt [open receipt.txt w]
puts $receipt "XZY01_SYNTH_V1 c6674737cfb2dd881b1169f5c69fbb78 COMPLETE"
close $receipt
} detail]} {puts stderr "XZY01_SYNTH_ERROR: $detail"; exit 2}
exit
