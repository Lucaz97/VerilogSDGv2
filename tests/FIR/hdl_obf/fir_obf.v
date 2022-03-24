
module FIR_filter_firBlock_left_1_obf
(
  X,
  clk,
  Y,
  reset,
  K_target
);

  parameter TOT_BITS_K_target = 1;
  parameter WORK_BITS_K_target = 1;
  input [31:0] X;
  input clk;
  output [31:0] Y;
  input reset;
  reg [31:0] Y;
  wire [31:0] Y_in;
  wire [31:0] multProducts [0:10];
  reg [31:0] firStep [0:9];
  input [TOT_BITS_K_target-1:0] K_target;

  FIR_filter_firBlock_left_MultiplyBlock_2_obf
  #(
    .TOT_BITS_K_target(TOT_BITS_K_target),
    .WORK_BITS_K_target(WORK_BITS_K_target)
  )
  my_FIR_filter_firBlock_left_MultiplyBlock
  (
    .X(X),
    .Y1(multProducts[0]),
    .Y2(multProducts[1]),
    .Y3(multProducts[2]),
    .Y4(multProducts[3]),
    .Y5(multProducts[4]),
    .Y6(multProducts[5]),
    .Y7(multProducts[6]),
    .Y8(multProducts[7]),
    .Y9(multProducts[8]),
    .Y10(multProducts[9]),
    .Y11(multProducts[10]),
    .K_target(K_target)
  );


  always @(posedge clk or negedge reset) begin
    if(~reset) begin
      Y <= 32'h00000000;
    end else begin
      Y <= Y_in;
    end
  end


  always @(posedge clk or negedge reset) begin
    if(~reset) begin
      firStep[0] <= 32'h00000000;
      firStep[1] <= 32'h00000000;
      firStep[2] <= 32'h00000000;
      firStep[3] <= 32'h00000000;
      firStep[4] <= 32'h00000000;
      firStep[5] <= 32'h00000000;
      firStep[6] <= 32'h00000000;
      firStep[7] <= 32'h00000000;
      firStep[8] <= 32'h00000000;
      firStep[9] <= 32'h00000000;
    end else begin
      firStep[0] <= multProducts[0];
      firStep[1] <= firStep[0] + multProducts[1];
      firStep[2] <= firStep[1] + multProducts[2];
      firStep[3] <= firStep[2] + multProducts[3];
      firStep[4] <= firStep[3] + multProducts[4];
      firStep[5] <= firStep[4] + multProducts[5];
      firStep[6] <= firStep[5] + multProducts[6];
      firStep[7] <= firStep[6] + multProducts[7];
      firStep[8] <= firStep[7] + multProducts[8];
      firStep[9] <= firStep[8] + multProducts[9];
    end
  end

  assign Y_in = firStep[9] + multProducts[10];

endmodule




module FIR_filter_firBlock_right_MultiplyBlock_4_obf
(
  X,
  Y,
  K_target
);

  parameter TOT_BITS_K_target = 1;
  parameter WORK_BITS_K_target = 1;
  input signed [31:0] X;
  output signed [31:0] Y;
  wire signed [39:0] w1;
  wire signed [39:0] w256;
  wire signed [39:0] w256_;
  input [TOT_BITS_K_target-1:0] K_target;
  assign w1 = X;
  assign w256 = w1 << 8;
  assign w256_ = -1 * w256;
  assign Y = w256_[39:8];

endmodule




module FIR_filter_firBlock_right_3_obf
(
  X,
  clk,
  Y,
  reset,
  K_target
);

  parameter TOT_BITS_K_target = 1;
  parameter WORK_BITS_K_target = 1;
  input [31:0] X;
  input clk;
  output [31:0] Y;
  input reset;
  reg [31:0] Y;
  wire [31:0] Y_in;
  wire [31:0] multProducts;
  input [TOT_BITS_K_target-1:0] K_target;

  FIR_filter_firBlock_right_MultiplyBlock_4_obf
  #(
    .TOT_BITS_K_target(TOT_BITS_K_target),
    .WORK_BITS_K_target(WORK_BITS_K_target)
  )
  my_FIR_filter_firBlock_right_MultiplyBlock
  (
    .X(X),
    .Y(multProducts),
    .K_target(K_target)
  );


  always @(posedge clk or negedge reset) begin
    if(~reset) begin
      Y <= 32'h00000000;
    end else begin
      Y <= Y_in;
    end
  end

  assign Y_in = multProducts;

