// AXI4-Stream Master VIP
// Provides send_single (single beat) and send_multi (multiple beats) APIs
// following the same send_*/recv_* channel API pattern as AXI4-Full/Lite VIPs.
//
// Architecture:
//   - send_single() : Channel-level API - drive tvalid + tdata + sidebands, wait for tready
//   - send_multi()   : High-level API - sends multiple beats via send_single loop
//
// Backpressure architecture (following AXI4-Full Master's pattern):
//   - apply_pause() is called ONLY in send_multi(), NOT in send_single()
//   - This gives users fine-grained control: use send_single() directly for
//     custom sequencing, or send_multi() for convenience with optional pauses

class Axi4StreamMasterVIP #(
    int DATA_WIDTH  = 32,
    int KEEP_WIDTH  = DATA_WIDTH / 8,
    int TID_WIDTH   = 8,
    int TDEST_WIDTH = 8,
    int TUSER_WIDTH = 32
);

  // handle to the interface
  virtual axi4_stream_if #(DATA_WIDTH, KEEP_WIDTH, TID_WIDTH, TDEST_WIDTH, TUSER_WIDTH).master vif;
  string vip_name;
  bit enable_pause_generator;
  int unsigned min_pause_cycles;
  int unsigned max_pause_cycles;
  int unsigned timeout_cycles;

  // constructor
  function new(
      virtual axi4_stream_if #(DATA_WIDTH, KEEP_WIDTH, TID_WIDTH, TDEST_WIDTH, TUSER_WIDTH).master vif,
      string vip_name = "axi4_stream_master_vip");
    this.vif               = vif;
    this.vip_name          = vip_name;
    enable_pause_generator = 1'b0;
    min_pause_cycles       = 0;
    max_pause_cycles       = 0;
    timeout_cycles         = 1000;
  endfunction

  function void configure_pause_generator(bit enable, int unsigned min_cycles = 0,
                                          int unsigned max_cycles = 0);
    enable_pause_generator = enable;
    min_pause_cycles       = min_cycles;
    max_pause_cycles       = (max_cycles < min_cycles) ? min_cycles : max_cycles;
  endfunction

  function void configure_timeout(int unsigned cycles);
    timeout_cycles = cycles;
  endfunction

  task automatic wait_reset_release();
    int unsigned cycles;
    cycles = 0;
    while (!vif.aresetn) begin
      @(posedge vif.aclk);
      cycles++;
      if (cycles >= timeout_cycles) begin
        $fatal(1, "%s timed out waiting for AXI-Stream reset release", vip_name);
      end
    end
  endtask

  // Clear all master output signals to default state
  // Must be called after reset release before starting transactions
  task automatic clear_outputs();
    vif.tvalid <= 1'b0;
    vif.tdata  <= '0;
    vif.tkeep  <= '0;
    vif.tstrb  <= '0;
    vif.tlast  <= 1'b0;
    vif.tid    <= '0;
    vif.tdest  <= '0;
    vif.tuser  <= '0;
  endtask

  // Channel-level API: send single beat
  // Drives tvalid + tdata + sidebands, waits for tready handshake
  // Does NOT call wait_reset_release() or apply_pause() - those are reserved for high-level tasks
  // (following AXI4-Full/Lite channel API pattern)
  // Signals are driven before the handshake loop (not re-driven each cycle),
  // matching AXI4-Full/Lite's send_bchn/recv_wchn pattern.
  task automatic send_single(logic [DATA_WIDTH-1:0] tdata, logic [KEEP_WIDTH-1:0] tkeep = '1,
                             logic [KEEP_WIDTH-1:0] tstrb = '1, bit tlast = '1,
                             logic [TID_WIDTH-1:0] tid = '0, logic [TDEST_WIDTH-1:0] tdest = '0,
                             logic [TUSER_WIDTH-1:0] tuser = 0);
    int unsigned cycles;

    vif.tdata  <= tdata;
    vif.tkeep  <= tkeep;
    vif.tstrb  <= tstrb;
    vif.tlast  <= tlast;
    vif.tid    <= tid;
    vif.tdest  <= tdest;
    vif.tuser  <= tuser;
    vif.tvalid <= 1'b1;

    cycles = 0;
    do begin
      @(posedge vif.aclk);
      cycles++;
      if (cycles >= timeout_cycles) begin
        $fatal(1, "%s timed out waiting for TREADY", vip_name);
      end
    end while (!vif.tready);

    $display("[%0t] %s TX tdata=%h tkeep=%h tstrb=%h tlast=%0b tid=%0h tdest=%0h tuser=%0h", $time,
             vip_name, tdata, tkeep, tstrb, tlast, tid, tdest, tuser);
    vif.tvalid <= 1'b0;
  endtask

  // High-level API: send multi-beat burst
  // Simplified parameter list (7 arrays -> 1 required array + 3 optional arrays + 2 scalars):
  //   - tdata[]  : required array, size() determines beat count
  //   - tkeep[]  : optional array (pass {} for all 1's)
  //   - tstrb[]  : optional array (pass {} for all 1's)
  //   - tuser[]  : optional array (pass {} for all 0's)
  //   - tid      : scalar, shared across all beats (default 0)
  //   - tdest    : scalar, shared across all beats (default 0)
  //   - tlast    : automatically asserted on the final beat (removed from parameter list)
  // Calls wait_reset_release() before starting, and apply_pause() between beats
  // when pause generator is enabled
  task automatic send_multi(
      input logic [DATA_WIDTH-1:0] tdata[], ref logic [KEEP_WIDTH-1:0] tkeep[],
      ref logic [KEEP_WIDTH-1:0] tstrb[], ref logic [TUSER_WIDTH-1:0] tuser[],
      input logic [TID_WIDTH-1:0] tid = '0, input logic [TDEST_WIDTH-1:0] tdest = '0);
    int unsigned beat_count;
    int unsigned beat_idx;
    logic [KEEP_WIDTH-1:0] default_keep;
    logic [KEEP_WIDTH-1:0] default_strb;
    logic [TUSER_WIDTH-1:0] default_user;

    wait_reset_release();
    beat_count = tdata.size();
    assert (beat_count > 0)
    else $fatal(1, "%s send_multi called with no data beats", vip_name);

    default_keep = '1;
    default_strb = '1;
    default_user = '0;

    // validate optional array sizes (if provided, must be >= beat_count)
    assert (tkeep.size() == 0 || tkeep.size() >= beat_count)
    else
      $fatal(
          1, "%s send_multi: tkeep.size()=%0d < beat_count=%0d", vip_name, tkeep.size(), beat_count
      );
    assert (tstrb.size() == 0 || tstrb.size() >= beat_count)
    else
      $fatal(
          1, "%s send_multi: tstrb.size()=%0d < beat_count=%0d", vip_name, tstrb.size(), beat_count
      );
    assert (tuser.size() == 0 || tuser.size() >= beat_count)
    else
      $fatal(
          1, "%s send_multi: tuser.size()=%0d < beat_count=%0d", vip_name, tuser.size(), beat_count
      );

    for (beat_idx = 0; beat_idx < beat_count; beat_idx++) begin
      if (enable_pause_generator && beat_idx > 0) begin
        apply_pause();
      end
      send_single(tdata[beat_idx], (tkeep.size() > 0) ? tkeep[beat_idx] : default_keep,
                  (tstrb.size() > 0) ? tstrb[beat_idx] : default_strb,
                  (beat_idx == beat_count - 1),  // tlast: auto-assert on final beat
                  tid, tdest, (tuser.size() > 0) ? tuser[beat_idx] : default_user);
    end
  endtask

  // Internal: apply random pause cycles (used only in high-level tasks)
  task automatic apply_pause();
    int unsigned pause_cycles;
    pause_cycles = $urandom_range(max_pause_cycles, min_pause_cycles);
    repeat (pause_cycles) @(posedge vif.aclk);
  endtask

endclass
