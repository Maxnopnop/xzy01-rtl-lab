module TopModule (
  input  logic cpu_overheated,
  output logic shut_off_computer,
  input  logic arrived,
  input  logic gas_tank_empty,
  output logic keep_driving
);

  always_comb begin
    // Default assignment avoids latches
    shut_off_computer = 1'b0;
    if (cpu_overheated)
      shut_off_computer = 1'b1;
  end

  always_comb begin
    // Default assignment avoids latches
    keep_driving = 1'b0;
    if (~arrived)
      keep_driving = ~gas_tank_empty;
  end

endmodule
