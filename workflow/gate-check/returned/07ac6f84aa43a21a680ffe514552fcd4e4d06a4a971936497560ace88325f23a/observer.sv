module gate_observer;
initial begin
$dumpfile("diag.vcd");
$dumpvars(1,tb);
$dumpvars(1,tb.dut);
end
endmodule
bind tb gate_observer gate_observer_inst();
