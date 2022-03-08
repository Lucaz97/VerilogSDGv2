

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
      Cond_140150047859328 = 4'h4;
    end else begin
      Cond_140150047859328 = op1;
    end
    Minus_140150047862736 = 4 - op2;
    if(key) begin
      Cond_140150047859664 = Cond_140150047859328;
    end else begin
      Cond_140150047859664 = Minus_140150047862736;
    end
    Plus_140150047913536 = op1 + op1;
    Uand_140150047859952 = &Plus_140150047913536;
    Ulnot_140150047858896 = !Uand_140150047859952;
    Times_140150047860480 = Cond_140150047859664 * Ulnot_140150047858896;
    out = Times_140150047860480;
  end

  wire [3:0] Cond_140150047859328;
  wire [31:0] Minus_140150047862736;
  wire [3:0] Cond_140150047859664;
  wire [7:0] Plus_140150047913536;
  wire [7:0] Uand_140150047859952;
  wire [7:0] Ulnot_140150047858896;
  wire [3:0] Times_140150047860480;

endmodule


