interface i2s_if(input logic clk,
                 input logic rstn);

  logic bclk;
  logic ws;
  logic sd;

  modport transmitter(input  clk, rstn,
                      output bclk, ws, sd);

  modport receiver(input clk, rstn, bclk, ws, sd);

endinterface
