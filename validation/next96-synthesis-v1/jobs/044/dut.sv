module TopModule (
    input  logic       in,
    input  logic [9:0] state,
    output logic [9:0] next_state,
    output logic       out1,
    output logic       out2
);

    always_comb begin
        next_state = 10'b0;

        if (!in) begin
            next_state[0] = state[0] | state[1] | state[2] | state[3] |
                             state[4] | state[7] | state[8] | state[9];
            next_state[8] = state[5];
            next_state[9] = state[6];
        end else begin
            next_state[1] = state[0] | state[8] | state[9];
            next_state[2] = state[1];
            next_state[3] = state[2];
            next_state[4] = state[3];
            next_state[5] = state[4];
            next_state[6] = state[5];
            next_state[7] = state[6] | state[7];
        end

        out1 = state[8] | state[9];
        out2 = state[7] | state[9];
    end

endmodule
