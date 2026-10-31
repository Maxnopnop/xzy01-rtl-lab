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
        next_state = 10'b0;

        if (state == S)
            next_state = d ? S1 : S;
        else if (state == S1)
            next_state = d ? S11 : S;
        else if (state == S11)
            next_state = d ? S11 : S110;
        else if (state == S110)
            next_state = d ? B0 : S;
        else if (state == B0)
            next_state = B1;
        else if (state == B1)
            next_state = B2;
        else if (state == B2)
            next_state = B3;
        else if (state == B3)
            next_state = Count;
        else if (state == Count)
            next_state = done_counting ? Wait : Count;
        else if (state == Wait)
            next_state = ack ? S : Wait;

        B3_next   = (next_state == B3);
        S_next    = (next_state == S);
        S1_next   = (next_state == S1);
        Count_next = (next_state == Count);
        Wait_next  = (next_state == Wait);

        shift_ena = (state == B0) || (state == B1) ||
                    (state == B2) || (state == B3);
        counting  = (state == Count);
        done      = (state == Wait);
    end

endmodule
