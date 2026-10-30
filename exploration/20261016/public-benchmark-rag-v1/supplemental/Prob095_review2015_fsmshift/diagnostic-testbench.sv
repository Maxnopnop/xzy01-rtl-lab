module tb; reg clk=0,reset=0; wire shift_ena; integer errors=0,checks=0;
TopModule dut(.clk(clk),.reset(reset),.shift_ena(shift_ena));
initial begin
#0; clk=0; reset=0; #1;
#3; clk=0; reset=1; #1;
#3; clk=1; reset=1; #1;
checks=checks+1; if(shift_ena !== 1'b1) begin errors=errors+1; $display("EVENT_FAIL index=2"); end
#3; clk=1; reset=0; #1;
checks=checks+1; if(shift_ena !== 1'b1) begin errors=errors+1; $display("EVENT_FAIL index=3"); end
#3; clk=0; reset=0; #1;
checks=checks+1; if(shift_ena !== 1'b1) begin errors=errors+1; $display("EVENT_FAIL index=4"); end
#3; clk=1; reset=0; #1;
checks=checks+1; if(shift_ena !== 1'b1) begin errors=errors+1; $display("EVENT_FAIL index=5"); end
#3; clk=0; reset=0; #1;
checks=checks+1; if(shift_ena !== 1'b1) begin errors=errors+1; $display("EVENT_FAIL index=6"); end
#3; clk=1; reset=0; #1;
checks=checks+1; if(shift_ena !== 1'b1) begin errors=errors+1; $display("EVENT_FAIL index=7"); end
#3; clk=0; reset=0; #1;
checks=checks+1; if(shift_ena !== 1'b1) begin errors=errors+1; $display("EVENT_FAIL index=8"); end
#3; clk=1; reset=0; #1;
checks=checks+1; if(shift_ena !== 1'b1) begin errors=errors+1; $display("EVENT_FAIL index=9"); end
#3; clk=0; reset=0; #1;
checks=checks+1; if(shift_ena !== 1'b1) begin errors=errors+1; $display("EVENT_FAIL index=10"); end
#3; clk=1; reset=0; #1;
checks=checks+1; if(shift_ena !== 1'b0) begin errors=errors+1; $display("EVENT_FAIL index=11"); end
#3; clk=1; reset=1; #1;
checks=checks+1; if(shift_ena !== 1'b0) begin errors=errors+1; $display("EVENT_FAIL index=12"); end
#3; clk=1; reset=0; #1;
checks=checks+1; if(shift_ena !== 1'b0) begin errors=errors+1; $display("EVENT_FAIL index=13"); end
#3; clk=0; reset=0; #1;
checks=checks+1; if(shift_ena !== 1'b0) begin errors=errors+1; $display("EVENT_FAIL index=14"); end
#3; clk=1; reset=0; #1;
checks=checks+1; if(shift_ena !== 1'b0) begin errors=errors+1; $display("EVENT_FAIL index=15"); end
#3; clk=0; reset=1; #1;
checks=checks+1; if(shift_ena !== 1'b0) begin errors=errors+1; $display("EVENT_FAIL index=16"); end
#3; clk=1; reset=1; #1;
checks=checks+1; if(shift_ena !== 1'b1) begin errors=errors+1; $display("EVENT_FAIL index=17"); end
#3; clk=0; reset=1; #1;
checks=checks+1; if(shift_ena !== 1'b1) begin errors=errors+1; $display("EVENT_FAIL index=18"); end
#3; clk=1; reset=1; #1;
checks=checks+1; if(shift_ena !== 1'b1) begin errors=errors+1; $display("EVENT_FAIL index=19"); end
#3; clk=1; reset=0; #1;
checks=checks+1; if(shift_ena !== 1'b1) begin errors=errors+1; $display("EVENT_FAIL index=20"); end
#3; clk=0; reset=0; #1;
checks=checks+1; if(shift_ena !== 1'b1) begin errors=errors+1; $display("EVENT_FAIL index=21"); end
#3; clk=1; reset=0; #1;
checks=checks+1; if(shift_ena !== 1'b1) begin errors=errors+1; $display("EVENT_FAIL index=22"); end
#3; clk=0; reset=0; #1;
checks=checks+1; if(shift_ena !== 1'b1) begin errors=errors+1; $display("EVENT_FAIL index=23"); end
#3; clk=1; reset=0; #1;
checks=checks+1; if(shift_ena !== 1'b1) begin errors=errors+1; $display("EVENT_FAIL index=24"); end
#3; clk=0; reset=0; #1;
checks=checks+1; if(shift_ena !== 1'b1) begin errors=errors+1; $display("EVENT_FAIL index=25"); end
#3; clk=1; reset=0; #1;
checks=checks+1; if(shift_ena !== 1'b1) begin errors=errors+1; $display("EVENT_FAIL index=26"); end
#3; clk=0; reset=0; #1;
checks=checks+1; if(shift_ena !== 1'b1) begin errors=errors+1; $display("EVENT_FAIL index=27"); end
#3; clk=1; reset=0; #1;
checks=checks+1; if(shift_ena !== 1'b0) begin errors=errors+1; $display("EVENT_FAIL index=28"); end
#3; clk=0; reset=0; #1;
checks=checks+1; if(shift_ena !== 1'b0) begin errors=errors+1; $display("EVENT_FAIL index=29"); end
#3; clk=1; reset=0; #1;
checks=checks+1; if(shift_ena !== 1'b0) begin errors=errors+1; $display("EVENT_FAIL index=30"); end
$display("PUBLIC_DIAGNOSTIC checks=%0d errors=%0d",checks,errors); $finish; end endmodule
