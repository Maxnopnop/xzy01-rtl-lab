module TopModule (
    input  logic cpu_overheated,
    output logic shut_off_computer,
    input  logic arrived,
    input  logic gas_tank_empty,
    output logic keep_driving
);

    // shut_off_computer: Set if cpu_overheated, otherwise clear
    always_comb begin
        shut_off_computer = cpu_overheated;
    end

    // keep_driving: Set if not arrived and not gas_tank_empty, otherwise clear
    always_comb begin
        keep_driving = (~arrived) & (~gas_tank_empty);
    end

endmodule
