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

  // API: transmit
  task transmit(logic [DATA_WIDTH-1:0] tdata, logic [KEEP_WIDTH-1:0] tkeep = '1,
                logic [KEEP_WIDTH-1:0] tstrb = '1, bit tlast = '1, logic [TID_WIDTH-1:0] tid = '0,
                logic [TDEST_WIDTH-1:0] tdest = '0, logic [TUSER_WIDTH-1:0] tuser = 0);
    int unsigned pause_cycles;

    wait_reset_release();

    if (enable_pause_generator) begin
      pause_cycles = $urandom_range(max_pause_cycles, min_pause_cycles);
      repeat (pause_cycles) @(posedge vif.aclk);
    end

    // drive signals
    vif.tdata  = tdata;
    vif.tkeep  = tkeep;
    vif.tstrb  = tstrb;
    vif.tlast  = tlast;
    vif.tid    = tid;
    vif.tdest  = tdest;
    vif.tuser  = tuser;

    // handshake
    vif.tvalid = 1'b1;
    @(posedge vif.aclk);
    begin
      int unsigned cycles;
      cycles = 0;
      while (!vif.tready) begin
        @(posedge vif.aclk);
        cycles++;
        if (cycles >= timeout_cycles) begin
          $fatal(1, "%s timed out waiting for TREADY", vip_name);
        end
      end
    end
    $display("[%0t] %s TX tdata=%h tkeep=%h tstrb=%h tlast=%0b tid=%0h tdest=%0h tuser=%0h", $time,
             vip_name, tdata, tkeep, tstrb, tlast, tid, tdest, tuser);
    vif.tvalid = 1'b0;
  endtask

endclass
