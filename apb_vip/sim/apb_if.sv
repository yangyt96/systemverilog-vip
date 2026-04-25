interface apb_if #(
  parameter int ADDR_WIDTH = 16,
  parameter int DATA_WIDTH = 32,
  parameter int STRB_WIDTH = DATA_WIDTH / 8,
  parameter int PROT_WIDTH = 3
) (
  input logic pclk,
  input logic presetn
);

  logic [ADDR_WIDTH-1:0] paddr;
  logic                  psel;
  logic                  penable;
  logic                  pwrite;
  logic [DATA_WIDTH-1:0] pwdata;
  logic [STRB_WIDTH-1:0] pstrb;
  logic [PROT_WIDTH-1:0] pprot;
  logic [DATA_WIDTH-1:0] prdata;
  logic                  pready;
  logic                  pslverr;

  modport master (
    input  pclk, presetn, prdata, pready, pslverr,
    output paddr, psel, penable, pwrite, pwdata, pstrb, pprot
  );

  modport slave (
    input  pclk, presetn, paddr, psel, penable, pwrite, pwdata, pstrb, pprot,
    output prdata, pready, pslverr
  );

endinterface
