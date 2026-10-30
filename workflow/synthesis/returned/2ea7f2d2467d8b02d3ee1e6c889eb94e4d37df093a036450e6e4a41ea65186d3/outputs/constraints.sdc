# ####################################################################

#  Created by Genus(TM) Synthesis Solution 21.14-s082_1 on Thu Oct 15 11:12:28 HKT 2026

# ####################################################################

set sdc_version 2.0

set_units -capacitance 1fF
set_units -time 1000ps

# Set the current design
current_design sequence_detector

create_clock -name "clk" -period 10.0 -waveform {0.0 5.0} [get_ports clk]
set_clock_transition 0.1 [get_clocks clk]
set_load -pin_load 5.0 [get_ports sequence_detected]
set_false_path -from [get_ports rst_n]
set_clock_gating_check -setup 0.0 
set_input_delay -clock [get_clocks clk] -add_delay -max 1.0 [get_ports data_in]
set_input_delay -clock [get_clocks clk] -add_delay -min 0.0 [get_ports data_in]
set_output_delay -clock [get_clocks clk] -add_delay -max 1.0 [get_ports sequence_detected]
set_output_delay -clock [get_clocks clk] -add_delay -min 0.0 [get_ports sequence_detected]
set_input_transition 0.1 [get_ports rst_n]
set_input_transition 0.1 [get_ports data_in]
set_wire_load_mode "enclosed"
set_clock_uncertainty -setup 0.1 [get_clocks clk]
set_clock_uncertainty -hold 0.1 [get_clocks clk]
