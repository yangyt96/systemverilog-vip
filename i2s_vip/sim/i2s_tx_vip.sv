class I2STxVIP #(
  int SAMPLE_WIDTH = 16,
  int HALF_BCLK_CYCLES = 4
);

  virtual i2s_if.transmitter vif;
  string vip_name;

  function new(virtual i2s_if.transmitter vif,
               string vip_name = "i2s_tx_vip");
    this.vif = vif;
    this.vip_name = vip_name;
  endfunction

  task automatic idle();
    vif.bclk = 1'b0;
    vif.ws   = 1'b0;
    vif.sd   = 1'b0;
  endtask

  task automatic wait_half_bclk();
    repeat (HALF_BCLK_CYCLES) @(posedge vif.clk);
  endtask

  task automatic drive_bit(input bit value);
    vif.sd = value;
    wait_half_bclk();
    vif.bclk = 1'b1;
    wait_half_bclk();
    vif.bclk = 1'b0;
  endtask

  // API: transmit one stereo I2S frame, MSB first.
  // WS=0 is left, WS=1 is right. Each channel has one lead bit before the MSB.
  task automatic transmit(input logic [SAMPLE_WIDTH-1:0] left_sample,
                           input logic [SAMPLE_WIDTH-1:0] right_sample);
    while (!vif.rstn) @(posedge vif.clk);
    @(posedge vif.clk);

    vif.ws = 1'b0;
    drive_bit(1'b0);
    for (int bit_idx = SAMPLE_WIDTH - 1; bit_idx >= 0; bit_idx--) begin
      drive_bit(left_sample[bit_idx]);
    end

    vif.ws = 1'b1;
    drive_bit(1'b0);
    for (int bit_idx = SAMPLE_WIDTH - 1; bit_idx >= 0; bit_idx--) begin
      drive_bit(right_sample[bit_idx]);
    end

    vif.ws = 1'b0;
    vif.sd = 1'b0;

    $display("[%0t] %s TX left=%h right=%h",
             $time, vip_name, left_sample, right_sample);
  endtask

endclass
