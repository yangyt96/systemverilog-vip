# APB VIP

## Overview

`apb_vip` is a lightweight AMBA APB Verification IP written with
SystemVerilog classes and verified with VUnit. It follows the direct
VIP-to-VIP style used by the serial VIPs in this repository.

The VIP currently includes:

- A parameterized APB interface ([`apb_if.sv`](sim/apb_if.sv))
- A master VIP with blocking `write` and `read` APIs ([`apb_master_vip.sv`](sim/apb_master_vip.sv))
- A slave VIP with `expect_write` and `respond_read` APIs ([`apb_slave_vip.sv`](sim/apb_slave_vip.sv))
  - Supports configurable `PREADY` delay and `PSLVERR` error injection
- A hardware memory slave VIP module ([`apb_mem_vip.sv`](sim/apb_mem_vip.sv))
  - Synthesizable APB slave with byte-addressed storage
  - Zero-wait-state response, supports `PSTRB` byte strobes

## Folder Structure

```text
apb_vip/
├── doc/
│   └── README.md
├── sim/
│   ├── apb_if.sv
│   ├── apb_master_vip.sv
│   ├── apb_mem_vip.sv          # Hardware memory slave module
│   ├── apb_slave_vip.sv
│   └── apb_vip_pkg.sv
├── tb/
│   ├── apb_vip_tb.do
│   ├── apb_vip_tb.sv           # Slave VIP testbench (software class)
│   ├── apb_mem_vip_tb.sv       # Mem VIP testbench (hardware module)
│   └── run.py
```

## Main APIs

### Master VIP (class-based)

```systemverilog
master_vip.write(addr, data, strb, slverr, prot);
master_vip.read(addr, data, slverr, prot);
```

**Configuration:**

```systemverilog
master_vip.configure_pause_generator(enable, min_cycles, max_cycles);
master_vip.configure_timeout(cycles);
```

### Slave VIP (class-based, software slave)

```systemverilog
slave_vip.expect_write(addr, data, strb, prot, slverr);
slave_vip.respond_read(read_data, addr, prot, slverr);
```

**Configuration:**

```systemverilog
slave_vip.configure_backpressure(enable, min_cycles, max_cycles);
slave_vip.configure_timeout(cycles);
```

### Memory VIP (hardware module, synthesizable)

The [`apb_mem_vip`](sim/apb_mem_vip.sv) module is a hardware APB slave that
provides byte-addressed memory storage. It connects directly to the APB
interface and handles read/write transactions automatically, without
requiring a software slave VIP.

```systemverilog
apb_mem_vip #(
    .ADDR_WIDTH(16),
    .DATA_WIDTH(32),
    .STRB_WIDTH(4),
    .MEM_BYTES (4096)
) mem_vip (
    .pclk    (clk),
    .presetn (rstn),
    .paddr   (apb_link.paddr),
    .psel    (apb_link.psel),
    .penable (apb_link.penable),
    .pwrite  (apb_link.pwrite),
    .pwdata  (apb_link.pwdata),
    .pstrb   (apb_link.pstrb),
    .pprot   (apb_link.pprot),
    .prdata  (apb_link.prdata),
    .pready  (apb_link.pready),
    .pslverr (apb_link.pslverr)
);
```

## Testbenches

Two separate testbenches are provided to avoid driver conflicts:

### [`apb_vip_tb.sv`](tb/apb_vip_tb.sv) — Slave VIP tests (software class)

| Test Case | Description |
|-----------|-------------|
| **Basic Write-Read** | 48 write-read pairs with zero ready delay |
| **Ready Delay Write-Read** | 8 write-read pairs with 3-cycle ready delay |
| **Error Response** | Write and read with `PSLVERR` error injection |
| **Backpressure Fixed Stall** | 8 write-read pairs with fixed 5-cycle PREADY stall |
| **Backpressure Random Stall** | 8 write-read pairs with random 1-10 cycle PREADY stall |
| **Backpressure Edge Cases** | Backpressure with min=0, max=0 (immediate ready) and max < min (clamped) |

### [`apb_mem_vip_tb.sv`](tb/apb_mem_vip_tb.sv) — Mem VIP tests (hardware module)

| Test Case | Description |
|-----------|-------------|
| **Mem VIP Write-Read** | Write 32 data words, read back and verify |
| **Mem VIP Write-Read with Strobe** | Write with varying `pstrb` patterns, verify masked read data |
| **Mem VIP Cross-Check** | Overwrite with different pattern, verify final value |
| **Mem VIP Boundary Access** | Test address boundaries (0, near MEM_BYTES end, wrapped address) |

## Running the Simulation

From the project root:

```bash
python3 apb_vip/tb/run.py
```

With Docker:

```bash
docker run --rm -v "$PWD":/work -w /work/apb_vip/tb modelsim:20.1 python3 run.py
```
