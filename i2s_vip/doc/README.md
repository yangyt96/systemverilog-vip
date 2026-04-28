# I2S VIP

## Overview

`i2s_vip` is a lightweight I2S Verification IP written with SystemVerilog
classes and verified with VUnit. It follows the direct VIP-to-VIP style used by
`uart_vip`, `spi_vip`, and `i2c_vip`.

The VIP currently includes:

- A three-wire I2S interface: `bclk`, `ws`, and `sd`
- A transmitter VIP with `send_frame`
- A receiver VIP with `recv_frame`
- Stereo frame support with `WS=0` for left and `WS=1` for right
- MSB-first sample transfer with one I2S lead bit before each channel MSB
- Configurable sample width via `SAMPLE_WIDTH` parameter
- Transaction timeout protection
- A self-checking VUnit testbench and ModelSim waveform setup

## Folder Structure

```text
i2s_vip/
├── doc/
│   └── README.md
├── sim/
│   ├── i2s_if.sv
│   ├── i2s_rx_vip.sv
│   ├── i2s_tx_vip.sv
│   └── i2s_vip_pkg.sv
├── tb/
│   ├── i2s_vip_tb.do
│   ├── i2s_vip_tb.sv
│   └── run.py
```

## Main Components

### `I2STxVIP`

**Parameters:**

| Parameter | Description | Valid Range |
|-----------|-------------|-------------|
| `SAMPLE_WIDTH` | Audio sample width in bits | > 0 |

**Main API:**

```systemverilog
tx_vip.send_frame(left_sample, right_sample);
```

**Configuration:**

```systemverilog
tx_vip.configure_pause_generator(enable, min_cycles, max_cycles);
tx_vip.configure_timeout(cycles);
```

### `I2SRxVIP`

**Parameters:**

| Parameter | Description | Valid Range |
|-----------|-------------|-------------|
| `SAMPLE_WIDTH` | Audio sample width in bits | > 0 |

**Main API:**

```systemverilog
rx_vip.recv_frame(left_sample, right_sample, frame_error);
```

**Configuration:**

```systemverilog
rx_vip.configure_timeout(cycles);
```

## Testbench Summary

| Test Case | Description |
|-----------|-------------|
| **BasicTransmitReceive** | Transmit 4 stereo frames, verify reception |
| **PauseBetweenFrames** | Transmit with pause generator, verify receiver matches |
| **DifferentSampleValues** | Test various sample values (min, max, alternating) |
| **MultipleFrames** | 16 continuous frames without gap |

## Running the Simulation

From the project root:

```bash
make test-i2s_vip          # Using Makefile (recommended)
python3 i2s_vip/tb/run.py  # Using Python directly
```

With Docker:

```bash
docker run --rm -v "$PWD":/work -w /work/i2s_vip/tb modelsim:20.1 python3 run.py
```
