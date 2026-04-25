class SpiMasterVIP #(
    int DATA_BITS        = 8,
    int HALF_SCLK_CYCLES = 4
);

  virtual spi_if.master vif;
  string vip_name;
  int unsigned timeout_cycles;
  bit cpol;
  bit cpha;

  function new(virtual spi_if.master vif, string vip_name = "spi_master_vip");
    this.vif = vif;
    this.vip_name = vip_name;
    timeout_cycles = 10000;
    cpol = 1'b0;
    cpha = 1'b0;
  endfunction

  function void configure_timeout(int unsigned cycles);
    timeout_cycles = cycles;
  endfunction

  function void configure_mode(input bit cpol, input bit cpha);
    this.cpol = cpol;
    this.cpha = cpha;
  endfunction

  task automatic idle();
    vif.sclk = cpol;
    vif.cs_n = 1'b1;
    vif.mosi = 1'b0;
  endtask

  task automatic wait_half_sclk();
    repeat (HALF_SCLK_CYCLES) @(posedge vif.clk);
  endtask

  // API: full-duplex SPI transfer, MSB first.
  // Supports all 4 SPI modes based on configured CPOL/CPHA.
  //   Mode 0: CPOL=0, CPHA=0 - SCLK idle low,  sample on rising  edge
  //   Mode 1: CPOL=0, CPHA=1 - SCLK idle low,  sample on falling edge
  //   Mode 2: CPOL=1, CPHA=0 - SCLK idle high, sample on falling edge
  //   Mode 3: CPOL=1, CPHA=1 - SCLK idle high, sample on rising  edge
  task automatic transfer(input logic [DATA_BITS-1:0] tx_data, output logic [DATA_BITS-1:0] rx_data);
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
    @(posedge vif.clk);

    vif.cs_n = 1'b0;

    for (int bit_idx = DATA_BITS - 1; bit_idx >= 0; bit_idx--) begin
      if (cpha == 1'b0) begin
        // CPHA=0: data output before first edge, sampled on first edge
        vif.mosi = tx_data[bit_idx];
        wait_half_sclk();
        vif.sclk = ~cpol;  // first edge
        wait_half_sclk();
        rx_data[bit_idx] = vif.miso;
        vif.sclk = cpol;   // second edge (back to idle)
      end else begin
        // CPHA=1: first edge shifts data out, second edge samples data
        vif.sclk = ~cpol;  // first edge
        vif.mosi = tx_data[bit_idx];
        wait_half_sclk();
        vif.sclk = cpol;   // second edge
        wait_half_sclk();
        rx_data[bit_idx] = vif.miso;
      end
    end

    wait_half_sclk();
    vif.cs_n = 1'b1;
    vif.mosi = 1'b0;

    $display("[%0t] %s TX=%h RX=%h (CPOL=%0b CPHA=%0b)", $time, vip_name, tx_data, rx_data, cpol, cpha);
  endtask

endclass
