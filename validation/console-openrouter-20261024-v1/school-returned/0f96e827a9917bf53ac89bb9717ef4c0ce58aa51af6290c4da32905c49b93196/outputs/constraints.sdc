# ####################################################################

#  Created by Genus(TM) Synthesis Solution 21.14-s082_1 on Sat Oct 24 17:14:55 HKT 2026

# ####################################################################

set sdc_version 2.0

set_units -capacitance 1fF
set_units -time 1000ps

# Set the current design
current_design TopModule

set_max_delay 10 -from [list \
  [get_ports {in[3]}]  \
  [get_ports {in[2]}]  \
  [get_ports {in[1]}]  \
  [get_ports {in[0]}] ] -to [list \
  [get_ports {out_both[3]}]  \
  [get_ports {out_both[2]}]  \
  [get_ports {out_both[1]}]  \
  [get_ports {out_both[0]}]  \
  [get_ports {out_any[3]}]  \
  [get_ports {out_any[2]}]  \
  [get_ports {out_any[1]}]  \
  [get_ports {out_any[0]}]  \
  [get_ports {out_different[3]}]  \
  [get_ports {out_different[2]}]  \
  [get_ports {out_different[1]}]  \
  [get_ports {out_different[0]}] ]
set_clock_gating_check -setup 0.0 
set_wire_load_mode "enclosed"
