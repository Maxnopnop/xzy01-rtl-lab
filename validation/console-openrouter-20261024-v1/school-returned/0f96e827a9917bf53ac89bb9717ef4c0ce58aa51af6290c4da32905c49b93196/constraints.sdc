# Combinational smoke constraint, no clock/reset ports.
# 10 library time units input-to-output, provisional engineering target.
# No external input delay, transition, output load or PPA claim.
set_max_delay 10.0 -from [all_inputs] -to [all_outputs]
