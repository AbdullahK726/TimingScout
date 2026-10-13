// top.sv
// Small demo datapath for generating a real Vivado timing report.
// Two 8-bit input registers feed a chain of combinational logic
// (adder, comparator, and a mux) before landing in an output register.
// This creates a real combinational path between two flip-flops so
// report_timing_summary has something meaningful to report on.

module top (
    input  logic       clk,
    input  logic       rst,
    input  logic [7:0] a_in,
    input  logic [7:0] b_in,
    input  logic       sel_in,
    output logic [7:0] result_out
);

    logic [7:0] a_reg;
    logic [7:0] b_reg;
    logic       sel_reg;

    // Input registers
    always_ff @(posedge clk) begin
        if (rst) begin
            a_reg   <= 8'd0;
            b_reg   <= 8'd0;
            sel_reg <= 1'b0;
        end else begin
            a_reg   <= a_in;
            b_reg   <= b_in;
            sel_reg <= sel_in;
        end
    end

    // Combinational datapath: adder, comparator, and a mux chain.
    // This is the logic that typically shows up as the critical path.
    logic [7:0] sum_value;
    logic       a_greater_than_b;
    logic [7:0] mux_stage_1;
    logic [7:0] mux_stage_2;

    assign sum_value       = a_reg + b_reg;
    assign a_greater_than_b = (a_reg > b_reg);
    assign mux_stage_1     = a_greater_than_b ? sum_value : b_reg;
    assign mux_stage_2     = sel_reg ? mux_stage_1 : a_reg;

    // Output register
    always_ff @(posedge clk) begin
        if (rst) begin
            result_out <= 8'd0;
        end else begin
            result_out <= mux_stage_2;
        end
    end

endmodule
