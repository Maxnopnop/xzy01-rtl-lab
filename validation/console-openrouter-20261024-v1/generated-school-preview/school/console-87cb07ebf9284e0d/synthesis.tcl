# One manually selected design; libraries stay on the school host.
if {[catch {
file mkdir reports outputs WORK
set_db library [list "/OFFLINE_FIXTURE_NOT_A_LIBRARY/library.lib"]
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
puts $receipt "XZY01_SYNTH_V1 247020f54fd54f8bb9a7d8d4a8745139 COMPLETE"
close $receipt
} detail]} {puts stderr "XZY01_SYNTH_ERROR: $detail"; exit 2}
exit
