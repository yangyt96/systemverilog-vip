class AxiStreamSlaveVIP #(
  int DATA_WIDTH = 32,
  int KEEP_WIDTH = DATA_WIDTH / 8
);

  // handle to the interface
  virtual axi_stream_if #(DATA_WIDTH, KEEP_WIDTH).slave vif;
  bit enable_backpressure;
  int unsigned min_stall_cycles;
  int unsigned max_stall_cycles;

  // constructor
  function new(virtual axi_stream_if #(DATA_WIDTH, KEEP_WIDTH).slave vif);
    this.vif = vif;
    enable_backpressure = 1'b0;
    min_stall_cycles    = 0;
    max_stall_cycles    = 0;
  endfunction

  function void configure_backpressure(bit enable,
                                       int unsigned min_cycles = 0,
                                       int unsigned max_cycles = 0);
    enable_backpressure = enable;
    min_stall_cycles    = min_cycles;
    max_stall_cycles    = (max_cycles < min_cycles) ? min_cycles : max_cycles;
  endfunction

  // API: pop_axi_stream
  task pop_axi_stream(output logic [DATA_WIDTH-1:0] tdata,
                      output logic [KEEP_WIDTH-1:0] tkeep,
                      output logic [KEEP_WIDTH-1:0] tstrb,
                      output bit                    tlast,
                      output byte                   tid,
                      output byte                   tdest,
                      output int unsigned           tuser);
    int unsigned stall_cycles;

    while (!vif.aresetn) @(posedge vif.aclk);
    vif.tready <= 1'b0;

    if (enable_backpressure) begin
      stall_cycles = $urandom_range(max_stall_cycles, min_stall_cycles);
      repeat (stall_cycles) @(posedge vif.aclk);
    end

    // ready to accept data
    vif.tready <= 1'b1;

    // wait for valid data
    while (!vif.tvalid) @(posedge vif.aclk);

    // capture signals
    tdata = vif.tdata;
    tkeep = vif.tkeep;
    tstrb = vif.tstrb;
    tlast = vif.tlast;
    tid   = vif.tid;
    tdest = vif.tdest;
    tuser = vif.tuser;

    // handshake complete
    @(posedge vif.aclk);
    vif.tready <= 1'b0;
  endtask

endclass
