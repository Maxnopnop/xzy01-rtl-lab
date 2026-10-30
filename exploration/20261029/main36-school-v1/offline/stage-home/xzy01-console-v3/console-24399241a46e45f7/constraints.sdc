# Engineering smoke only: original specification gives no frequency.
# Clock period 10 library time units, zero external IO delay, no load model.
create_clock -name smoke_clk -period 10.0 [get_ports clk]
set_input_delay 0.0 -clock smoke_clk [get_ports {load data*}]
set_output_delay 0.0 -clock smoke_clk [get_ports {q*}]
