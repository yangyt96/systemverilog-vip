class SpiSlaveVIP #(
    int DATA_BITS = 8
);

  virtual spi_if.slave vif;
  string vip_name;
  int unsigned timeout_cycles;

  function new(virtual spi_if.slave vif, string vip_name = "spi_slave_vip");
    this.vif = vif;
    this.vip_name = vip_name;
    timeout_cycles = 10000;
  endfunction

  function void configure_timeout(int unsigned cycles);
    timeout_cycles = cycles;
  endfunction

  task automatic idle();
    vif.miso = 1'b0;
  endtask

  // API: full-duplex SPI mode 0 transfer, MSB first.
  task transfer(input logic [DATA_BITS-1:0] tx_data, output logic [DATA_BITS-1:0] rx_data);
    int unsigned cycles;

    rx_data = '0;

    cycles = 0;
    while (!vif.rstn) begin
      @(posedge vif.clk);
      cycles++;
      if (cycles >= timeout_cycles) begin
        $fatal(1, "%s timed out waiting for SPI reset release", vip_name);
      end
    end
    cycles = 0;
    while (vif.cs_n !== 1'b1) begin
      @(posedge vif.clk);
      cycles++;
      if (cycles >= timeout_cycles) begin
        $fatal(1, "%s timed out waiting for SPI idle", vip_name);
      end
    end
    cycles = 0;
    while (vif.cs_n !== 1'b0) begin
      @(posedge vif.clk);
      cycles++;
      if (cycles >= timeout_cycles) begin
        $fatal(1, "%s timed out waiting for SPI chip-select", vip_name);
      end
    end

    vif.miso = tx_data[DATA_BITS-1];

    for (int bit_idx = DATA_BITS - 1; bit_idx >= 0; bit_idx--) begin
      @(posedge vif.sclk);
      rx_data[bit_idx] = vif.mosi;

      if (bit_idx > 0) begin
        @(negedge vif.sclk);
        vif.miso = tx_data[bit_idx-1];
      end
    end

    @(posedge vif.cs_n);
    vif.miso = 1'b0;

    $display("[%0t] %s TX=%h RX=%h", $time, vip_name, tx_data, rx_data);
  endtask

endclass
