class AxiStreamMasterVIP #(
  int DATA_WIDTH = 32,
  int KEEP_WIDTH = DATA_WIDTH / 8
);

  // handle to the interface
  virtual axi_stream_if #(DATA_WIDTH, KEEP_WIDTH).master vif;

  // constructor
  function new(virtual axi_stream_if #(DATA_WIDTH, KEEP_WIDTH).master vif);
    this.vif = vif;
  endfunction

  // API: push_axi_stream
  task push_axi_stream(logic [DATA_WIDTH-1:0] tdata,
                       logic [KEEP_WIDTH-1:0] tkeep,
                       logic [KEEP_WIDTH-1:0] tstrb,
                       bit                    tlast,
                       byte                   tid,
                       byte                   tdest,
                       int unsigned           tuser);
    while (!vif.aresetn) @(posedge vif.aclk);

    // drive signals
    vif.tdata  <= tdata;
    vif.tkeep  <= tkeep;
    vif.tstrb  <= tstrb;
    vif.tlast  <= tlast;
    vif.tid    <= tid;
    vif.tdest  <= tdest;
    vif.tuser  <= tuser;

    // handshake
    vif.tvalid <= 1'b1;
    @(posedge vif.aclk);
    while (!vif.tready) @(posedge vif.aclk);
    vif.tvalid <= 1'b0;
  endtask

endclass