endmodule




module FIR_filter_0_obf
(
  inData,
  clk,
  outData,
  reset
);

  parameter TOT_BITS_K_target = 0;
  parameter WORK_BITS_K_target = 0;
  input [31:0] inData;
  input clk;
  output [31:0] outData;
  input reset;
  reg [31:0] inData_in;
  reg [31:0] outData;
  wire [31:0] outData_in;
  wire [31:0] leftOut;
  wire [31:0] rightOut;
  wire [1:0] K_target;

  FIR_filter_firBlock_left_1_obf
  #(
    .TOT_BITS_K_target(TOT_BITS_K_target),
    .WORK_BITS_K_target(WORK_BITS_K_target)
  )
  my_FIR_filter_firBlock_left
  (
    .X(inData_in),
    .Y(leftOut),
    .clk(clk),
    .reset(reset),
    .K_target(K_target)
  );


  FIR_filter_firBlock_right_3_obf
  #(
    .TOT_BITS_K_target(TOT_BITS_K_target),
    .WORK_BITS_K_target(WORK_BITS_K_target)
  )
  my_FIR_filter_firBlock_right
  (
    .X(outData_in),
    .Y(rightOut),
    .clk(clk),
    .reset(reset),
    .K_target(K_target)
  );


  always @(posedge clk or negedge reset) begin
    if(~reset) begin
      inData_in <= 32'h00000000;
    end else begin
      inData_in <= inData;
    end
  end


  always @(posedge clk or negedge reset) begin
    if(~reset) begin
      outData <= 32'h00000000;
    end else begin
      outData <= outData_in;
    end
  end

  assign outData_in = leftOut + rightOut;

endmodule




module FIR_filter_firBlock_left_MultiplyBlock_2_obf
(
  X,
  Y1,
  Y2,
  Y3,
  Y4,
  Y5,
  Y6,
  Y7,
  Y8,
  Y9,
  Y10,
  Y11,
  K_target
);

  parameter TOT_BITS_K_target = 1;
  parameter WORK_BITS_K_target = 1;
  input signed [31:0] X;
  output signed [31:0] Y1;
  output signed [31:0] Y2;
  output signed [31:0] Y3;
  output signed [31:0] Y4;
  output signed [31:0] Y5;
  output signed [31:0] Y6;
  output signed [31:0] Y7;
  output signed [31:0] Y8;
  output signed [31:0] Y9;
  output signed [31:0] Y10;
  output signed [31:0] Y11;
  wire [31:0] Y [0:10];
  wire signed [39:0] w1;
  wire signed [39:0] w0;
  wire signed [39:0] w16;
  wire signed [39:0] w17;
  wire signed [39:0] w4;
  wire signed [39:0] w3;
  wire signed [39:0] w8;
  wire signed [39:0] w11;
  wire signed [39:0] w192;
  wire signed [39:0] w191;
  wire signed [39:0] w22;
  wire signed [39:0] w68;
  wire signed [39:0] w136;
  input [TOT_BITS_K_target-1:0] K_target;
  assign Y1 = Y[0];
  assign Y2 = Y[1];
  assign Y3 = Y[2];
  assign Y4 = Y[3];
  assign Y5 = Y[4];
  assign Y6 = Y[5];
  assign Y7 = Y[6];
  assign Y8 = Y[7];
  assign Y9 = Y[8];
  assign Y10 = Y[9];
  assign Y11 = Y[10];
  assign w1 = X;
  assign w0 = 0;
  assign w11 = w3 + w8;
  assign w136 = w17 << 3;
  assign w16 = w1 << 4;
  assign w17 = w1 + w16;
  assign w191 = w192 - w1;
  assign w192 = w3 << 6;
  assign w22 = w11 << 1;
  assign w3 = w4 - w1;
  assign w4 = w1 << 2;
  assign w68 = w17 << 2;
  assign w8 = w1 << 3;
  assign Y[0] = w4[39:8];
  assign Y[1] = w22[39:8];
  assign Y[2] = w68[39:8];
  assign Y[3] = w136[39:8];
  assign Y[4] = w191[39:8];
  assign Y[5] = w191[39:8];
  assign Y[6] = w136[39:8];
  assign Y[7] = w68[39:8];
  assign Y[8] = w22[39:8];
  assign Y[9] = w4[39:8];
  assign Y[10] = w0[39:8];

endmodule



