class UartTxVIP #(
    int CLKS_PER_BIT = 16,
    int DATA_BITS    = 8
);

  virtual uart_if.transmitter vif;
  string vip_name;

  function new(virtual uart_if.transmitter vif, string vip_name = "uart_tx_vip");
    this.vif = vif;
    this.vip_name = vip_name;
  endfunction

  task automatic idle();
    vif.tx = 1'b1;
  endtask

  task automatic drive_bit(input bit bit_value);
    vif.tx = bit_value;
    repeat (CLKS_PER_BIT) @(posedge vif.clk);
  endtask

  // API: transmit one UART frame, 8N1 by default, LSB first.
  task transmit(input logic [DATA_BITS-1:0] data);
    while (!vif.rstn) @(posedge vif.clk);
    @(posedge vif.clk);

    drive_bit(1'b0);
    for (int bit_idx = 0; bit_idx < DATA_BITS; bit_idx++) begin
      drive_bit(data[bit_idx]);
    end
    drive_bit(1'b1);

    $display("[%0t] %s TX data=%h", $time, vip_name, data);
  endtask

endclass
