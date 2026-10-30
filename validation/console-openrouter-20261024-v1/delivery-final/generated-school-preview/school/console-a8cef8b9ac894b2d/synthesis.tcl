# One manually selected design; libraries stay on the school host.
if {[catch {
file mkdir reports outputs WORK
set_app_var target_library [list "/OFFLINE_FIXTURE_NOT_A_LIBRARY/library.db"]
set_app_var link_library [concat [list "*"] $target_library]
define_design_lib WORK -path ./WORK
if {![analyze -format sverilog dut.sv]} {error "RTL analyze failed"}
if {![elaborate TopModule]} {error "RTL elaboration failed"}
current_design TopModule
if {![link]} {error "Library/design linking failed"}
source constraints.sdc
redirect reports/check_design.rpt {check_design}
if {![check_design]} {error "check_design failed"}
if {![compile]} {error "compile failed"}
report_area > reports/area.rpt
report_timing -max_paths 10 > reports/timing.rpt
report_constraint -all_violators > reports/constraints.rpt
write -format verilog -hierarchy -output outputs/netlist.v
write_sdc outputs/constraints.sdc
write -format ddc -hierarchy -output outputs/design.ddc
foreach artifact {outputs/netlist.v outputs/constraints.sdc reports/area.rpt reports/timing.rpt} {
  if {![file exists $artifact] || [file size $artifact] == 0} {error "Missing output: $artifact"}
}
set receipt [open receipt.txt w]
puts $receipt "XZY01_SYNTH_V1 756eab7ff99f4bafbfd5f8c42ea7d24b COMPLETE"
close $receipt
} detail]} {puts stderr "XZY01_SYNTH_ERROR: $detail"; exit 2}
exit
