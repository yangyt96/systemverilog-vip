`timescale 1ns/1ps

`include "vunit_defines.svh"
`include "axi4_stream_if.sv"
`include "axi4_stream_vip_pkg.sv"

module axi4_stream_vip_tb;

  import vunit_pkg::*;
  import axi4_stream_vip_pkg::*;

  localparam int DATA_WIDTH                = 64;
  localparam int KEEP_WIDTH                = DATA_WIDTH / 8;
  localparam int TID_WIDTH                 = 8;
  localparam int TDEST_WIDTH               = 8;
  localparam int TUSER_WIDTH               = 32;
  localparam int BASIC_STIMULUS_COUNT      = 48;
  localparam int PAUSE_STIMULUS_COUNT      = 40;
  localparam int BP_STIMULUS_COUNT         = 40;
  localparam int CONTINUOUS_STIMULUS_COUNT = 64;

  logic clk;
  logic rstn;

  axi4_stream_if #(DATA_WIDTH, KEEP_WIDTH, TID_WIDTH, TDEST_WIDTH, TUSER_WIDTH) axis_if(clk, rstn);

  Axi4StreamMasterVIP #(DATA_WIDTH, KEEP_WIDTH, TID_WIDTH, TDEST_WIDTH, TUSER_WIDTH) master;
  Axi4StreamSlaveVIP  #(DATA_WIDTH, KEEP_WIDTH, TID_WIDTH, TDEST_WIDTH, TUSER_WIDTH) slave;

  // Clock generation
  initial begin
    clk = 0;
    forever #5 clk = ~clk;
  end

  // Reset generation
  initial begin
    rstn = 0;
    #20 rstn = 1;
  end

  // Initialize master-driven signals (tready is driven by slave VIP through its modport)
  initial begin
    axis_if.tvalid = 1'b0;
    axis_if.tdata  = '0;
    axis_if.tkeep  = '0;
    axis_if.tstrb  = '0;
    axis_if.tlast  = 1'b0;
    axis_if.tid    = '0;
    axis_if.tdest  = '0;
    axis_if.tuser  = '0;
  end

  function automatic logic [DATA_WIDTH-1:0] build_tdata(int unsigned index);
    logic [DATA_WIDTH-1:0] value;
    value = '0;
    for (int byte_idx = 0; byte_idx < KEEP_WIDTH; byte_idx++) begin
      value[(byte_idx * 8) +: 8] = byte'((index * 13) + byte_idx);
    end
    return value;
  endfunction

  function automatic logic [KEEP_WIDTH-1:0] build_byte_mask(int unsigned index);
    logic [KEEP_WIDTH-1:0] mask;
    int active_bytes;
    mask = '0;
    active_bytes = (index % KEEP_WIDTH) + 1;
    for (int byte_idx = 0; byte_idx < active_bytes; byte_idx++) begin
      mask[byte_idx] = 1'b1;
    end
    return mask;
  endfunction

  // Single transfer: fork send + recv, then verify all signals
  task automatic run_transfer(input int unsigned index);
    logic [DATA_WIDTH-1:0] exp_tdata;
    logic [KEEP_WIDTH-1:0] exp_tkeep;
    logic [KEEP_WIDTH-1:0] exp_tstrb;
    bit                    exp_tlast;
    logic [TID_WIDTH-1:0]  exp_tid;
    logic [TDEST_WIDTH-1:0] exp_tdest;
    logic [TUSER_WIDTH-1:0] exp_tuser;
    logic [DATA_WIDTH-1:0] rx_tdata;
    logic [KEEP_WIDTH-1:0] rx_tkeep;
    logic [KEEP_WIDTH-1:0] rx_tstrb;
    bit                    rx_tlast;
    logic [TID_WIDTH-1:0]  rx_tid;
    logic [TDEST_WIDTH-1:0] rx_tdest;
    logic [TUSER_WIDTH-1:0] rx_tuser;

    exp_tdata = build_tdata(index);
    exp_tkeep = build_byte_mask(index);
    exp_tstrb = build_byte_mask(index + 1);
    exp_tlast = ((index % 8) == 7);
    exp_tid   = TID_WIDTH'(index);
    exp_tdest = TDEST_WIDTH'(8'h80 | (index & 'h7f));
    exp_tuser = TUSER_WIDTH'(32'h8765_0000 | index);

    fork
      master.send_single(exp_tdata, exp_tkeep, exp_tstrb, exp_tlast,
                         exp_tid, exp_tdest, exp_tuser);
      slave.recv_single(rx_tdata, rx_tkeep, rx_tstrb, rx_tlast,
                        rx_tid, rx_tdest, rx_tuser);
    join

    assert(rx_tdata == exp_tdata) else $error("Data mismatch at stimulus %0d", index);
    assert(rx_tkeep == exp_tkeep) else $error("TKEEP mismatch at stimulus %0d", index);
    assert(rx_tstrb == exp_tstrb) else $error("TSTRB mismatch at stimulus %0d", index);
    assert(rx_tlast == exp_tlast) else $error("TLAST mismatch at stimulus %0d", index);
    assert(rx_tid == exp_tid) else $error("TID mismatch at stimulus %0d", index);
    assert(rx_tdest == exp_tdest) else $error("TDEST mismatch at stimulus %0d", index);
    assert(rx_tuser == exp_tuser) else $error("TUSER mismatch at stimulus %0d", index);

    @(posedge clk);
  endtask

  `TEST_SUITE begin
    int unsigned stimulus_idx;
    int unsigned observed_count;
    int unsigned observed_tlast_count;

    `TEST_SUITE_SETUP begin
      master = new(axis_if.master, "master_vip");
      slave  = new(axis_if.slave, "slave_vip");

      @(posedge rstn);
      @(posedge clk);

      master.clear_outputs();
      slave.clear_outputs();
      @(posedge clk);
    end

    `TEST_CASE("BasicTransfers") begin
      master.configure_pause_generator(1'b0);
      slave.configure_backpressure(1'b0);
      for (stimulus_idx = 0; stimulus_idx < BASIC_STIMULUS_COUNT; stimulus_idx++) begin
        run_transfer(stimulus_idx);
      end
    end

    `TEST_CASE("PauseGenerator") begin
      master.configure_pause_generator(1'b1, 1, 4);
      slave.configure_backpressure(1'b0);
      for (stimulus_idx = BASIC_STIMULUS_COUNT;
           stimulus_idx < (BASIC_STIMULUS_COUNT + PAUSE_STIMULUS_COUNT);
           stimulus_idx++) begin
        run_transfer(stimulus_idx);
      end
    end

    `TEST_CASE("Backpressure") begin
      master.configure_pause_generator(1'b0);
      slave.configure_backpressure(1'b1, 2, 6);
      for (stimulus_idx = (BASIC_STIMULUS_COUNT + PAUSE_STIMULUS_COUNT);
           stimulus_idx < (BASIC_STIMULUS_COUNT + PAUSE_STIMULUS_COUNT + BP_STIMULUS_COUNT);
           stimulus_idx++) begin
        run_transfer(stimulus_idx);
      end
    end

    `TEST_CASE("ContinuousStream") begin
      master.configure_pause_generator(1'b0);
      slave.configure_backpressure(1'b0);

      fork
        // Drive stream
        for (stimulus_idx = 0; stimulus_idx < CONTINUOUS_STIMULUS_COUNT; stimulus_idx++) begin
          master.send_single(build_tdata(stimulus_idx),
                             build_byte_mask(stimulus_idx),
                             build_byte_mask(stimulus_idx + 1),
                             ((stimulus_idx % 8) == 7),
                             TID_WIDTH'(stimulus_idx),
                             TDEST_WIDTH'(8'h80 | (stimulus_idx & 'h7f)),
                             TUSER_WIDTH'(32'h8765_0000 | stimulus_idx));
        end
        // Receive stream using slave VIP (avoids direct tready drive conflict)
        begin
          logic [DATA_WIDTH-1:0] rx_tdata;
          logic [KEEP_WIDTH-1:0] rx_tkeep;
          logic [KEEP_WIDTH-1:0] rx_tstrb;
          bit                    rx_tlast;
          logic [TID_WIDTH-1:0]  rx_tid;
          logic [TDEST_WIDTH-1:0] rx_tdest;
          logic [TUSER_WIDTH-1:0] rx_tuser;
          int unsigned last_seen_tid;
          int unsigned last_seen_tlast_count;

          observed_count = 0;
          last_seen_tid = 0;
          last_seen_tlast_count = 0;

          while (observed_count < CONTINUOUS_STIMULUS_COUNT) begin
            slave.recv_single(rx_tdata, rx_tkeep, rx_tstrb, rx_tlast,
                              rx_tid, rx_tdest, rx_tuser);
            observed_count++;
            last_seen_tid = rx_tid;
            if (rx_tlast) begin
              last_seen_tlast_count++;
            end
          end

          observed_tlast_count = last_seen_tlast_count;
          assert(last_seen_tid == (CONTINUOUS_STIMULUS_COUNT - 1))
            else $error("Continuous stream last TID mismatch exp=%0d got=%0d",
                        CONTINUOUS_STIMULUS_COUNT - 1, last_seen_tid);
        end
      join

      assert(observed_count == CONTINUOUS_STIMULUS_COUNT)
        else $error("Continuous stream count mismatch exp=%0d got=%0d",
                    CONTINUOUS_STIMULUS_COUNT, observed_count);
      assert(observed_tlast_count == (CONTINUOUS_STIMULUS_COUNT / 8))
        else $error("Continuous stream TLAST count mismatch exp=%0d got=%0d",
                    CONTINUOUS_STIMULUS_COUNT / 8, observed_tlast_count);
    end

    `TEST_CASE("BurstTransfers") begin
      int data_idx;

      master.configure_pause_generator(1'b0);
      slave.configure_backpressure(1'b0);

      for (int burst_idx = 0; burst_idx < 10; burst_idx++) begin
        int unsigned burst_length;
        logic [DATA_WIDTH-1:0] tx_tdata[];
        logic [KEEP_WIDTH-1:0] tx_tkeep[];
        logic [KEEP_WIDTH-1:0] tx_tstrb[];
        bit                    tx_tlast[];
        logic [TID_WIDTH-1:0]  tx_tid[];
        logic [TDEST_WIDTH-1:0] tx_tdest[];
        logic [TUSER_WIDTH-1:0] tx_tuser[];

        logic [DATA_WIDTH-1:0] rx_tdata[];
        logic [KEEP_WIDTH-1:0] rx_tkeep[];
        logic [KEEP_WIDTH-1:0] rx_tstrb[];
        bit                    rx_tlast[];
        logic [TID_WIDTH-1:0]  rx_tid[];
        logic [TDEST_WIDTH-1:0] rx_tdest[];
        logic [TUSER_WIDTH-1:0] rx_tuser[];

        burst_length = $urandom_range(16, 2);

        tx_tdata  = new[burst_length];
        tx_tkeep  = new[burst_length];
        tx_tstrb  = new[burst_length];
        tx_tlast  = new[burst_length];
        tx_tid    = new[burst_length];
        tx_tdest  = new[burst_length];
        tx_tuser  = new[burst_length];
        rx_tdata  = new[burst_length];
        rx_tkeep  = new[burst_length];
        rx_tstrb  = new[burst_length];
        rx_tlast  = new[burst_length];
        rx_tid    = new[burst_length];
        rx_tdest  = new[burst_length];
        rx_tuser  = new[burst_length];

        for (int beat_idx = 0; beat_idx < burst_length; beat_idx++) begin
          data_idx = burst_idx * 100 + beat_idx;
          tx_tdata[beat_idx]  = build_tdata(data_idx);
          tx_tkeep[beat_idx]  = build_byte_mask(data_idx);
          tx_tstrb[beat_idx]  = build_byte_mask(data_idx + 1);
          tx_tlast[beat_idx]  = (beat_idx == burst_length - 1);
          tx_tid[beat_idx]    = TID_WIDTH'(burst_idx);
          tx_tdest[beat_idx]  = TDEST_WIDTH'(8'hA0 | (burst_idx & 'h0F));
          tx_tuser[beat_idx]  = TUSER_WIDTH'(32'hABCD_0000 | beat_idx);
        end

        fork
          master.send_multi(tx_tdata, tx_tkeep, tx_tstrb, tx_tlast, tx_tid, tx_tdest, tx_tuser);
          slave.recv_multi(rx_tdata, rx_tkeep, rx_tstrb, rx_tlast, rx_tid, rx_tdest, rx_tuser);
        join

        assert(rx_tdata.size() == burst_length)
          else $error("Burst %0d: RX data size mismatch", burst_idx);
        assert(rx_tkeep.size() == burst_length)
          else $error("Burst %0d: RX keep size mismatch", burst_idx);
        assert(rx_tstrb.size() == burst_length)
          else $error("Burst %0d: RX strb size mismatch", burst_idx);
        assert(rx_tlast.size() == burst_length)
          else $error("Burst %0d: RX last size mismatch", burst_idx);
        assert(rx_tid.size() == burst_length)
          else $error("Burst %0d: RX tid size mismatch", burst_idx);
        assert(rx_tdest.size() == burst_length)
          else $error("Burst %0d: RX tdest size mismatch", burst_idx);
        assert(rx_tuser.size() == burst_length)
          else $error("Burst %0d: RX tuser size mismatch", burst_idx);

        for (int beat_idx = 0; beat_idx < burst_length; beat_idx++) begin
          assert(rx_tdata[beat_idx] == tx_tdata[beat_idx])
            else $error("Burst %0d beat %0d: TDATA mismatch", burst_idx, beat_idx);
          assert(rx_tkeep[beat_idx] == tx_tkeep[beat_idx])
            else $error("Burst %0d beat %0d: TKEEP mismatch", burst_idx, beat_idx);
          assert(rx_tstrb[beat_idx] == tx_tstrb[beat_idx])
            else $error("Burst %0d beat %0d: TSTRB mismatch", burst_idx, beat_idx);
          assert(rx_tlast[beat_idx] == tx_tlast[beat_idx])
            else $error("Burst %0d beat %0d: TLAST mismatch", burst_idx, beat_idx);
          assert(rx_tid[beat_idx] == tx_tid[beat_idx])
            else $error("Burst %0d beat %0d: TID mismatch", burst_idx, beat_idx);
          assert(rx_tdest[beat_idx] == tx_tdest[beat_idx])
            else $error("Burst %0d beat %0d: TDEST mismatch", burst_idx, beat_idx);
          assert(rx_tuser[beat_idx] == tx_tuser[beat_idx])
            else $error("Burst %0d beat %0d: TUSER mismatch", burst_idx, beat_idx);
        end

        $display("[%0t] Burst %0d completed with %0d beats", $time, burst_idx, burst_length);
      end
    end

    `TEST_CASE("SidebandSignals") begin
      master.configure_pause_generator(1'b0);
      slave.configure_backpressure(1'b0);

      for (stimulus_idx = 0; stimulus_idx < 16; stimulus_idx++) begin
        logic [DATA_WIDTH-1:0] exp_tdata;
        logic [KEEP_WIDTH-1:0] exp_tkeep;
        logic [KEEP_WIDTH-1:0] exp_tstrb;
        bit                    exp_tlast;
        logic [TID_WIDTH-1:0]  exp_tid;
        logic [TDEST_WIDTH-1:0] exp_tdest;
        logic [TUSER_WIDTH-1:0] exp_tuser;
        logic [DATA_WIDTH-1:0] rx_tdata;
        logic [KEEP_WIDTH-1:0] rx_tkeep;
        logic [KEEP_WIDTH-1:0] rx_tstrb;
        bit                    rx_tlast;
        logic [TID_WIDTH-1:0]  rx_tid;
        logic [TDEST_WIDTH-1:0] rx_tdest;
        logic [TUSER_WIDTH-1:0] rx_tuser;

        exp_tdata = build_tdata(stimulus_idx);
        exp_tkeep = '1;
        exp_tstrb = '1;
        exp_tlast = 1'b0;

        if (stimulus_idx < 4) begin
          exp_tid   = TID_WIDTH'(stimulus_idx == 0 ? '0 : stimulus_idx == 1 ? '1 : stimulus_idx == 2 ? 8'hAA : 8'h55);
          exp_tdest = TDEST_WIDTH'(8'h00);
          exp_tuser = TUSER_WIDTH'(32'h0000_0000);
        end else if (stimulus_idx < 8) begin
          exp_tid   = TID_WIDTH'(8'hF0);
          exp_tdest = TDEST_WIDTH'(stimulus_idx == 4 ? '0 : stimulus_idx == 5 ? '1 : stimulus_idx == 6 ? 8'hCC : 8'h33);
          exp_tuser = TUSER_WIDTH'(32'h0000_0000);
        end else begin
          exp_tid   = TID_WIDTH'(8'h0F);
          exp_tdest = TDEST_WIDTH'(8'h55);
          exp_tuser = TUSER_WIDTH'(stimulus_idx == 8 ? '0 : stimulus_idx == 9 ? '1 : stimulus_idx == 10 ? 32'hAAAA_AAAA : 32'h5555_5555);
        end

        fork
          master.send_single(exp_tdata, exp_tkeep, exp_tstrb, exp_tlast,
                             exp_tid, exp_tdest, exp_tuser);
          slave.recv_single(rx_tdata, rx_tkeep, rx_tstrb, rx_tlast,
                            rx_tid, rx_tdest, rx_tuser);
        join

        assert(rx_tdata == exp_tdata) else $error("Sideband: TDATA mismatch at %0d", stimulus_idx);
        assert(rx_tkeep == exp_tkeep) else $error("Sideband: TKEEP mismatch at %0d", stimulus_idx);
        assert(rx_tstrb == exp_tstrb) else $error("Sideband: TSTRB mismatch at %0d", stimulus_idx);
        assert(rx_tlast == exp_tlast) else $error("Sideband: TLAST mismatch at %0d", stimulus_idx);
        assert(rx_tid == exp_tid) else $error("Sideband: TID mismatch at %0d", stimulus_idx);
        assert(rx_tdest == exp_tdest) else $error("Sideband: TDEST mismatch at %0d", stimulus_idx);
        assert(rx_tuser == exp_tuser) else $error("Sideband: TUSER mismatch at %0d", stimulus_idx);

        @(posedge clk);
      end
    end
  end

endmodule
