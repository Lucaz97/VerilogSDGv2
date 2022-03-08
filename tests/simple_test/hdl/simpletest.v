
module simpletest(
// port declaration
    
        input wire clk, rst,
        input wire [1:0] sel,
        input wire [7:0] in1, in2, // input data
        output reg [7:0] out, // output data
        input wire key
        );
        
        reg [7:0]  op1, op2;
        reg [1:0] sel_r;
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
        always @(*)
        begin
            //p1 = 8;
            //if (sel_r == 2'b00)
            out = (key?((key+3)?4'h4:op1):4 - op2)*!&(op1+op1);
            /*else if (sel_r == 2'b01)
                out = op1-op2;
            else if (sel_r == 2'b10)
                out = op1 + 8'b10101010;
            else if (sel_r == 2'b11)
                out = op2 - 8'b10101010;*/
            //else 
            //    op2 = 8'b00000000;
            //out = op2+2;
        end
        //assign out = op2-op1+ (key?2:5);
        endmodule 
        