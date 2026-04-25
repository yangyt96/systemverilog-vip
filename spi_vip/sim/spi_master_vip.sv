class SpiMasterVIP #(
    int DATA_BITS        = 8,
    int HALF_SCLK_CYCLES = 4
);

  virtual spi_if.master vif;
  string vip_name;

  function new(virtual spi_if.master vif, string vip_name = "spi_master_vip");
    this.vif = vif;
    this.vip_name = vip_name;
  endfunction

  task automatic idle();
    vif.sclk = 1'b0;
    vif.cs_n = 1'b1;
    vif.mosi = 1'b0;
  endtask

  task automatic wait_half_sclk();
    repeat (HALF_SCLK_CYCLES) @(posedge vif.clk);
  endtask

  // API: full-duplex SPI mode 0 transfer, MSB first.
  task transfer(input logic [DATA_BITS-1:0] tx_data, output logic [DATA_BITS-1:0] rx_data);
    rx_data = '0;

    while (!vif.rstn) @(posedge vif.clk);
    @(posedge vif.clk);

    vif.cs_n = 1'b0;

    for (int bit_idx = DATA_BITS - 1; bit_idx >= 0; bit_idx--) begin
      vif.mosi = tx_data[bit_idx];
      wait_half_sclk();
      vif.sclk = 1'b1;
      wait_half_sclk();
      rx_data[bit_idx] = vif.miso;
      vif.sclk = 1'b0;
    end

    wait_half_sclk();
    vif.cs_n = 1'b1;
    vif.mosi = 1'b0;

    $display("[%0t] %s TX=%h RX=%h", $time, vip_name, tx_data, rx_data);
  endtask

endclass
