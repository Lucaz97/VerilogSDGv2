
module simpletest(
// port declaration
    
        input wire clk, rst,
        input wire [1:0] sel,
        input wire [7:0] op1, op2, // input data
        output  [7:0]out, out1, // output data
        input wire key,
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
  Y11
        );
        reg [1:0] sel_r;
        wire [7:0] Y [0:10];
          output signed  [31:0]
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
    Y11;
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
        /*always @(posedge clk)
        begin
            if (rst)
            begin
                op1 <= 8'b00000000;
                sel_r <= 2'b00;
                op2 <= 8'b00000000;
            end
            else
            begin
                op1 <= in1;
                op2 <= in2;
                sel_r <= sel;
            end
        end*/
        //always @(*)
        //begin
            //p1 = 8;
            //if (sel_r == 2'b00)
          //  out = (key?((key+3)?4'h4:op1):4 - op2)*!&(op1+op1);
            /*else if (sel_r == 2'b01)
                out = op1-op2;
            else if (sel_r == 2'b10)
                out = op1 + 8'b10101010;
            else if (sel_r == 2'b11)
                out = op2 - 8'b10101010;*/
            //else 
            //    op2 = 8'b00000000;
            //out = op2+2;
        //end
        assign Y[0] = op1+op2-3;
        assign out = Y[0];        
endmodule 
        