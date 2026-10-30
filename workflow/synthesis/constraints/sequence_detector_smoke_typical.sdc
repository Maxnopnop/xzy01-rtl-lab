# Smoke-test assumptions, not a measured performance target or signoff.
# Bound to paired-a32/m01__real_overlap__s001__control sequence_detector.
# Expected library units: ns and fF (Liberty metadata supplied by user).
# 100 MHz clock; ideal pre-layout clock, 0.1 ns uncertainty/transition.
create_clock -name clk -period 10.0 [get_ports clk]
set_clock_uncertainty 0.1 [get_clocks clk]
set_clock_transition 0.1 [get_clocks clk]
set_input_delay -clock [get_clocks clk] -max 1.0 [get_ports data_in]
set_input_delay -clock [get_clocks clk] -min 0.0 [get_ports data_in]
set_input_transition 0.1 [get_ports {data_in rst_n}]
set_output_delay -clock [get_clocks clk] -max 1.0 [get_ports sequence_detected]
set_output_delay -clock [get_clocks clk] -min 0.0 [get_ports sequence_detected]
set_load 5.0 [get_ports sequence_detected]
# Async reset excluded ONLY for this flow smoke test. Recovery/removal and
# reset-release safety are NOT covered; do not reuse as signoff constraints.
set_false_path -from [get_ports rst_n]
