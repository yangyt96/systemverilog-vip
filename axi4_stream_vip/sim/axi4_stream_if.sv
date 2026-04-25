interface axi4_stream_if #(
    parameter int unsigned DATA_WIDTH  = 32,
    parameter int unsigned KEEP_WIDTH  = DATA_WIDTH / 8,
    parameter int unsigned TID_WIDTH   = 8,
    parameter int unsigned TDEST_WIDTH = 8,
    parameter int unsigned TUSER_WIDTH = 32
) (
    input logic aclk,
    input logic aresetn
);

  // core signals
  logic [ DATA_WIDTH-1:0] tdata;
  logic                   tvalid;
  logic                   tready;

  // optional signals
  logic [ KEEP_WIDTH-1:0] tkeep;  // byte qualifiers
  logic [ KEEP_WIDTH-1:0] tstrb;  // byte strobes
  logic                   tlast;  // end of packet/frame
  logic [  TID_WIDTH-1:0] tid;  // stream id
  logic [TDEST_WIDTH-1:0] tdest;  // destination routing
  logic [TUSER_WIDTH-1:0] tuser;  // user-defined sideband

  // modports for direction control
  modport master(
      input aclk, aresetn, tready,
      output tvalid, tdata, tkeep, tstrb, tlast, tid, tdest, tuser
  );

  modport slave(
      input aclk, aresetn, tvalid, tdata, tkeep, tstrb, tlast, tid, tdest, tuser,
      output tready
  );

endinterface
