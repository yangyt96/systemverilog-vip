class SpiSlaveVIP #(
  int DATA_BITS = 8
);

  virtual spi_if.slave vif;
  string vip_name;

  function new(virtual spi_if.slave vif,
               string vip_name = "spi_slave_vip");
    this.vif = vif;
    this.vip_name = vip_name;
  endfunction

  task automatic idle();
    vif.miso = 1'b0;
  endtask

  // API: full-duplex SPI mode 0 transfer, MSB first.
  task transfer(input  logic [DATA_BITS-1:0] tx_data,
                output logic [DATA_BITS-1:0] rx_data);
    rx_data = '0;

    while (!vif.rstn) @(posedge vif.clk);
    while (vif.cs_n !== 1'b1) @(posedge vif.clk);
    @(negedge vif.cs_n);

    vif.miso = tx_data[DATA_BITS-1];

    for (int bit_idx = DATA_BITS - 1; bit_idx >= 0; bit_idx--) begin
      @(posedge vif.sclk);
      rx_data[bit_idx] = vif.mosi;

      if (bit_idx > 0) begin
        @(negedge vif.sclk);
        vif.miso = tx_data[bit_idx - 1];
      end
    end

    @(posedge vif.cs_n);
    vif.miso = 1'b0;

    $display("[%0t] %s TX=%h RX=%h", $time, vip_name, tx_data, rx_data);
  endtask

endclass
