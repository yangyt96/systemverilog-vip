interface uart_if (
    input logic clk,
    input logic rstn
);

  // UART line is idle high. One interface instance represents one serial link.
  // The signal is named serial_data because it carries data in both directions:
  // the transmitter drives it and the receiver samples it.
  logic serial_data;

  modport transmitter(input clk, rstn, output serial_data);

  modport receiver(input clk, rstn, serial_data);

endinterface
