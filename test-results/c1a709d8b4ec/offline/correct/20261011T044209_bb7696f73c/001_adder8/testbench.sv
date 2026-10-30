`timescale 1ns/1ps
module tb;
  reg [7:0] a, b;
  wire [8:0] sum;
  integer ai, bi;
  reg [8:0] expected;
  adder8 dut(.a(a), .b(b), .sum(sum));

  integer checks = 0;
  integer errors = 0;
  integer fd;
  reg [255:0] nonce;
  task finish_test;
    begin
      if (!$value$plusargs("nonce=%s", nonce)) $fatal(1, "Missing evaluator nonce");
      fd = $fopen("verdict.txt", "w");
      if (fd == 0) $fatal(1, "Cannot write evaluator receipt");
      $fdisplay(fd, "RTL_LAB_V1 %0s checks=%0d errors=%0d", nonce, checks, errors);
      $fclose(fd);
      if (errors != 0) $fatal(1, "Functional mismatches: %0d", errors);
      $display("Evaluator completed %0d checks", checks);
      $finish;
    end
  endtask

  initial begin
    for (ai = 0; ai < 256; ai = ai + 1) begin
      for (bi = 0; bi < 256; bi = bi + 1) begin
        a = ai; b = bi;
        expected = ai + bi;
        #1;
        checks = checks + 1;
        if (sum !== expected) begin
          errors = errors + 1;
          if (errors <= 8) $display("Mismatch a=%0d b=%0d got=%0d want=%0d", a, b, sum, expected);
        end
      end
    end
    finish_test;
  end
endmodule
