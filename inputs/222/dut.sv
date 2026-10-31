module TopModule (
    input  logic       d,
    input  logic       done_counting,
    input  logic       ack,
    input  logic [9:0] state,
    output logic       B3_next,
    output logic       S_next,
    output logic       S1_next,
    output logic       Count_next,
    output logic       Wait_next,
    output logic       done,
    output logic       counting,
    output logic       shift_ena
);

    localparam logic [9:0] S     = 10'b0000000001;
    localparam logic [9:0] S1    = 10'b0000000010;
    localparam logic [9:0] S11   = 10'b0000000100;
    localparam logic [9:0] S110  = 10'b0000001000;
    localparam logic [9:0] B0    = 10'b0000010000;
    localparam logic [9:0] B1    = 10'b0000100000;
    localparam logic [9:0] B2    = 10'b0001000000;
    localparam logic [9:0] B3    = 10'b0010000000;
    localparam logic [9:0] Count = 10'b0100000000;
    localparam logic [9:0] Wait  = 10'b1000000000;

    logic [9:0] next_state;

    always_comb begin
        next_state = state;

        done = 1'b0;
        counting = 1'b0;
        shift_ena = 1'b0;

        case (state)
            S: begin
                if (d)
                    next_state = S1;
            end
            S1: begin
                if (d)
                    next_state = S11;
                else
                    next_state = S;
            end
            S11: begin
                if (!d)
                    next_state = S110;
            end
            S110: begin
                if (d)
                    next_state = B0;
                else
                    next_state = S;
            end
            B0: begin
                shift_ena = 1'b1;
                next_state = B1;
            end
            B1: begin
                shift_ena = 1'b1;
                next_state = B2;
            end
            B2: begin
                shift_ena = 1'b1;
                next_state = B3;
            end
            B3: begin
                shift_ena = 1'b1;
                next_state = Count;
            end
            Count: begin
                counting = 1'b1;
                if (done_counting)
                    next_state = Wait;
            end
            Wait: begin
                done = 1'b1;
                if (ack)
                    next_state = S;
            end
            default: begin
                next_state = S;
            end
        endcase

        S_next = (next_state == S);
        S1_next = (next_state == S1);
        B3_next = (next_state == B3);
        Count_next = (next_state == Count);
        Wait_next = (next_state == Wait);
    end

endmodule
