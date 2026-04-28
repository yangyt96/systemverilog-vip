# SPI VIP

## Overview

`spi_vip` is a lightweight SPI Verification IP written with SystemVerilog
classes and verified with VUnit. It follows the same direct VIP-to-VIP style as
`uart_vip`, so the master and slave VIPs can be connected through a shared SPI
interface without a DUT.

The VIP currently includes:

- A four-wire SPI interface: `sclk`, `cs_n`, `mosi`, and `miso`
- A master VIP with `send_recv`
- A slave VIP with `send_recv`
- Configurable CPOL and CPHA for all SPI modes (0-3)
- MSB-first full-duplex transfers
- Transaction timeout protection
- Transaction logging to the simulator CLI
- A VUnit testbench with single, continuous, and CS abort coverage

## Folder Structure

```text
spi_vip/
├── doc/
│   └── README.md
├── sim/
│   ├── spi_if.sv
│   ├── spi_master_vip.sv
│   ├── spi_slave_vip.sv
│   └── spi_vip_pkg.sv
├── tb/
│   ├── spi_vip_tb.do
│   ├── spi_vip_tb.sv
│   └── run.py
```

## Main Components

### `spi_if.sv`

Defines the shared SPI signals and modports:

- `master`: drives `sclk`, `cs_n`, and `mosi`; samples `miso`
- `slave`: samples `sclk`, `cs_n`, and `mosi`; drives `miso`

### `SpiMasterVIP`

The master VIP controls chip select and serial clock.

**Parameters:**

| Parameter | Description | Valid Range |
|-----------|-------------|-------------|
| `DATA_BITS` | Number of data bits per transfer | > 0 |
| `CPOL` | Clock polarity (0=idle low, 1=idle high) | 0 or 1 |
| `CPHA` | Clock phase (0=leading edge, 1=trailing edge) | 0 or 1 |

**Main API:**

```systemverilog
master_vip.send_recv(tx_data, rx_data);
```

**Configuration:**

```systemverilog
master_vip.configure_pause_generator(enable, min_cycles, max_cycles);
master_vip.configure_timeout(cycles);
```

### `SpiSlaveVIP`

The slave VIP waits for `cs_n` assertion, samples `mosi`, and shifts response
data on `miso`.

**Parameters:**

| Parameter | Description | Valid Range |
|-----------|-------------|-------------|
| `DATA_BITS` | Number of data bits per transfer | > 0 |
| `CPOL` | Clock polarity | 0 or 1 |
| `CPHA` | Clock phase | 0 or 1 |

**Main API:**

```systemverilog
slave_vip.send_recv(tx_data, rx_data);
```

**Configuration:**

```systemverilog
slave_vip.configure_timeout(cycles);
```

## Testbench Summary

Tests run for all 4 SPI mode combinations (CPOL=0/1 × CPHA=0/1):

| Test Case | Description |
|-----------|-------------|
| **SingleTransfers** | 8 single transfers with inter-transfer gap |
| **ContinuousTransfers** | 16 back-to-back transfers without gap |
| **CSAbortMidTransfer** | CS de-asserted mid-transfer, verify slave detects abort |

## Running the Simulation

From the project root:

```bash
make test-spi_vip          # Using Makefile (recommended)
python3 spi_vip/tb/run.py  # Using Python directly
```

With the provided Docker image:

```bash
docker run --rm -v "$PWD":/work -w /work/spi_vip/tb modelsim:20.1 python3 run.py
```
