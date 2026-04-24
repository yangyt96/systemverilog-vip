`timescale 1ns/1ps




`include "vunit_defines.svh"
`include "axi_stream_master_vip.sv"
`include "axi_stream_slave_vip.sv"

module axi_stream_dut_tb;

  import vunit_pkg::*;  // VUnit integration

  // clock and reset
  logic clk;
  logic rstn;

  // instantiate AXI Stream interfaces for DUT input and output
  axi_stream_if #(32) s_axis_if(clk, rstn);
  axi_stream_if #(32) m_axis_if(clk, rstn);

  // DUT instantiation (explicit ports if not using interface)
  axi_stream_dut #(.DATA_WIDTH(32)) dut (
    .aclk(clk),
    .aresetn(rstn),
    .s_axis_tdata (s_axis_if.tdata),
    .s_axis_tvalid(s_axis_if.tvalid),
    .s_axis_tready(s_axis_if.tready),
    .s_axis_tkeep (s_axis_if.tkeep),
    .s_axis_tstrb (s_axis_if.tstrb),
    .s_axis_tlast (s_axis_if.tlast),
    .s_axis_tid   (s_axis_if.tid),
    .s_axis_tdest (s_axis_if.tdest),
    .s_axis_tuser (s_axis_if.tuser),

    .m_axis_tdata (m_axis_if.tdata),
    .m_axis_tvalid(m_axis_if.tvalid),
    .m_axis_tready(m_axis_if.tready),
    .m_axis_tkeep (m_axis_if.tkeep),
    .m_axis_tstrb (m_axis_if.tstrb),
    .m_axis_tlast (m_axis_if.tlast),
    .m_axis_tid   (m_axis_if.tid),
    .m_axis_tdest (m_axis_if.tdest),
    .m_axis_tuser (m_axis_if.tuser)
  );

  // VIP handles
  AxiStreamMasterVIP master;
  AxiStreamSlaveVIP  slave;

  // clock generation
  initial begin
    clk = 0;
    forever #5 clk = ~clk;
  end

  // reset
  initial begin
    rstn = 0;
    #20 rstn = 1;
  end

  initial begin
    s_axis_if.tvalid = 1'b0;
    s_axis_if.tdata  = '0;
    s_axis_if.tkeep  = '0;
    s_axis_if.tstrb  = '0;
    s_axis_if.tlast  = 1'b0;
    s_axis_if.tid    = '0;
    s_axis_if.tdest  = '0;
    s_axis_if.tuser  = '0;
    m_axis_if.tready = 1'b0;
  end


  `TEST_SUITE begin

      logic [31:0] tdata;
      logic [3:0]  tkeep, tstrb;
      bit          tlast;
      byte         tid, tdest;
      int unsigned tuser;

      master = new(s_axis_if.master);
      slave  = new(m_axis_if.slave);

      @(posedge rstn);
      @(posedge clk);

      fork
        master.push_axi_stream(32'hCAFEBABE,
                               4'hF, 4'hF,
                               1'b1,
                               8'h02,
                               8'h01,
                               32'h87654321);
        slave.pop_axi_stream(tdata, tkeep, tstrb, tlast, tid, tdest, tuser);
      join

      // check result
      assert(tdata == 32'hCAFEBABE) else $error("Data mismatch!");
      assert(tlast == 1'b1) else $error("TLAST mismatch!");
  end


endmodule
