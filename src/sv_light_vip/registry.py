"""VIP registry — maps VIP names to their source files and metadata.

This module defines the canonical list of all VIPs in sv-light-vip,
their source files, parameters, and interface signals. It is used by:

- `vunit_helper.py` — to add VIP sources to a VUnit project
- `mcp_server/server.py` — to provide AI query tools
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class VipSourceFile:
    """A single source file belonging to a VIP."""

    path: str  # Relative to the VIP's sim/ directory
    is_package: bool = False
    is_interface: bool = False
    is_hw_module: bool = False


@dataclass
class VipComponent:
    """A component within a VIP (master, slave, etc.)."""

    name: str
    type: str  # "class" or "hw_module"
    source_file: str
    description: str = ""


@dataclass
class VipParameter:
    """A parameter of a VIP component."""

    name: str
    type: str = "int"
    default: str = ""
    description: str = ""
    valid_range: str = ""


@dataclass
class VipInfo:
    """Complete information about a VIP."""

    name: str
    protocol: str
    description: str
    components: List[VipComponent]
    source_files: List[VipSourceFile]
    parameters: List[VipParameter] = field(default_factory=list)
    interface_signals: List[dict] = field(default_factory=list)
    has_mem_vip: bool = False
    has_class_slave: bool = False


# ---------------------------------------------------------------------------
# VIP registry — canonical data
# ---------------------------------------------------------------------------

_VIPS: dict = {}


def _register(vip: VipInfo) -> None:
    _VIPS[vip.name] = vip


def _rel(path: str) -> str:
    """Return a path relative to the repo root (for internal use)."""
    return path


_register(
    VipInfo(
        name="apb_vip",
        protocol="APB",
        description="AMBA APB master/slave verification IP",
        components=[
            VipComponent(
                "ApbMasterVIP",
                "class",
                "apb_master_vip.sv",
                "Blocking write/read with pause generator",
            ),
            VipComponent(
                "ApbSlaveVIP",
                "class",
                "apb_slave_vip.sv",
                "Configurable PREADY backpressure and PSLVERR injection",
            ),
            VipComponent(
                "apb_mem_vip",
                "hw_module",
                "apb_mem_vip.sv",
                "Synthesizable APB slave with byte-addressed storage",
            ),
        ],
        source_files=[
            VipSourceFile("apb_if.sv", is_interface=True),
            VipSourceFile("apb_master_vip.sv"),
            VipSourceFile("apb_slave_vip.sv"),
            VipSourceFile("apb_vip_pkg.sv", is_package=True),
        ],
        parameters=[
            VipParameter("ADDR_WIDTH", "int", "16", "Address bus width"),
            VipParameter("DATA_WIDTH", "int", "32", "Data bus width"),
        ],
        has_mem_vip=True,
        has_class_slave=True,
    )
)

_register(
    VipInfo(
        name="axi4_lite_vip",
        protocol="AXI4-Lite",
        description="AXI4-Lite master + memory slave verification IP",
        components=[
            VipComponent(
                "Axi4LiteMasterVIP",
                "class",
                "axi4_lite_master_vip.sv",
                "High-level and channel-level APIs with pause generator",
            ),
            VipComponent(
                "Axi4LiteSlaveVIP",
                "class",
                "axi4_lite_slave_vip.sv",
                "Configurable backpressure on all channels",
            ),
            VipComponent(
                "axi4_lite_mem_vip",
                "hw_module",
                "axi4_lite_mem_vip.sv",
                "Synthesizable AXI4-Lite slave with byte strobes",
            ),
        ],
        source_files=[
            VipSourceFile("axi4_lite_if.sv", is_interface=True),
            VipSourceFile("axi4_lite_master_vip.sv"),
            VipSourceFile("axi4_lite_slave_vip.sv"),
            VipSourceFile("axi4_lite_vip_pkg.sv", is_package=True),
        ],
        parameters=[
            VipParameter("ADDR_WIDTH", "int", "32", "Address bus width"),
            VipParameter("DATA_WIDTH", "int", "32", "Data bus width"),
        ],
        has_mem_vip=True,
        has_class_slave=True,
    )
)

_register(
    VipInfo(
        name="axi4_full_vip",
        protocol="AXI4-Full",
        description="AXI4-Full master + burst slave verification IP",
        components=[
            VipComponent(
                "Axi4FullMasterVIP",
                "class",
                "axi4_full_master_vip.sv",
                "Single/burst transactions, channel-level APIs",
            ),
            VipComponent(
                "Axi4FullSlaveVIP",
                "class",
                "axi4_full_slave_vip.sv",
                "Configurable backpressure on all channels",
            ),
            VipComponent(
                "axi4_full_mem_vip",
                "hw_module",
                "axi4_full_mem_vip.sv",
                "Synthesizable AXI4-Full slave with burst address progression",
            ),
        ],
        source_files=[
            VipSourceFile("axi4_full_if.sv", is_interface=True),
            VipSourceFile("axi4_full_master_vip.sv"),
            VipSourceFile("axi4_full_slave_vip.sv"),
            VipSourceFile("axi4_full_vip_pkg.sv", is_package=True),
        ],
        parameters=[
            VipParameter("ID_WIDTH", "int", "4", "ID bus width"),
            VipParameter("ADDR_WIDTH", "int", "32", "Address bus width"),
            VipParameter("DATA_WIDTH", "int", "32", "Data bus width"),
        ],
        has_mem_vip=True,
        has_class_slave=True,
    )
)

_register(
    VipInfo(
        name="axi4_stream_vip",
        protocol="AXI4-Stream",
        description="AXI4-Stream master/slave verification IP",
        components=[
            VipComponent(
                "Axi4StreamMasterVIP",
                "class",
                "axi4_stream_master_vip.sv",
                "Transmit with pause generator",
            ),
            VipComponent(
                "Axi4StreamSlaveVIP",
                "class",
                "axi4_stream_slave_vip.sv",
                "Receive with backpressure",
            ),
        ],
        source_files=[
            VipSourceFile("axi4_stream_if.sv", is_interface=True),
            VipSourceFile("axi4_stream_master_vip.sv"),
            VipSourceFile("axi4_stream_slave_vip.sv"),
            VipSourceFile("axi4_stream_vip_pkg.sv", is_package=True),
        ],
        parameters=[
            VipParameter("DATA_WIDTH", "int", "64", "Data bus width"),
            VipParameter("KEEP_WIDTH", "int", "8", "TKEEP width (= DATA_WIDTH/8)"),
        ],
        has_class_slave=True,
    )
)

_register(
    VipInfo(
        name="uart_vip",
        protocol="UART",
        description="UART transmitter/receiver verification IP (8N1)",
        components=[
            VipComponent(
                "UartTxVIP",
                "class",
                "uart_tx_vip.sv",
                "Transmitter with configurable baud rate and parity",
            ),
            VipComponent(
                "UartRxVIP",
                "class",
                "uart_rx_vip.sv",
                "Receiver with framing error detection",
            ),
        ],
        source_files=[
            VipSourceFile("uart_if.sv", is_interface=True),
            VipSourceFile("uart_tx_vip.sv"),
            VipSourceFile("uart_rx_vip.sv"),
            VipSourceFile("uart_vip_pkg.sv", is_package=True),
        ],
        parameters=[
            VipParameter(
                "CLKS_PER_BIT", "int", "8", "Clock cycles per UART bit period", ">= 4"
            ),
            VipParameter(
                "PARITY_MODE",
                "int",
                "0",
                "Parity configuration",
                "0=none, 1=odd, 2=even",
            ),
        ],
    )
)

_register(
    VipInfo(
        name="spi_vip",
        protocol="SPI",
        description="SPI master/slave verification IP",
        components=[
            VipComponent(
                "SpiMasterVIP",
                "class",
                "spi_master_vip.sv",
                "Full-duplex with configurable CPOL/CPHA",
            ),
            VipComponent(
                "SpiSlaveVIP", "class", "spi_slave_vip.sv", "Full-duplex slave"
            ),
        ],
        source_files=[
            VipSourceFile("spi_if.sv", is_interface=True),
            VipSourceFile("spi_master_vip.sv"),
            VipSourceFile("spi_slave_vip.sv"),
            VipSourceFile("spi_vip_pkg.sv", is_package=True),
        ],
        parameters=[
            VipParameter(
                "DATA_BITS", "int", "8", "Number of data bits per transfer", "> 0"
            ),
            VipParameter("CPOL", "int", "0", "Clock polarity", "0 or 1"),
            VipParameter("CPHA", "int", "0", "Clock phase", "0 or 1"),
        ],
    )
)

_register(
    VipInfo(
        name="i2c_vip",
        protocol="I2C",
        description="I2C master/slave verification IP",
        components=[
            VipComponent(
                "I2CMasterVIP",
                "class",
                "i2c_master_vip.sv",
                "7-bit addressing, ACK/NACK, clock stretching",
            ),
            VipComponent(
                "I2CSlaveVIP",
                "class",
                "i2c_slave_vip.sv",
                "Address match, clock stretching, bus contention",
            ),
        ],
        source_files=[
            VipSourceFile("i2c_if.sv", is_interface=True),
            VipSourceFile("i2c_master_vip.sv"),
            VipSourceFile("i2c_slave_vip.sv"),
            VipSourceFile("i2c_vip_pkg.sv", is_package=True),
        ],
        parameters=[
            VipParameter(
                "HALF_SCL_CYCLES",
                "int",
                "25",
                "Clock cycles for half SCL period",
                "> 0",
            ),
        ],
        has_class_slave=True,
    )
)

_register(
    VipInfo(
        name="i2s_vip",
        protocol="I2S",
        description="I2S stereo transmitter/receiver verification IP",
        components=[
            VipComponent(
                "I2STxVIP", "class", "i2s_tx_vip.sv", "Stereo frame transmitter"
            ),
            VipComponent(
                "I2SRxVIP",
                "class",
                "i2s_rx_vip.sv",
                "Stereo frame receiver with frame error detection",
            ),
        ],
        source_files=[
            VipSourceFile("i2s_if.sv", is_interface=True),
            VipSourceFile("i2s_tx_vip.sv"),
            VipSourceFile("i2s_rx_vip.sv"),
            VipSourceFile("i2s_vip_pkg.sv", is_package=True),
        ],
        parameters=[
            VipParameter(
                "SAMPLE_WIDTH", "int", "16", "Audio sample width in bits", "> 0"
            ),
        ],
    )
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def list_vips() -> List[VipInfo]:
    """Return sorted list of all registered VIPs as VipInfo objects."""
    return [_VIPS[name] for name in sorted(_VIPS.keys())]


def get_vip_info(name: str) -> Optional[VipInfo]:
    """Return VipInfo for the given VIP name, or None if not found."""
    return _VIPS.get(name)


def get_vip_path(name: str) -> Optional[str]:
    """Return the absolute path to the VIP's root directory.

    Resolution order:
    1. SV_LIGHT_VIP_ROOT environment variable (overrides auto-detection)
    2. Auto-detect from this file's location (../../<vip_name>)
    """
    override = os.environ.get("SV_LIGHT_VIP_ROOT")
    if override:
        base = override
    else:
        base = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )

    path = os.path.join(base, name)
    if os.path.isdir(path):
        return path
    return None


def get_vip_sim_path(name: str) -> Optional[str]:
    """Return the absolute path to the VIP's sim/ directory."""
    vip_path = get_vip_path(name)
    if vip_path is None:
        return None
    sim_path = os.path.join(vip_path, "sim")
    return sim_path if os.path.isdir(sim_path) else None
