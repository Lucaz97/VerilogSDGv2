
module simpletest(
// port declaration
    
        input wire clk, rst,
        input wire [1:0] sel,
        input wire [7:0] in1, in2, // input data
        output reg [7:0] out // output data
        );
        
        reg [7:0]  op1, op2;
        reg [1:0] sel_r;
        always @(posedge clk)
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
        end
        always @(*)
        begin
            if (sel_r == 2'b00)
                out = op1+op2;
            else if (sel_r == 2'b01)
                out = op1-op2;
            else if (sel_r == 2'b10)
                out = op1 + 8'b10101010;
            else if (sel_r == 2'b11)
                out = op2 - 8'b10101010;
            else 
                out = 8'b00000000;
        end
        endmodule 
        