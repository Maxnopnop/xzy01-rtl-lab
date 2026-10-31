# Engineering smoke, NOT specification frequency or signoff. Period 10 library units; zero IO delay, no drive/load model.
create_clock -name smoke_clk -period 10.0 [get_ports clk]
set_input_delay 0.0 -clock smoke_clk [get_ports {areset bump_left bump_right}]
set_output_delay 0.0 -clock smoke_clk [all_outputs]
