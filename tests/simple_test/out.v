

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

  always @(*) begin
    if(key + 3) begin
      Cond_140523358814800 = 4'h4;
    end else begin
      Cond_140523358814800 = op1;
    end
    Minus_140523358876000 = 4 - op2;
    if(key) begin
      Cond_140523358815136 = Cond_140523358814800;
    end else begin
      Cond_140523358815136 = Minus_140523358876000;
    end
    Xor_140523358817488 = op1 ^ op2;
    Uand_140523358815040 = &Xor_140523358817488;
    Times_140523358816528 = Cond_140523358815136 * Uand_140523358815040;
    out = Times_140523358816528;
  end

  wire [3:0] Cond_140523358814800;
  wire [31:0] Minus_140523358876000;
  wire [3:0] Cond_140523358815136;
  wire [7:0] Xor_140523358817488;
  wire [7:0] Uand_140523358815040;
  wire [3:0] Times_140523358816528;

endmodule


