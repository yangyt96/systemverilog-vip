interface spi_if(input logic clk,
                 input logic rstn);

  logic sclk;
  logic cs_n;
  logic mosi;
  logic miso;

  modport master(input  clk, rstn, miso,
                 output sclk, cs_n, mosi);

  modport slave(input  clk, rstn, sclk, cs_n, mosi,
                output miso);

endinterface
