class UartRxVIP #(
    int CLKS_PER_BIT = 16,
    int DATA_BITS    = 8
);

  virtual uart_if.receiver vif;
  string vip_name;
  int unsigned timeout_cycles;

  function new(virtual uart_if.receiver vif, string vip_name = "uart_rx_vip");
    this.vif = vif;
    this.vip_name = vip_name;
    timeout_cycles = 10000;
  endfunction

  function void configure_timeout(int unsigned cycles);
    timeout_cycles = cycles;
  endfunction

  task automatic wait_clocks(input int unsigned cycles);
    repeat (cycles) @(posedge vif.clk);
  endtask

  task automatic wait_reset_release();
    int unsigned cycles;
    cycles = 0;
    while (!vif.rstn) begin
      @(posedge vif.clk);
      cycles++;
      if (cycles >= timeout_cycles) begin
        $fatal(1, "%s timed out waiting for UART reset release", vip_name);
      end
    end
  endtask

  // API: receive one UART frame, 8N1 by default, LSB first.
  task receive(output logic [DATA_BITS-1:0] data, output bit framing_error);
    data = '0;
    framing_error = 1'b0;

    wait_reset_release();

    begin
      int unsigned cycles;
      cycles = 0;
      while (vif.tx !== 1'b1) begin
        @(posedge vif.clk);
        cycles++;
        if (cycles >= timeout_cycles) begin
          $fatal(1, "%s timed out waiting for UART idle", vip_name);
        end
      end

      cycles = 0;
      while (vif.tx !== 1'b0) begin
        @(posedge vif.clk);
        cycles++;
        if (cycles >= timeout_cycles) begin
          $fatal(1, "%s timed out waiting for UART start bit", vip_name);
        end
      end
    end

    wait_clocks(CLKS_PER_BIT / 2);
    if (vif.tx !== 1'b0) begin
      framing_error = 1'b1;
    end

    for (int bit_idx = 0; bit_idx < DATA_BITS; bit_idx++) begin
      wait_clocks(CLKS_PER_BIT);
      data[bit_idx] = vif.tx;
    end

    wait_clocks(CLKS_PER_BIT);
    if (vif.tx !== 1'b1) begin
      framing_error = 1'b1;
    end

    $display("[%0t] %s RX data=%h framing_error=%0b", $time, vip_name, data, framing_error);
  endtask

endclass
