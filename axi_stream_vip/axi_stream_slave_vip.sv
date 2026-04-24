class AxiStreamSlaveVIP;

  // handle to the interface
  virtual axi_stream_if #(32).slave vif;

  // constructor
  function new(virtual axi_stream_if #(32).slave vif);
    this.vif = vif;
  endfunction

  // API: pop_axi_stream
  task pop_axi_stream(output logic [31:0] tdata,
                      output logic [3:0]  tkeep,
                      output logic [3:0]  tstrb,
                      output bit          tlast,
                      output byte         tid,
                      output byte         tdest,
                      output int unsigned tuser);
    // ready to accept data
    vif.tready <= 1'b1;

    // wait for valid data
    @(posedge vif.aclk);
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
