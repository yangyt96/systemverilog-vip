# UART VIP

## Overview

`uart_vip` is a lightweight UART Verification IP written with SystemVerilog
classes and verified with VUnit. It follows the same class-based style as
`axi4_stream_vip`, but the transmitter and receiver can be connected directly
through a UART interface without a DUT.

The VIP currently includes:

- A single-wire UART interface
- A transmitter VIP with `send_frame`
- A receiver VIP with `recv_frame`
- 8N1 frame support, LSB first
- Configurable baud rate via `CLKS_PER_BIT` parameter
- Configurable parity (none/odd/even) via `PARITY_MODE` parameter
- Transaction timeout protection
- Transaction logging to the simulator CLI
- A VUnit testbench with single frame, continuous frame, and parity coverage

## Folder Structure

```text
uart_vip/
├── doc/
│   └── README.md
├── sim/
│   ├── uart_if.sv
│   ├── uart_rx_vip.sv
│   ├── uart_tx_vip.sv
│   └── uart_vip_pkg.sv
├── tb/
│   ├── uart_vip_tb.do
│   ├── uart_vip_tb.sv
│   └── run.py
```

## Main Components

### `uart_if.sv`

Defines the shared UART serial line and modports:

- `transmitter`: drives `tx`
- `receiver`: samples `tx`

The UART line is idle high.

### `UartTxVIP`

The transmitter VIP is a class-based UART source.

**Parameters:**

| Parameter | Description | Valid Range |
|-----------|-------------|-------------|
| `CLKS_PER_BIT` | Clock cycles per UART bit period | >= 4 |
| `PARITY_MODE` | Parity configuration | 0=none, 1=odd, 2=even |

**Main API:**

```systemverilog
tx_vip.send_frame(data);
```

**Configuration:**

```systemverilog
tx_vip.configure_pause_generator(enable, min_cycles, max_cycles);
tx_vip.configure_timeout(cycles);
```

### `UartRxVIP`

The receiver VIP is a class-based UART sink.

**Parameters:**

| Parameter | Description | Valid Range |
|-----------|-------------|-------------|
| `CLKS_PER_BIT` | Clock cycles per UART bit period | >= 4 |
| `PARITY_MODE` | Parity configuration | 0=none, 1=odd, 2=even |

**Main API:**

```systemverilog
rx_vip.recv_frame(data, framing_error);
```

**Configuration:**

```systemverilog
rx_vip.configure_timeout(cycles);
```

The receiver waits for a start bit, samples each data bit in the middle of the
bit period, and reports a framing error if the start or stop bit is invalid.

Basic UART has no ready/valid handshake, so this receiver does not provide
backpressure. Hardware flow control such as RTS/CTS can be modeled as an
optional extension if needed.

## Testbench Summary

| Test Case | Description |
|-----------|-------------|
| **SingleFrames** | 8 single frames with inter-frame gap |
| **ContinuousFrames** | 16 back-to-back frames without gap |
| **OddParity** | 8 frames with odd parity |
| **EvenParity** | 8 frames with even parity |

## Running the Simulation

From the project root:

```bash
make test-uart_vip          # Using Makefile (recommended)
python3 uart_vip/tb/run.py  # Using Python directly
```

With the provided Docker image:

```bash
docker run --rm -v "$PWD":/work -w /work/uart_vip/tb modelsim:20.1 python3 run.py
```
