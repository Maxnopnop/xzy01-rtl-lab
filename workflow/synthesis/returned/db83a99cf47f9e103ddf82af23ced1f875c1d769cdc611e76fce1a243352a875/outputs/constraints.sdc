###################################################################

# Created by write_sdc on Thu Oct 15 11:00:16 2026

###################################################################
set sdc_version 2.2

set_units -time ns -resistance MOhm -capacitance fF -voltage V -current mA
set_load -pin_load 5 [get_ports sequence_detected]
create_clock [get_ports clk]  -period 10  -waveform {0 5}
set_clock_uncertainty 0.1  [get_clocks clk]
set_clock_transition -max -rise 0.1 [get_clocks clk]
set_clock_transition -max -fall 0.1 [get_clocks clk]
set_clock_transition -min -rise 0.1 [get_clocks clk]
set_clock_transition -min -fall 0.1 [get_clocks clk]
set_input_delay -clock clk  -max 1  [get_ports data_in]
set_input_delay -clock clk  -min 0  [get_ports data_in]
set_output_delay -clock clk  -max 1  [get_ports sequence_detected]
set_output_delay -clock clk  -min 0  [get_ports sequence_detected]
set_input_transition -max 0.1  [get_ports rst_n]
set_input_transition -min 0.1  [get_ports rst_n]
set_input_transition -max 0.1  [get_ports data_in]
set_input_transition -min 0.1  [get_ports data_in]
set_false_path   -from [get_ports rst_n]
