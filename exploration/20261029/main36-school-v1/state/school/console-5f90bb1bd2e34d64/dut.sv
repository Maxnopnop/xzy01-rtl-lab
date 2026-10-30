module TopModule (
  input  mode,
  input  too_cold,
  input  too_hot,
  input  fan_on,
  output logic heater,
  output logic aircon,
  output logic fan
);

  always_comb begin
    if (mode) begin // Heating mode
      heater = too_cold;
      aircon = 1'b0;
    end else begin // Cooling mode
      heater = 1'b0;
      aircon = too_hot;
    end
    fan = fan_on | heater | aircon;
  end

endmodule
