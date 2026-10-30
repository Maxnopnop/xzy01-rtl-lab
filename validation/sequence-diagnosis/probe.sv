module probe;
reg clk=0,rst_n=1,data_in=0; wire sequence_detected;
sequence_detector dut(.*);
task step(input b); begin data_in=b; #2; clk=1; #2; clk=0; #2; end endtask
initial begin
#1; rst_n=0; #2; rst_n=1;
step(1);step(0);step(0);step(1);$display("input=1001 expected=1 observed=%b",sequence_detected);
rst_n=0;#2;rst_n=1;
step(1);step(0);step(1);step(1);$display("input=1011 expected=0 observed=%b",sequence_detected);
$finish;
end
endmodule
