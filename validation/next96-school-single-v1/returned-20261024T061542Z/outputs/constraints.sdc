###################################################################

# Created by write_sdc on Sat Oct 24 14:15:42 2026

###################################################################
set sdc_version 2.2

set_units -time ns -resistance MOhm -capacitance fF -voltage V -current mA
set_max_delay 10  -from [list [get_ports {in[3]}] [get_ports {in[2]}] [get_ports {in[1]}]       \
[get_ports {in[0]}]]  -to [list [get_ports {out_both[3]}] [get_ports {out_both[2]}] [get_ports      \
{out_both[1]}] [get_ports {out_both[0]}] [get_ports {out_any[3]}] [get_ports   \
{out_any[2]}] [get_ports {out_any[1]}] [get_ports {out_any[0]}] [get_ports     \
{out_different[3]}] [get_ports {out_different[2]}] [get_ports                  \
{out_different[1]}] [get_ports {out_different[0]}]]
