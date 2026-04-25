// axi4_lite_mem_vip.sv
// Simple memory VIP that acts as a slave to store and read data

`timescale 1ns/1ps

module axi4_lite_mem_vip (
    input  logic         aclk,
    input  logic         aresetn,
    input  logic [15:0]  awaddr,
    input  logic [2:0]   awprot,
    input  logic         awvalid,
    output logic         awready,
    input  logic [31:0]  wdata,
    input  logic [3:0]   wstrb,
    input  logic         wvalid,
    output logic         wready,
    output logic [1:0]   bresp,
    output logic         bvalid,
    input  logic         bready,
    input  logic [15:0]  araddr,
    input  logic [2:0]   arprot,
    input  logic         arvalid,
    output logic         arready,
    output logic [31:0]  rdata,
    output logic [1:0]   rresp,
    output logic         rvalid,
    input  logic         rready
);

    // Internal memory - 256 entries x 32 bits = 8KB
    logic [31:0] mem [0:255];

    // Write address channel
    always_ff @(posedge aclk or negedge aresetn) begin
        if (!aresetn) begin
            awready <= 1'b0;
        end else begin
            awready <= awvalid;
        end
    end

    // Write data channel
    always_ff @(posedge aclk or negedge aresetn) begin
        if (!aresetn) begin
            wready <= 1'b0;
        end else begin
            wready <= wvalid;
        end
    end

    // Write operation with byte enables
    always_ff @(posedge aclk or negedge aresetn) begin
        if (!aresetn) begin
            for (int i = 0; i < 256; i++) begin
                mem[i] <= '0;
            end
        end else if (awvalid && awready && wvalid && wready) begin
            for (int byte_idx = 0; byte_idx < 4; byte_idx++) begin
                if (wstrb[byte_idx]) begin
                    mem[awaddr[7:0]][8*byte_idx +: 8] <= wdata[8*byte_idx +: 8];
                end
            end
        end
    end

    // Write response channel
    always_ff @(posedge aclk or negedge aresetn) begin
        if (!aresetn) begin
            bvalid <= 1'b0;
            bresp <= 2'b00;
        end else begin
            if (awvalid && awready && wvalid && wready) begin
                bvalid <= 1'b1;
                bresp <= 2'b00;
            end else if (bready && bvalid) begin
                bvalid <= 1'b0;
            end
        end
    end

    // Read address channel
    always_ff @(posedge aclk or negedge aresetn) begin
        if (!aresetn) begin
            arready <= 1'b0;
        end else begin
            arready <= arvalid;
        end
    end

    // Read data channel
    always_ff @(posedge aclk or negedge aresetn) begin
        if (!aresetn) begin
            rvalid <= 1'b0;
            rdata <= 32'b0;
            rresp <= 2'b00;
        end else begin
            if (arvalid && arready) begin
                rdata <= mem[araddr[7:0]];
                rresp <= 2'b00;
                rvalid <= 1'b1;
            end else if (rready && rvalid) begin
                rvalid <= 1'b0;
            end
        end
    end

endmodule
