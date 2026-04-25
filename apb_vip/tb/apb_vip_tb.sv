`timescale 1ns/1ps

`include "vunit_defines.svh"
`include "apb_master_vip.sv"
`include "apb_slave_vip.sv"

module apb_vip_tb;

  import vunit_pkg::*;

  localparam int ADDR_WIDTH = 16;
  localparam int DATA_WIDTH = 32;
  localparam int STRB_WIDTH = DATA_WIDTH / 8;
  localparam int PROT_WIDTH = 3;
  localparam int STIMULUS_COUNT = 48;
  localparam time INTER_TRANSACTION_PAUSE = 1us;

  logic clk;
  logic rstn;

  apb_if #(ADDR_WIDTH, DATA_WIDTH, STRB_WIDTH, PROT_WIDTH) apb_link(clk, rstn);

  ApbMasterVIP #(ADDR_WIDTH, DATA_WIDTH, STRB_WIDTH, PROT_WIDTH) master_vip;
  ApbSlaveVIP  #(ADDR_WIDTH, DATA_WIDTH, STRB_WIDTH, PROT_WIDTH) slave_vip;

  function automatic logic [ADDR_WIDTH-1:0] build_addr(input int unsigned index);
    return ADDR_WIDTH'(16'h1000 + (index * STRB_WIDTH));
  endfunction

  function automatic logic [DATA_WIDTH-1:0] build_data(input int unsigned index);
    return DATA_WIDTH'(32'hCAFE_0000 ^ (index * 32'h0101_0011));
  endfunction

  function automatic logic [STRB_WIDTH-1:0] build_strb(input int unsigned index);
    logic [STRB_WIDTH-1:0] strb;
    begin
      strb = '0;
      for (int byte_idx = 0; byte_idx <= (index % STRB_WIDTH); byte_idx++) begin
        strb[byte_idx] = 1'b1;
      end
      return strb;
    end
  endfunction

  task automatic run_write(input int unsigned index);
    logic [ADDR_WIDTH-1:0] exp_addr;
    logic [DATA_WIDTH-1:0] exp_data;
    logic [STRB_WIDTH-1:0] exp_strb;
    logic [PROT_WIDTH-1:0] exp_prot;
    logic [ADDR_WIDTH-1:0] rx_addr;
    logic [DATA_WIDTH-1:0] rx_data;
    logic [STRB_WIDTH-1:0] rx_strb;
    logic [PROT_WIDTH-1:0] rx_prot;
    bit master_slverr;

    exp_addr = build_addr(index);
    exp_data = build_data(index);
    exp_strb = build_strb(index);
    exp_prot = PROT_WIDTH'(index);

    fork
      master_vip.write(exp_addr, exp_data, exp_strb, master_slverr, exp_prot);
      slave_vip.expect_write(rx_addr, rx_data, rx_strb, rx_prot, 1'b0);
    join

    assert(!master_slverr) else $error("APB write returned error at %0d", index);
    assert(rx_addr == exp_addr) else $error("APB write address mismatch at %0d", index);
    assert(rx_data == exp_data) else $error("APB write data mismatch at %0d", index);
    assert(rx_strb == exp_strb) else $error("APB write strobe mismatch at %0d", index);
    assert(rx_prot == exp_prot) else $error("APB write prot mismatch at %0d", index);

    #(INTER_TRANSACTION_PAUSE);
  endtask

  task automatic run_read(input int unsigned index);
    logic [ADDR_WIDTH-1:0] exp_addr;
    logic [DATA_WIDTH-1:0] exp_data;
    logic [PROT_WIDTH-1:0] exp_prot;
    logic [ADDR_WIDTH-1:0] rx_addr;
    logic [PROT_WIDTH-1:0] rx_prot;
    logic [DATA_WIDTH-1:0] master_data;
    bit master_slverr;

    exp_addr = build_addr(index);
    exp_data = build_data(index + 100);
    exp_prot = PROT_WIDTH'(index + 3);

    fork
      master_vip.read(exp_addr, master_data, master_slverr, exp_prot);
      slave_vip.respond_read(exp_data, rx_addr, rx_prot, 1'b0);
    join

    assert(!master_slverr) else $error("APB read returned error at %0d", index);
    assert(rx_addr == exp_addr) else $error("APB read address mismatch at %0d", index);
    assert(rx_prot == exp_prot) else $error("APB read prot mismatch at %0d", index);
    assert(master_data == exp_data)
      else $error("APB read data mismatch at %0d exp=%h got=%h", index, exp_data, master_data);

    #(INTER_TRANSACTION_PAUSE);
  endtask

  initial begin
    clk = 1'b0;
    forever #5 clk = ~clk;
  end

  initial begin
    rstn = 1'b0;
    #20 rstn = 1'b1;
  end

  initial begin
    apb_link.paddr = '0;
    apb_link.psel = 1'b0;
    apb_link.penable = 1'b0;
    apb_link.pwrite = 1'b0;
    apb_link.pwdata = '0;
    apb_link.pstrb = '0;
    apb_link.pprot = '0;
    apb_link.prdata = '0;
    apb_link.pready = 1'b0;
    apb_link.pslverr = 1'b0;
  end

  `TEST_SUITE begin
    master_vip = new(apb_link.master, "master_vip");
    slave_vip  = new(apb_link.slave, "slave_vip");
    master_vip.idle();
    slave_vip.idle();

    @(posedge rstn);
    @(posedge clk);

    slave_vip.configure_ready_delay(0);
    for (int unsigned idx = 0; idx < STIMULUS_COUNT; idx++) begin
      run_write(idx);
      run_read(idx);
    end

    slave_vip.configure_ready_delay(3);
    for (int unsigned idx = 0; idx < 8; idx++) begin
      run_write(idx + STIMULUS_COUNT);
      run_read(idx + STIMULUS_COUNT);
    end
  end

endmodule
