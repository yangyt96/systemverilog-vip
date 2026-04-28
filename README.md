# sv-light-vip
**Lightweight, class‑based SystemVerilog Verification IPs (UVM‑free)**


## 🚀 Lightweight SystemVerilog Verification IPs
**Pure SystemVerilog • Class‑Based • UVM‑Free • VUnit‑Ready • ModelSim‑Friendly**

This repository provides a collection of **lightweight, class‑based SystemVerilog Verification IPs (VIPs)** designed for engineers who want reusable, protocol‑accurate verification components **without the overhead of UVM**.

Each VIP is intentionally small, readable, and self‑contained. The structure is consistent across all protocols:

- `sim/` — reusable interfaces, transaction classes, drivers, monitors, scoreboards
- `tb/` — self‑checking bring‑up testbenches with VUnit integration
- `doc/` — protocol‑specific notes and diagrams

Every VIP includes its own `tb/run.py`, keeping compile order explicit and avoiding hidden dependencies.

---

## 🧭 Motivation

Most open‑source verification resources fall into two extremes:

- **Heavy UVM frameworks** that require complex infrastructure and commercial simulators
- **Minimal BFMs** that lack structure, reuse, and realistic protocol behavior

This project fills the gap by providing:

- **Pure SystemVerilog, class‑based VIPs**
- **No UVM, no factories, no phases**
- **Accurate protocol behavior** for AXI, APB, UART, SPI, I2C, I2S
- **VUnit + ModelSim ASE compatibility**
- **Readable, hackable, and easy to integrate**

The goal is to offer a practical, modern, open‑source VIP suite that works for FPGA/ASIC bring‑up, education, and small/medium verification environments.

---

## 📦 Supported VIPs

| VIP | Description | Components | Features |
|-----|-------------|------------|----------|
| **apb_vip** | AMBA APB master/slave | Master VIP, Slave VIP, Mem VIP (hw) | Blocking write/read, PREADY backpressure, PSLVERR injection, byte strobes, pause generator |
| **axi4_lite_vip** | AXI4‑Lite master + memory slave | Master VIP, Mem VIP (hw) | Blocking write/read, byte strobes, pause generator |
| **axi4_full_vip** | AXI4‑Full master + burst slave | Master VIP, Slave VIP, Mem VIP (hw) | Single/burst transactions, channel-level APIs, FIXED/INCR/WRAP bursts, byte strobes, backpressure, pause generator |
| **axi4_stream_vip** | AXI4‑Stream master/slave | Master VIP, Slave VIP, DUT | Transmit/receive, TUSER/TID/TDEST/TKEEP/TSTRB, backpressure, pause generator |
| **uart_vip** | UART TX/RX (8N1) | Transmitter VIP, Receiver VIP | Configurable baud rate, parity (none/odd/even), framing error detection |
| **spi_vip** | SPI master/slave | Master VIP, Slave VIP | Full-duplex, configurable CPOL/CPHA, CS abort test |
| **i2c_vip** | I2C master/slave | Master VIP, Slave VIP | 7-bit addressing, ACK/NACK, clock stretching, bus contention detection |
| **i2s_vip** | I2S stereo TX/RX | Transmitter VIP, Receiver VIP | Stereo frames (L/R), configurable sample width |

All VIPs follow the same structure and coding style for consistency. See [`API_REFERENCE.md`](API_REFERENCE.md) for detailed API documentation.

---

## 🧪 Running Regressions

### Using Makefile (recommended)

```bash
make test              # Run all VIPs (Docker)
make test-apb_vip      # Run a single VIP
make test-axi4_full_vip
make list              # List available VIPs
make lint              # Run Verible lint
make format            # Run Verible format
make format-check      # Check formatting only
make clean             # Clean all simulation outputs
```

Run locally (without Docker):

```bash
DOCKER=0 make test
DOCKER=0 make test-apb_vip
```

### Using Python scripts directly

```bash
python3 run_all.py                          # Run all VIPs
python3 run_all.py --list                   # List available VIPs
python3 run_all.py --gui                    # Run with ModelSim GUI
python3 <vip_name>/tb/run.py                # Run a single VIP
```

## 🐳 Docker Environment

A ready‑to‑use ModelSim ASE Docker image is available:

```text
https://github.com/yangyt96/docker-hdl-images/blob/master/modelsim-image/Dockerfile.modelsim
```

The Makefile uses Docker by default (`DOCKER=1`). Set `DOCKER=0` to run tools locally.

## 🖥️ ModelSim GUI (via Docker)

```bash
xhost +local:docker
docker run -it --rm \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v "$PWD":/work \
  -w /work \
  modelsim:20.1
```

## 🧩 Project Philosophy
Human‑designed, AI‑assisted: AI tools were used to accelerate boilerplate and documentation, but all protocol behavior, architecture, and verification methodology are manually reviewed and engineered.

Lightweight by design: No UVM, no unnecessary abstraction layers.

Readable and educational: Suitable for learning, teaching, and real bring‑up.

## 📜 License
This project is open‑source and available under the MIT license.
