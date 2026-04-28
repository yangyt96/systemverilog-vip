# I2C VIP

## Overview

`i2c_vip` is a lightweight I2C Verification IP written with SystemVerilog
classes and verified with VUnit. It follows the same direct VIP-to-VIP style as
`uart_vip` and `spi_vip`, so the master and slave VIPs can be connected through
a shared I2C interface without a DUT.

The VIP currently includes:

- An open-drain I2C interface with resolved `scl` and `sda`
- A master VIP with single-byte `write_byte` and `read_byte` APIs
- A slave VIP with matching `expect_write` and `respond_read` APIs
- 7-bit addressing
- ACK/NACK checking
- Wrong-address NACK checking
- Bus contention detection (SVA assertions on SDA conflicts)
- Clock stretching support
- Transaction timeout protection
- Transaction logging to the simulator CLI
- A VUnit testbench with write, read, continuous read, clock stretching, and bus contention coverage

## Folder Structure

```text
i2c_vip/
├── doc/
│   └── README.md
├── sim/
│   ├── i2c_if.sv
│   ├── i2c_master_vip.sv
│   ├── i2c_slave_vip.sv
│   └── i2c_vip_pkg.sv
├── tb/
│   ├── i2c_vip_tb.do
│   ├── i2c_vip_tb.sv
│   └── run.py
```

## Main Components

### `i2c_if.sv`

Defines the shared open-drain I2C bus:

- `scl` and `sda` are resolved with pull-up behavior
- The master and slave each expose low-drive control signals
- Includes SVA assertions for bus contention detection

### `I2CMasterVIP`

The master VIP generates start and stop conditions, serializes the 7-bit
address plus R/W bit, and checks ACK/NACK.

**Parameters:**

| Parameter | Description | Valid Range |
|-----------|-------------|-------------|
| `HALF_SCL_CYCLES` | Clock cycles for half SCL period | > 0 |

**Main APIs:**

```systemverilog
master_vip.write_byte(address, data, address_ack, data_ack);
master_vip.read_byte(address, data, address_ack);
```

**Configuration:**

```systemverilog
master_vip.configure_timeout(cycles);
```

### `I2CSlaveVIP`

The slave VIP waits for a start condition and responds when the address and R/W
bit match its configured address.

**Main APIs:**

```systemverilog
slave_vip.expect_write(data, address_match);
slave_vip.respond_read(data, address_match, master_ack);
```

**Configuration:**

```systemverilog
slave_vip.configure_timeout(cycles);
```

## Testbench Summary

| Test Case | Description |
|-----------|-------------|
| **WriteRead** | Write 8 bytes then read 8 bytes |
| **WrongAddressNack** | Write to wrong address, expect NACK |
| **ContinuousRead** | Read 16 bytes continuously |
| **ClockStretchWrite** | Slave stretches SCL during write |
| **ClockStretchRead** | Slave stretches SCL during read |
| **ClockStretchMultiByte** | Slave stretches SCL across multi-byte transfer |
| **ClockStretchEdgeCases** | Stretch at start, mid-byte, and stop conditions |

## Running the Simulation

From the project root:

```bash
python3 i2c_vip/tb/run.py
```

With the provided Docker image:

```bash
docker run --rm -v "$PWD":/work -w /work/i2c_vip/tb modelsim:20.1 python3 run.py
```
