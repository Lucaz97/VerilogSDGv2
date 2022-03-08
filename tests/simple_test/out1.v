

module simpletest
(
  input wire clk,
  input rst,
  input wire [1:0] sel,
  input wire [7:0] in1,
  input [7:0] in2,
  output reg [7:0] out,
  input wire key
);

  reg [7:0] op1;reg [7:0] op2;
  reg [1:0] sel_r;

  always @(posedge clk) begin
    if(rst) begin
      op1 <= 8'b00000000;
      sel_r <= 2'b00;
      op2 <= 8'b00000000;
    end else begin
      op1 <= in1;
      op2 <= in2;
      sel_r <= sel;
    end
  end


  always @(*) begin
    if(sel_r == 2'b00) begin
      out = (op1 - op2) * (op1 + op1);
    end else begin
      out = 8'b00000000;
    end
  end


endmodule


