#!/usr/bin/env python3
"""MCP Server for sv-light-vip — AI agent integration.

This server exposes tools that allow AI coding assistants (Claude, Cursor, etc.)
to query VIP metadata, generate testbench code, and produce VUnit run scripts
for the sv-light-vip repository.

Usage:
    # Run with stdio transport (for AI integration):
    python mcp_server/server.py

    # Or with SSE transport (for web-based tools):
    python mcp_server/server.py --transport sse --port 8000

Requires:
    - mcp>=1.0.0  (pip install mcp)
    - sv-light-vip package installed (pip install -e .)
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any

# Ensure the repo root is on sys.path so we can import sv_light_vip
_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from sv_light_vip import (
    VipInfo,
    get_vip_info,
    get_vip_path,
    get_vip_sim_path,
    list_vips,
)

# ---------------------------------------------------------------------------
# MCP Server setup
# ---------------------------------------------------------------------------

try:
    from mcp.server import Server, NotificationOptions
    from mcp.server.models import InitializationOptions
    import mcp.server.stdio
    import mcp.types as types
except ImportError:
    print(
        "ERROR: 'mcp' package not found. Install with: pip install mcp", file=sys.stderr
    )
    sys.exit(1)

server = Server("sv-light-vip")


# ---------------------------------------------------------------------------
# Helper: VIP API database (extracted from source code)
# ---------------------------------------------------------------------------

_VIP_API: dict[str, dict[str, list[dict[str, str]]]] = {
    "apb_vip": {
        "ApbMasterVIP": [
            {
                "name": "new",
                "sig": "new(string name, virtual apb_if vif)",
                "desc": "Constructor",
            },
            {
                "name": "configure_pause_generator",
                "sig": "configure_pause_generator(bit enable, int unsigned min_cycles=0, int unsigned max_cycles=0)",
                "desc": "Enable/disable random pause between transactions",
            },
            {
                "name": "configure_timeout",
                "sig": "configure_timeout(int unsigned cycles)",
                "desc": "Set timeout cycle count",
            },
            {
                "name": "clear_outputs",
                "sig": "clear_outputs()",
                "desc": "Drive all output signals to default state",
            },
            {
                "name": "wait_reset_release",
                "sig": "wait_reset_release()",
                "desc": "Wait for reset de-assertion",
            },
            {
                "name": "apply_pause",
                "sig": "apply_pause()",
                "desc": "Apply random pause if enabled",
            },
            {
                "name": "wait_ready",
                "sig": "wait_ready()",
                "desc": "Wait for pready handshake",
            },
            {
                "name": "write_req",
                "sig": "write_req(logic [ADDR_WIDTH-1:0] addr, logic [DATA_WIDTH-1:0] data, logic [STRB_WIDTH-1:0] strb='1, output bit slverr, logic [PROT_WIDTH-1:0] prot='0)",
                "desc": "Blocking APB write transaction",
            },
            {
                "name": "read_req",
                "sig": "read_req(logic [ADDR_WIDTH-1:0] addr, output logic [DATA_WIDTH-1:0] data, output bit slverr, logic [PROT_WIDTH-1:0] prot='0)",
                "desc": "Blocking APB read transaction",
            },
        ],
        "ApbSlaveVIP": [
            {
                "name": "new",
                "sig": "new(string name, virtual apb_if vif)",
                "desc": "Constructor",
            },
            {
                "name": "configure_backpressure",
                "sig": "configure_backpressure(bit enable, int unsigned min_cycles=0, int unsigned max_cycles=0)",
                "desc": "Enable/random PREADY backpressure",
            },
            {
                "name": "configure_timeout",
                "sig": "configure_timeout(int unsigned cycles)",
                "desc": "Set timeout cycle count",
            },
            {
                "name": "clear_outputs",
                "sig": "clear_outputs()",
                "desc": "Drive all output signals to default state",
            },
            {
                "name": "wait_reset_release",
                "sig": "wait_reset_release()",
                "desc": "Wait for reset de-assertion",
            },
            {
                "name": "wait_access",
                "sig": "wait_access(bit expect_write)",
                "desc": "Wait for PENABLE=1, detect direction",
            },
            {
                "name": "write_resp",
                "sig": "write_resp(output logic [ADDR_WIDTH-1:0] addr, output logic [DATA_WIDTH-1:0] data, output logic [STRB_WIDTH-1:0] strb, output logic [PROT_WIDTH-1:0] prot, input bit slverr=0)",
                "desc": "Respond to APB write (capture address/data)",
            },
            {
                "name": "read_resp",
                "sig": "read_resp(logic [DATA_WIDTH-1:0] read_data, output logic [ADDR_WIDTH-1:0] addr, output logic [PROT_WIDTH-1:0] prot, input bit slverr=0)",
                "desc": "Respond to APB read (provide data)",
            },
        ],
        "apb_mem_vip": [
            {
                "name": "write_word",
                "sig": "write_word(logic [ADDR_WIDTH-1:0] addr, logic [DATA_WIDTH-1:0] data, logic [STRB_WIDTH-1:0] strb)",
                "desc": "Write to byte-addressed memory with strobes",
            },
        ],
    },
    "axi4_lite_vip": {
        "Axi4LiteMasterVIP": [
            {
                "name": "new",
                "sig": "new(string name, virtual axi4_lite_if vif)",
                "desc": "Constructor",
            },
            {
                "name": "configure_pause_generator",
                "sig": "configure_pause_generator(bit enable, int unsigned min_cycles=0, int unsigned max_cycles=0)",
                "desc": "Enable/disable random pause between transactions",
            },
            {
                "name": "configure_timeout",
                "sig": "configure_timeout(int unsigned cycles)",
                "desc": "Set timeout cycle count",
            },
            {
                "name": "clear_outputs",
                "sig": "clear_outputs()",
                "desc": "Drive all output signals to default state",
            },
            {
                "name": "wait_reset_release",
                "sig": "wait_reset_release()",
                "desc": "Wait for reset de-assertion",
            },
            {
                "name": "apply_pause",
                "sig": "apply_pause()",
                "desc": "Apply random pause if enabled",
            },
            {
                "name": "send_awchn",
                "sig": "send_awchn(logic [ADDR_WIDTH-1:0] addr, logic [2:0] prot='b000)",
                "desc": "Send write address channel",
            },
            {
                "name": "send_wchn",
                "sig": "send_wchn(logic [DATA_WIDTH-1:0] data, logic [STRB_WIDTH-1:0] strb='1)",
                "desc": "Send write data channel",
            },
            {
                "name": "recv_bchn",
                "sig": "recv_bchn(output logic [1:0] resp)",
                "desc": "Receive write response channel",
            },
            {
                "name": "send_archn",
                "sig": "send_archn(logic [ADDR_WIDTH-1:0] addr, logic [2:0] prot='b000)",
                "desc": "Send read address channel",
            },
            {
                "name": "recv_rchn",
                "sig": "recv_rchn(output logic [DATA_WIDTH-1:0] data, output logic [1:0] resp)",
                "desc": "Receive read data channel",
            },
            {
                "name": "write_req_single",
                "sig": "write_req_single(logic [ADDR_WIDTH-1:0] addr, logic [DATA_WIDTH-1:0] data, logic [STRB_WIDTH-1:0] strb='1, output logic [1:0] resp)",
                "desc": "High-level single-beat write",
            },
            {
                "name": "read_req_single",
                "sig": "read_req_single(logic [ADDR_WIDTH-1:0] addr, output logic [DATA_WIDTH-1:0] data, output logic [1:0] resp)",
                "desc": "High-level single-beat read",
            },
        ],
        "Axi4LiteSlaveVIP": [
            {
                "name": "new",
                "sig": "new(string name, virtual axi4_lite_if vif)",
                "desc": "Constructor",
            },
            {
                "name": "configure_backpressure",
                "sig": "configure_backpressure(bit enable=0, int unsigned min_cycles=0, int unsigned max_cycles=0)",
                "desc": "Configure backpressure for all channels",
            },
            {
                "name": "configure_timeout",
                "sig": "configure_timeout(int unsigned cycles)",
                "desc": "Set timeout cycle count",
            },
            {
                "name": "clear_outputs",
                "sig": "clear_outputs()",
                "desc": "Drive all output signals to default state",
            },
            {
                "name": "wait_reset_release",
                "sig": "wait_reset_release()",
                "desc": "Wait for reset de-assertion",
            },
            {
                "name": "recv_awchn",
                "sig": "recv_awchn(output logic [ADDR_WIDTH-1:0] addr, output logic [2:0] prot)",
                "desc": "Receive write address channel",
            },
            {
                "name": "recv_wchn",
                "sig": "recv_wchn(output logic [DATA_WIDTH-1:0] data, output logic [STRB_WIDTH-1:0] strb)",
                "desc": "Receive write data channel",
            },
            {
                "name": "send_bchn",
                "sig": "send_bchn(logic [1:0] resp='b00)",
                "desc": "Send write response channel",
            },
            {
                "name": "write_resp_single",
                "sig": "write_resp_single(logic [DATA_WIDTH-1:0] data, logic [STRB_WIDTH-1:0] strb='1, logic [1:0] resp='b00)",
                "desc": "High-level single-beat write response",
            },
            {
                "name": "recv_archn",
                "sig": "recv_archn(output logic [ADDR_WIDTH-1:0] addr, output logic [2:0] prot)",
                "desc": "Receive read address channel",
            },
            {
                "name": "send_rchn",
                "sig": "send_rchn(logic [DATA_WIDTH-1:0] data, logic [1:0] resp='b00)",
                "desc": "Send read data channel",
            },
            {
                "name": "read_resp_single",
                "sig": "read_resp_single(logic [DATA_WIDTH-1:0] data, logic [1:0] resp='b00)",
                "desc": "High-level single-beat read response",
            },
        ],
        "axi4_lite_mem_vip": [
            {
                "name": "write_word",
                "sig": "write_word(logic [ADDR_WIDTH-1:0] addr, logic [DATA_WIDTH-1:0] data, logic [STRB_WIDTH-1:0] strb)",
                "desc": "Write to byte-addressed memory with strobes",
            },
        ],
    },
    "axi4_full_vip": {
        "Axi4FullMasterVIP": [
            {
                "name": "new",
                "sig": "new(string name, virtual axi4_full_if vif)",
                "desc": "Constructor",
            },
            {
                "name": "configure_pause_generator",
                "sig": "configure_pause_generator(bit enable, int unsigned min_cycles=0, int unsigned max_cycles=0)",
                "desc": "Enable/disable random pause between transactions",
            },
            {
                "name": "configure_timeout",
                "sig": "configure_timeout(int unsigned cycles)",
                "desc": "Set timeout cycle count",
            },
            {
                "name": "clear_outputs",
                "sig": "clear_outputs()",
                "desc": "Drive all output signals to default state",
            },
            {
                "name": "wait_reset_release",
                "sig": "wait_reset_release()",
                "desc": "Wait for reset de-assertion",
            },
            {
                "name": "apply_pause",
                "sig": "apply_pause()",
                "desc": "Apply random pause if enabled",
            },
            {
                "name": "send_awchn",
                "sig": "send_awchn(logic [ADDR_WIDTH-1:0] addr, int unsigned beat_count=1, logic [ID_WIDTH-1:0] id='0, logic [SIZE_WIDTH-1:0] size=$clog2(STRB_WIDTH), logic [BURST_WIDTH-1:0] burst='b01, ...)",
                "desc": "Send write address channel (burst-capable)",
            },
            {
                "name": "send_wchn",
                "sig": "send_wchn(logic [DATA_WIDTH-1:0] data, logic [STRB_WIDTH-1:0] strb, logic last, logic [WUSER_WIDTH-1:0] user='0)",
                "desc": "Send write data channel (single beat)",
            },
            {
                "name": "recv_bchn",
                "sig": "recv_bchn(output logic [1:0] resp, output logic [ID_WIDTH-1:0] id, output logic [BUSER_WIDTH-1:0] user)",
                "desc": "Receive write response channel",
            },
            {
                "name": "send_archn",
                "sig": "send_archn(logic [ADDR_WIDTH-1:0] addr, int unsigned beat_count=1, logic [ID_WIDTH-1:0] id='0, ...)",
                "desc": "Send read address channel (burst-capable)",
            },
            {
                "name": "recv_rchn",
                "sig": "recv_rchn(ref logic [DATA_WIDTH-1:0] data, ref logic [1:0] resp, ref logic [ID_WIDTH-1:0] id, ref logic last, ref logic [RUSER_WIDTH-1:0] user)",
                "desc": "Receive read data channel (single beat)",
            },
            {
                "name": "write_req_single",
                "sig": "write_req_single(logic [ADDR_WIDTH-1:0] addr, logic [DATA_WIDTH-1:0] data, logic [STRB_WIDTH-1:0] strb='1, logic [ID_WIDTH-1:0] id='0, output logic [1:0] resp)",
                "desc": "High-level single-beat write",
            },
            {
                "name": "read_req_single",
                "sig": "read_req_single(logic [ADDR_WIDTH-1:0] addr, output logic [DATA_WIDTH-1:0] data, output logic [1:0] resp, logic [ID_WIDTH-1:0] id='0)",
                "desc": "High-level single-beat read",
            },
            {
                "name": "write_burst",
                "sig": "write_burst(logic [ADDR_WIDTH-1:0] addr, ref logic [DATA_WIDTH-1:0] data[], ref logic [STRB_WIDTH-1:0] strb[], logic [ID_WIDTH-1:0] id='0, logic [BURST_WIDTH-1:0] burst='b01, output logic [1:0] resp[])",
                "desc": "High-level burst write",
            },
            {
                "name": "read_burst",
                "sig": "read_burst(logic [ADDR_WIDTH-1:0] addr, int unsigned beat_count, output logic [DATA_WIDTH-1:0] data[], output logic [1:0] resp[], logic [ID_WIDTH-1:0] id='0, logic [BURST_WIDTH-1:0] burst='b01)",
                "desc": "High-level burst read",
            },
        ],
        "Axi4FullSlaveVIP": [
            {
                "name": "new",
                "sig": "new(string name, virtual axi4_full_if vif)",
                "desc": "Constructor",
            },
            {
                "name": "configure_backpressure",
                "sig": "configure_backpressure(bit enable=0, int unsigned min_cycles=0, int unsigned max_cycles=0)",
                "desc": "Configure backpressure for all channels",
            },
            {
                "name": "configure_timeout",
                "sig": "configure_timeout(int unsigned cycles)",
                "desc": "Set timeout cycle count",
            },
            {
                "name": "clear_outputs",
                "sig": "clear_outputs()",
                "desc": "Drive all output signals to default state",
            },
            {
                "name": "wait_reset_release",
                "sig": "wait_reset_release()",
                "desc": "Wait for reset de-assertion",
            },
            {
                "name": "recv_awchn",
                "sig": "recv_awchn(output logic [ADDR_WIDTH-1:0] addr, output logic [ID_WIDTH-1:0] id, output logic [SIZE_WIDTH-1:0] size, output logic [LEN_WIDTH-1:0] len, ...)",
                "desc": "Receive write address channel",
            },
            {
                "name": "recv_wchn",
                "sig": "recv_wchn(output logic [DATA_WIDTH-1:0] data, output logic [STRB_WIDTH-1:0] strb, output logic last, output logic [WUSER_WIDTH-1:0] user)",
                "desc": "Receive write data channel",
            },
            {
                "name": "send_bchn",
                "sig": "send_bchn(logic [ID_WIDTH-1:0] id, logic [1:0] resp='b00, logic [BUSER_WIDTH-1:0] user='0)",
                "desc": "Send write response channel",
            },
            {
                "name": "write_resp_single",
                "sig": "write_resp_single(logic [DATA_WIDTH-1:0] data, logic [STRB_WIDTH-1:0] strb='1, logic [ID_WIDTH-1:0] id='0, logic [1:0] resp='b00)",
                "desc": "High-level single-beat write response",
            },
            {
                "name": "write_resp_burst",
                "sig": "write_resp_burst(ref logic [DATA_WIDTH-1:0] data[], ref logic [STRB_WIDTH-1:0] strb[], logic [ID_WIDTH-1:0] id='0, logic [1:0] resp='b00)",
                "desc": "High-level burst write response",
            },
            {
                "name": "recv_archn",
                "sig": "recv_archn(output logic [ADDR_WIDTH-1:0] addr, output logic [ID_WIDTH-1:0] id, output logic [SIZE_WIDTH-1:0] size, output logic [LEN_WIDTH-1:0] len, ...)",
                "desc": "Receive read address channel",
            },
            {
                "name": "send_rchn",
                "sig": "send_rchn(logic [DATA_WIDTH-1:0] data, logic [ID_WIDTH-1:0] id, logic [1:0] resp='b00, logic last='b1, logic [RUSER_WIDTH-1:0] user='0)",
                "desc": "Send read data channel",
            },
            {
                "name": "read_resp_single",
                "sig": "read_resp_single(logic [DATA_WIDTH-1:0] data, logic [ID_WIDTH-1:0] id='0, logic [1:0] resp='b00)",
                "desc": "High-level single-beat read response",
            },
            {
                "name": "read_resp_burst",
                "sig": "read_resp_burst(ref logic [DATA_WIDTH-1:0] data[], logic [ID_WIDTH-1:0] id='0, logic [1:0] resp='b00)",
                "desc": "High-level burst read response",
            },
        ],
        "axi4_full_mem_vip": [
            {
                "name": "write_word",
                "sig": "write_word(logic [ADDR_WIDTH-1:0] addr, logic [DATA_WIDTH-1:0] data, logic [STRB_WIDTH-1:0] strb)",
                "desc": "Write to byte-addressed memory with strobes",
            },
        ],
    },
    "axi4_stream_vip": {
        "Axi4StreamMasterVIP": [
            {
                "name": "new",
                "sig": "new(string name, virtual axi4_stream_if vif)",
                "desc": "Constructor",
            },
            {
                "name": "configure_pause_generator",
                "sig": "configure_pause_generator(bit enable, int unsigned min_cycles=0, int unsigned max_cycles=0)",
                "desc": "Enable/disable random pause between transfers",
            },
            {
                "name": "configure_timeout",
                "sig": "configure_timeout(int unsigned cycles)",
                "desc": "Set timeout cycle count",
            },
            {
                "name": "clear_outputs",
                "sig": "clear_outputs()",
                "desc": "Drive all output signals to default state",
            },
            {
                "name": "wait_reset_release",
                "sig": "wait_reset_release()",
                "desc": "Wait for reset de-assertion",
            },
            {
                "name": "send_single",
                "sig": "send_single(logic [DATA_WIDTH-1:0] tdata, logic [KEEP_WIDTH-1:0] tkeep='1, logic [KEEP_WIDTH-1:0] tstrb='1, bit tlast='1, logic [TUSER_WIDTH-1:0] tuser='0, logic [TDEST_WIDTH-1:0] tdest='0, logic [TID_WIDTH-1:0] tid='0)",
                "desc": "Send single transfer",
            },
            {
                "name": "send_multi",
                "sig": "send_multi(logic [DATA_WIDTH-1:0] tdata[], ref logic [KEEP_WIDTH-1:0] tkeep[], ref logic [KEEP_WIDTH-1:0] tstrb[], ref logic [TUSER_WIDTH-1:0] tuser[], ref logic [TDEST_WIDTH-1:0] tdest[], ref logic [TID_WIDTH-1:0] tid[], bit tlast=1)",
                "desc": "Send multiple transfers",
            },
        ],
        "Axi4StreamSlaveVIP": [
            {
                "name": "new",
                "sig": "new(string name, virtual axi4_stream_if vif)",
                "desc": "Constructor",
            },
            {
                "name": "configure_backpressure",
                "sig": "configure_backpressure(bit enable=0, int unsigned min_cycles=0, int unsigned max_cycles=0)",
                "desc": "Configure tready backpressure",
            },
            {
                "name": "configure_timeout",
                "sig": "configure_timeout(int unsigned cycles)",
                "desc": "Set timeout cycle count",
            },
            {
                "name": "clear_outputs",
                "sig": "clear_outputs()",
                "desc": "Drive all output signals to default state",
            },
            {
                "name": "wait_reset_release",
                "sig": "wait_reset_release()",
                "desc": "Wait for reset de-assertion",
            },
            {
                "name": "recv_single",
                "sig": "recv_single(output logic [DATA_WIDTH-1:0] tdata, output logic [KEEP_WIDTH-1:0] tkeep, output logic [KEEP_WIDTH-1:0] tstrb, output logic [TUSER_WIDTH-1:0] tuser, output logic [TDEST_WIDTH-1:0] tdest, output logic [TID_WIDTH-1:0] tid, output bit tlast)",
                "desc": "Receive single transfer",
            },
            {
                "name": "recv_multi",
                "sig": "recv_multi(ref logic [DATA_WIDTH-1:0] tdata[], ref logic [KEEP_WIDTH-1:0] tkeep[], ref logic [KEEP_WIDTH-1:0] tstrb[], ref logic [TUSER_WIDTH-1:0] tuser[], ref logic [TDEST_WIDTH-1:0] tdest[], ref logic [TID_WIDTH-1:0] tid[], input int unsigned count=1)",
                "desc": "Receive multiple transfers",
            },
        ],
    },
    "uart_vip": {
        "UartTxVIP": [
            {
                "name": "new",
                "sig": "new(string name, virtual uart_if vif)",
                "desc": "Constructor",
            },
            {
                "name": "configure_pause_generator",
                "sig": "configure_pause_generator(bit enable, int unsigned min_cycles=0, int unsigned max_cycles=0)",
                "desc": "Enable/disable random pause between bytes",
            },
            {
                "name": "configure_timeout",
                "sig": "configure_timeout(int unsigned cycles)",
                "desc": "Set timeout cycle count",
            },
            {
                "name": "clear_outputs",
                "sig": "clear_outputs()",
                "desc": "Drive serial_data to idle (1'b1)",
            },
            {
                "name": "wait_reset_release",
                "sig": "wait_reset_release()",
                "desc": "Wait for reset de-assertion",
            },
            {
                "name": "apply_pause",
                "sig": "apply_pause()",
                "desc": "Apply random pause if enabled",
            },
            {
                "name": "send_byte",
                "sig": "send_byte(logic [7:0] data)",
                "desc": "Transmit one byte (8N1 format)",
            },
        ],
        "UartRxVIP": [
            {
                "name": "new",
                "sig": "new(string name, virtual uart_if vif)",
                "desc": "Constructor",
            },
            {
                "name": "configure_timeout",
                "sig": "configure_timeout(int unsigned cycles)",
                "desc": "Set timeout cycle count",
            },
            {
                "name": "wait_reset_release",
                "sig": "wait_reset_release()",
                "desc": "Wait for reset de-assertion",
            },
            {
                "name": "recv_byte",
                "sig": "recv_byte(output logic [7:0] data, output bit framing_error)",
                "desc": "Receive one byte (8N1 format)",
            },
        ],
    },
    "spi_vip": {
        "SpiMasterVIP": [
            {
                "name": "new",
                "sig": "new(string name, virtual spi_if vif)",
                "desc": "Constructor",
            },
            {
                "name": "configure_pause_generator",
                "sig": "configure_pause_generator(bit enable, int unsigned min_cycles=0, int unsigned max_cycles=0)",
                "desc": "Enable/disable random pause between transfers",
            },
            {
                "name": "configure_timeout",
                "sig": "configure_timeout(int unsigned cycles)",
                "desc": "Set timeout cycle count",
            },
            {
                "name": "clear_outputs",
                "sig": "clear_outputs()",
                "desc": "Drive SCLK/CS to idle state",
            },
            {
                "name": "wait_reset_release",
                "sig": "wait_reset_release()",
                "desc": "Wait for reset de-assertion",
            },
            {
                "name": "apply_pause",
                "sig": "apply_pause()",
                "desc": "Apply random pause if enabled",
            },
            {
                "name": "send_recv",
                "sig": "send_recv(logic [DATA_BITS-1:0] tx_data, output logic [DATA_BITS-1:0] rx_data)",
                "desc": "Full-duplex SPI transfer",
            },
        ],
        "SpiSlaveVIP": [
            {
                "name": "new",
                "sig": "new(string name, virtual spi_if vif)",
                "desc": "Constructor",
            },
            {
                "name": "configure_timeout",
                "sig": "configure_timeout(int unsigned cycles)",
                "desc": "Set timeout cycle count",
            },
            {
                "name": "clear_outputs",
                "sig": "clear_outputs()",
                "desc": "Drive MISO to default (1'b0)",
            },
            {
                "name": "wait_reset_release",
                "sig": "wait_reset_release()",
                "desc": "Wait for reset de-assertion",
            },
            {
                "name": "send_recv",
                "sig": "send_recv(logic [DATA_BITS-1:0] tx_data, output logic [DATA_BITS-1:0] rx_data)",
                "desc": "Full-duplex SPI transfer (slave)",
            },
        ],
    },
    "i2c_vip": {
        "I2CMasterVIP": [
            {
                "name": "new",
                "sig": "new(string name, virtual i2c_if vif)",
                "desc": "Constructor",
            },
            {
                "name": "configure_pause_generator",
                "sig": "configure_pause_generator(bit enable, int unsigned min_cycles=0, int unsigned max_cycles=0)",
                "desc": "Enable/disable random pause between transactions",
            },
            {
                "name": "configure_timeout",
                "sig": "configure_timeout(int unsigned cycles)",
                "desc": "Set timeout cycle count",
            },
            {
                "name": "clear_outputs",
                "sig": "clear_outputs()",
                "desc": "Release SDA/SCL (tri-state)",
            },
            {
                "name": "wait_reset_release",
                "sig": "wait_reset_release()",
                "desc": "Wait for reset de-assertion",
            },
            {
                "name": "apply_pause",
                "sig": "apply_pause()",
                "desc": "Apply random pause if enabled",
            },
            {
                "name": "start_condition",
                "sig": "start_condition()",
                "desc": "Generate I2C start condition",
            },
            {
                "name": "repeated_start_condition",
                "sig": "repeated_start_condition()",
                "desc": "Generate repeated start",
            },
            {
                "name": "stop_condition",
                "sig": "stop_condition()",
                "desc": "Generate I2C stop condition",
            },
            {
                "name": "write_bit",
                "sig": "write_bit(bit bit_value)",
                "desc": "Write single bit on SDA",
            },
            {
                "name": "read_bit",
                "sig": "read_bit(output bit bit_value)",
                "desc": "Read single bit from SDA",
            },
            {
                "name": "write_raw_byte",
                "sig": "write_raw_byte(logic [7:0] data, output bit ack)",
                "desc": "Write byte, get ACK",
            },
            {
                "name": "read_raw_byte",
                "sig": "read_raw_byte(output logic [7:0] data, bit ack)",
                "desc": "Read byte, send ACK/NACK",
            },
            {
                "name": "send_byte",
                "sig": "send_byte(logic [6:0] address, logic [7:0] data, output bit address_ack, output bit data_ack)",
                "desc": "Single-byte write to slave",
            },
            {
                "name": "recv_byte",
                "sig": "recv_byte(logic [6:0] address, output logic [7:0] data, output bit address_ack)",
                "desc": "Single-byte read from slave",
            },
            {
                "name": "send_bytes",
                "sig": "send_bytes(logic [6:0] address, logic [7:0] data[], output bit address_ack, output bit data_acks[], bit use_repeated_start=0)",
                "desc": "Multi-byte write to slave",
            },
            {
                "name": "recv_bytes",
                "sig": "recv_bytes(logic [6:0] address, ref logic [7:0] data[], output bit address_ack, bit use_repeated_start=0)",
                "desc": "Multi-byte read from slave",
            },
        ],
        "I2CSlaveVIP": [
            {
                "name": "new",
                "sig": "new(string name, virtual i2c_if vif)",
                "desc": "Constructor",
            },
            {
                "name": "configure_timeout",
                "sig": "configure_timeout(int unsigned cycles)",
                "desc": "Set timeout cycle count",
            },
            {
                "name": "clear_outputs",
                "sig": "clear_outputs()",
                "desc": "Release SDA/SCL (tri-state)",
            },
            {
                "name": "wait_reset_release",
                "sig": "wait_reset_release()",
                "desc": "Wait for reset de-assertion",
            },
            {
                "name": "wait_start",
                "sig": "wait_start()",
                "desc": "Wait for start condition from master",
            },
            {
                "name": "wait_stop",
                "sig": "wait_stop()",
                "desc": "Wait for stop condition from master",
            },
            {
                "name": "read_raw_byte",
                "sig": "read_raw_byte(output logic [7:0] data)",
                "desc": "Read byte from master",
            },
            {"name": "send_ack", "sig": "send_ack(bit ack)", "desc": "Send ACK/NACK"},
            {
                "name": "send_ack_stretch",
                "sig": "send_ack_stretch(bit ack, int unsigned stretch_cycles=0)",
                "desc": "Send ACK with clock stretching",
            },
            {
                "name": "write_raw_byte",
                "sig": "write_raw_byte(logic [7:0] data)",
                "desc": "Write byte to master",
            },
            {
                "name": "receive_ack",
                "sig": "receive_ack(output bit ack)",
                "desc": "Receive ACK from master",
            },
            {
                "name": "recv_byte",
                "sig": "recv_byte(output logic [7:0] data, output bit address_match)",
                "desc": "Single-byte receive (backward compatible)",
            },
            {
                "name": "send_byte",
                "sig": "send_byte(logic [7:0] data, output bit address_match, output bit master_ack)",
                "desc": "Single-byte send (backward compatible)",
            },
            {
                "name": "recv_bytes",
                "sig": "recv_bytes(int unsigned byte_count, output logic [7:0] data[], output bit address_match, int unsigned stretch_after_addr=0)",
                "desc": "Multi-byte receive",
            },
            {
                "name": "send_bytes",
                "sig": "send_bytes(int unsigned byte_count, logic [7:0] data[], output bit address_match, output bit master_acks[], int unsigned stretch_after_addr=0)",
                "desc": "Multi-byte send",
            },
        ],
    },
    "i2s_vip": {
        "I2STxVIP": [
            {
                "name": "new",
                "sig": "new(string name, virtual i2s_if vif)",
                "desc": "Constructor",
            },
            {
                "name": "configure_pause_generator",
                "sig": "configure_pause_generator(bit enable, int unsigned min_cycles=0, int unsigned max_cycles=0)",
                "desc": "Enable/disable random pause between frames",
            },
            {
                "name": "configure_timeout",
                "sig": "configure_timeout(int unsigned cycles)",
                "desc": "Set timeout cycle count",
            },
            {
                "name": "clear_outputs",
                "sig": "clear_outputs()",
                "desc": "Drive BCLK/WS/SD to idle state",
            },
            {
                "name": "wait_reset_release",
                "sig": "wait_reset_release()",
                "desc": "Wait for reset de-assertion",
            },
            {
                "name": "apply_pause",
                "sig": "apply_pause()",
                "desc": "Apply random pause if enabled",
            },
            {
                "name": "send_frame",
                "sig": "send_frame(logic [SAMPLE_WIDTH-1:0] left_sample, logic [SAMPLE_WIDTH-1:0] right_sample)",
                "desc": "Transmit stereo I2S frame",
            },
        ],
        "I2SRxVIP": [
            {
                "name": "new",
                "sig": "new(string name, virtual i2s_if vif)",
                "desc": "Constructor",
            },
            {
                "name": "configure_timeout",
                "sig": "configure_timeout(int unsigned cycles)",
                "desc": "Set timeout cycle count",
            },
            {
                "name": "wait_reset_release",
                "sig": "wait_reset_release()",
                "desc": "Wait for reset de-assertion",
            },
            {
                "name": "recv_frame",
                "sig": "recv_frame(output logic [SAMPLE_WIDTH-1:0] left_sample, output logic [SAMPLE_WIDTH-1:0] right_sample, output bit frame_error)",
                "desc": "Receive stereo I2S frame",
            },
        ],
    },
}


# ---------------------------------------------------------------------------
# Helper: Interface signal definitions
# ---------------------------------------------------------------------------

_VIP_INTERFACES: dict[str, dict[str, Any]] = {
    "apb_vip": {
        "name": "apb_if",
        "file": "apb_if.sv",
        "signals": [
            {"name": "paddr", "dir": "input", "width": "ADDR_WIDTH"},
            {"name": "psel", "dir": "input", "width": "1"},
            {"name": "penable", "dir": "input", "width": "1"},
            {"name": "pwrite", "dir": "input", "width": "1"},
            {"name": "pwdata", "dir": "input", "width": "DATA_WIDTH"},
            {"name": "pstrb", "dir": "input", "width": "STRB_WIDTH"},
            {"name": "pprot", "dir": "input", "width": "PROT_WIDTH"},
            {"name": "prdata", "dir": "output", "width": "DATA_WIDTH"},
            {"name": "pready", "dir": "output", "width": "1"},
            {"name": "pslverr", "dir": "output", "width": "1"},
        ],
    },
    "axi4_lite_vip": {
        "name": "axi4_lite_if",
        "file": "axi4_lite_if.sv",
        "signals": [
            {"name": "aclk", "dir": "input", "width": "1"},
            {"name": "aresetn", "dir": "input", "width": "1"},
            {"name": "awaddr", "dir": "input", "width": "ADDR_WIDTH"},
            {"name": "awprot", "dir": "input", "width": "3"},
            {"name": "awvalid", "dir": "input", "width": "1"},
            {"name": "awready", "dir": "output", "width": "1"},
            {"name": "wdata", "dir": "input", "width": "DATA_WIDTH"},
            {"name": "wstrb", "dir": "input", "width": "STRB_WIDTH"},
            {"name": "wvalid", "dir": "input", "width": "1"},
            {"name": "wready", "dir": "output", "width": "1"},
            {"name": "bresp", "dir": "output", "width": "2"},
            {"name": "bvalid", "dir": "output", "width": "1"},
            {"name": "bready", "dir": "input", "width": "1"},
            {"name": "araddr", "dir": "input", "width": "ADDR_WIDTH"},
            {"name": "arprot", "dir": "input", "width": "3"},
            {"name": "arvalid", "dir": "input", "width": "1"},
            {"name": "arready", "dir": "output", "width": "1"},
            {"name": "rdata", "dir": "output", "width": "DATA_WIDTH"},
            {"name": "rresp", "dir": "output", "width": "2"},
            {"name": "rvalid", "dir": "output", "width": "1"},
            {"name": "rready", "dir": "input", "width": "1"},
        ],
    },
    "axi4_full_vip": {
        "name": "axi4_full_if",
        "file": "axi4_full_if.sv",
        "signals": [
            {"name": "aclk", "dir": "input", "width": "1"},
            {"name": "aresetn", "dir": "input", "width": "1"},
            {"name": "awid", "dir": "input", "width": "ID_WIDTH"},
            {"name": "awaddr", "dir": "input", "width": "ADDR_WIDTH"},
            {"name": "awlen", "dir": "input", "width": "8"},
            {"name": "awsize", "dir": "input", "width": "3"},
            {"name": "awburst", "dir": "input", "width": "2"},
            {"name": "awlock", "dir": "input", "width": "1"},
            {"name": "awcache", "dir": "input", "width": "4"},
            {"name": "awprot", "dir": "input", "width": "3"},
            {"name": "awqos", "dir": "input", "width": "4"},
            {"name": "awregion", "dir": "input", "width": "4"},
            {"name": "awuser", "dir": "input", "width": "AWUSER_WIDTH"},
            {"name": "awvalid", "dir": "input", "width": "1"},
            {"name": "awready", "dir": "output", "width": "1"},
            {"name": "wdata", "dir": "input", "width": "DATA_WIDTH"},
            {"name": "wstrb", "dir": "input", "width": "STRB_WIDTH"},
            {"name": "wlast", "dir": "input", "width": "1"},
            {"name": "wuser", "dir": "input", "width": "WUSER_WIDTH"},
            {"name": "wvalid", "dir": "input", "width": "1"},
            {"name": "wready", "dir": "output", "width": "1"},
            {"name": "bid", "dir": "output", "width": "ID_WIDTH"},
            {"name": "bresp", "dir": "output", "width": "2"},
            {"name": "buser", "dir": "output", "width": "BUSER_WIDTH"},
            {"name": "bvalid", "dir": "output", "width": "1"},
            {"name": "bready", "dir": "input", "width": "1"},
            {"name": "arid", "dir": "input", "width": "ID_WIDTH"},
            {"name": "araddr", "dir": "input", "width": "ADDR_WIDTH"},
            {"name": "arlen", "dir": "input", "width": "8"},
            {"name": "arsize", "dir": "input", "width": "3"},
            {"name": "arburst", "dir": "input", "width": "2"},
            {"name": "arlock", "dir": "input", "width": "1"},
            {"name": "arcache", "dir": "input", "width": "4"},
            {"name": "arprot", "dir": "input", "width": "3"},
            {"name": "arqos", "dir": "input", "width": "4"},
            {"name": "arregion", "dir": "input", "width": "4"},
            {"name": "aruser", "dir": "input", "width": "ARUSER_WIDTH"},
            {"name": "arvalid", "dir": "input", "width": "1"},
            {"name": "arready", "dir": "output", "width": "1"},
            {"name": "rid", "dir": "output", "width": "ID_WIDTH"},
            {"name": "rdata", "dir": "output", "width": "DATA_WIDTH"},
            {"name": "rresp", "dir": "output", "width": "2"},
            {"name": "rlast", "dir": "output", "width": "1"},
            {"name": "ruser", "dir": "output", "width": "RUSER_WIDTH"},
            {"name": "rvalid", "dir": "output", "width": "1"},
            {"name": "rready", "dir": "input", "width": "1"},
        ],
    },
    "axi4_stream_vip": {
        "name": "axi4_stream_if",
        "file": "axi4_stream_if.sv",
        "signals": [
            {"name": "aclk", "dir": "input", "width": "1"},
            {"name": "aresetn", "dir": "input", "width": "1"},
            {"name": "tdata", "dir": "input", "width": "DATA_WIDTH"},
            {"name": "tkeep", "dir": "input", "width": "KEEP_WIDTH"},
            {"name": "tstrb", "dir": "input", "width": "KEEP_WIDTH"},
            {"name": "tuser", "dir": "input", "width": "TUSER_WIDTH"},
            {"name": "tdest", "dir": "input", "width": "TDEST_WIDTH"},
            {"name": "tid", "dir": "input", "width": "TID_WIDTH"},
            {"name": "tlast", "dir": "input", "width": "1"},
            {"name": "tvalid", "dir": "input", "width": "1"},
            {"name": "tready", "dir": "output", "width": "1"},
        ],
    },
    "uart_vip": {
        "name": "uart_if",
        "file": "uart_if.sv",
        "signals": [
            {"name": "clk", "dir": "input", "width": "1"},
            {"name": "rst", "dir": "input", "width": "1"},
            {"name": "serial_data", "dir": "inout", "width": "1"},
        ],
    },
    "spi_vip": {
        "name": "spi_if",
        "file": "spi_if.sv",
        "signals": [
            {"name": "clk", "dir": "input", "width": "1"},
            {"name": "rst", "dir": "input", "width": "1"},
            {"name": "sclk", "dir": "input", "width": "1"},
            {"name": "cs", "dir": "input", "width": "1"},
            {"name": "mosi", "dir": "input", "width": "1"},
            {"name": "miso", "dir": "output", "width": "1"},
        ],
    },
    "i2c_vip": {
        "name": "i2c_if",
        "file": "i2c_if.sv",
        "signals": [
            {"name": "clk", "dir": "input", "width": "1"},
            {"name": "rst", "dir": "input", "width": "1"},
            {"name": "scl", "dir": "inout", "width": "1"},
            {"name": "sda", "dir": "inout", "width": "1"},
            {"name": "master_scl_low", "dir": "input", "width": "1"},
            {"name": "master_sda_low", "dir": "input", "width": "1"},
            {"name": "slave_scl_low", "dir": "input", "width": "1"},
            {"name": "slave_sda_low", "dir": "input", "width": "1"},
        ],
    },
    "i2s_vip": {
        "name": "i2s_if",
        "file": "i2s_if.sv",
        "signals": [
            {"name": "clk", "dir": "input", "width": "1"},
            {"name": "rst", "dir": "input", "width": "1"},
            {"name": "bclk", "dir": "input", "width": "1"},
            {"name": "ws", "dir": "input", "width": "1"},
            {"name": "sd", "dir": "output", "width": "1"},
        ],
    },
}


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------


def _handle_list_vips() -> list[types.TextContent]:
    """List all available VIPs with their components."""
    vips = list_vips()
    lines: list[str] = []
    for v in vips:
        comps = ", ".join(c.name for c in v.components)
        lines.append(f"- **{v.name}**: {v.description}")
        lines.append(f"  - Components: {comps}")
        lines.append(f"  - Source: `{get_vip_path(v.name)}`")
        lines.append("")
    return [types.TextContent(type="text", text="\n".join(lines))]


def _handle_get_vip_info(arguments: dict[str, Any]) -> list[types.TextContent]:
    """Get detailed information about a specific VIP."""
    name = arguments.get("vip_name", "")
    info = get_vip_info(name)
    if info is None:
        return [types.TextContent(type="text", text=f"Error: VIP '{name}' not found.")]

    lines = [
        f"# {info.name}",
        f"**Description**: {info.description}",
        f"**Path**: `{get_vip_path(info.name)}`",
        f"**Sim Path**: `{get_vip_sim_path(info.name)}`",
        "",
        "## Components",
    ]
    for comp in info.components:
        lines.append(f"- **{comp.name}** ({comp.comp_type})")
        lines.append(f"  - File: `{comp.file}`")
        if comp.description:
            lines.append(f"  - {comp.description}")
        lines.append("")

    if info.parameters:
        lines.append("## Parameters")
        for p in info.parameters:
            lines.append(f"- `{p.name}`: {p.type} = {p.default} — {p.description}")

    return [types.TextContent(type="text", text="\n".join(lines))]


def _handle_get_vip_api(arguments: dict[str, Any]) -> list[types.TextContent]:
    """Get API signatures for a VIP component."""
    name = arguments.get("vip_name", "")
    component = arguments.get("component", "")

    if name not in _VIP_API:
        return [types.TextContent(type="text", text=f"Error: VIP '{name}' not found.")]

    components = _VIP_API[name]
    if component and component not in components:
        return [
            types.TextContent(
                type="text",
                text=f"Error: Component '{component}' not found in '{name}'. Available: {', '.join(components.keys())}",
            )
        ]

    lines: list[str] = []
    comps = {component: components[component]} if component else components
    for comp_name, methods in comps.items():
        lines.append(f"## {comp_name}")
        for m in methods:
            lines.append(f"- `{m['sig']}`")
            lines.append(f"  - {m['desc']}")
        lines.append("")

    return [types.TextContent(type="text", text="\n".join(lines))]


def _handle_get_vip_interface(arguments: dict[str, Any]) -> list[types.TextContent]:
    """Get interface signal definitions for a VIP."""
    name = arguments.get("vip_name", "")

    if name not in _VIP_INTERFACES:
        return [types.TextContent(type="text", text=f"Error: VIP '{name}' not found.")]

    iface = _VIP_INTERFACES[name]
    lines = [
        f"# {iface['name']} (`{iface['file']}`)",
        "",
        "| Signal | Direction | Width |",
        "|--------|-----------|-------|",
    ]
    for sig in iface["signals"]:
        lines.append(f"| `{sig['name']}` | {sig['dir']} | {sig['width']} |")

    return [types.TextContent(type="text", text="\n".join(lines))]


def _handle_generate_testbench(arguments: dict[str, Any]) -> list[types.TextContent]:
    """Generate a SystemVerilog testbench template for a VIP."""
    vip_name = arguments.get("vip_name", "")
    dut_name = arguments.get("dut_name", "my_dut")
    signals = arguments.get("signals", [])

    info = get_vip_info(vip_name)
    if info is None:
        return [
            types.TextContent(type="text", text=f"Error: VIP '{vip_name}' not found.")
        ]

    # Build signal port list
    sig_ports = (
        "\n    ".join(
            f"logic [{s.get('width', '1')}-1:0] {s['name']};" for s in signals
        )
        if signals
        else "    // TODO: add DUT signals"
    )

    sig_connections = (
        "\n        .".join(f"{s['name']}({s['name']})" for s in signals)
        if signals
        else "// TODO: connect DUT"
    )

    # Build VIP instantiation
    vif_name = f"{vip_name.replace('_vip', '')}_if"
    vip_insts = []
    for comp in info.components:
        if comp.comp_type == "class":
            vip_insts.append(
                f"    {comp.name} #{','.join(f'{p.name}={p.default}' for p in info.parameters)} "
                f"{comp.name.lower()}_i;\n"
                f"    initial begin\n"
                f'        {comp.name.lower()}_i = new("{comp.name.lower()}_i", vif);\n'
                f"    end"
            )

    tb_code = f"""// Auto-generated testbench for {vip_name}
// Generated by sv-light-vip MCP Server

`timescale 1ns / 1ps

module {dut_name}_tb;

    // ------------------------------------------------------------------
    // Parameters
    // ------------------------------------------------------------------
{chr(10).join(f'    parameter {p.name} = {p.default};' for p in info.parameters)}

    // ------------------------------------------------------------------
    // DUT Signals
    // ------------------------------------------------------------------
    {sig_ports}

    // ------------------------------------------------------------------
    // VIP Interface
    // ------------------------------------------------------------------
    {vif_name} #(
        {chr(10).join(f'        .{p.name}({p.name}),' for p in info.parameters)}
    ) vif ();

    // ------------------------------------------------------------------
    // Clock & Reset
    // ------------------------------------------------------------------
    logic clk = 0;
    logic rst = 0;
    always #5 clk = ~clk;

    initial begin
        rst = 1;
        #20 rst = 0;
    end

    // ------------------------------------------------------------------
    // DUT Instantiation
    // ------------------------------------------------------------------
    {dut_name} u_dut (
        .clk(clk),
        .rst(rst),
        {sig_connections}
    );

    // ------------------------------------------------------------------
    // VIP Instantiation
    // ------------------------------------------------------------------
{chr(10).join(vip_insts)}

    // ------------------------------------------------------------------
    // Test Sequence
    // ------------------------------------------------------------------
    initial begin
        // Wait for reset release
        @(posedge clk);
        @(negedge rst);
        @(posedge clk);

        $display("=== Test Start ===");

        // TODO: add test sequence here

        #100;
        $display("=== Test Done ===");
        $finish;
    end

endmodule
"""
    return [types.TextContent(type="text", text=tb_code)]


def _handle_generate_run_py(arguments: dict[str, Any]) -> list[types.TextContent]:
    """Generate a VUnit run.py script for a VIP."""
    vip_name = arguments.get("vip_name", "")

    info = get_vip_info(vip_name)
    if info is None:
        return [
            types.TextContent(type="text", text=f"Error: VIP '{vip_name}' not found.")
        ]

    run_py_code = f'''"""VUnit test runner for {vip_name} — auto-generated by sv-light-vip MCP Server."""

from pathlib import Path
import sys

# Add sv-light-vip to path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from sv_light_vip import add_vip_to_vunit
from vunit import VUnit

PROJECT_ROOT = Path(__file__).parent


def main():
    vu = VUnit.from_argv()
    lib = vu.add_library("work")

    # Add VIP sources
    add_vip_to_vunit(vu, lib, "{vip_name}")

    # Add testbench
    lib.add_source_files(PROJECT_ROOT / "*.sv")

    vu.main()


if __name__ == "__main__":
    main()
'''
    return [types.TextContent(type="text", text=run_py_code)]


# ---------------------------------------------------------------------------
# MCP tool registration
# ---------------------------------------------------------------------------


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """Register all available tools."""
    return [
        types.Tool(
            name="list_vips",
            description="List all available Verification IPs in sv-light-vip",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="get_vip_info",
            description="Get detailed information about a specific VIP (components, parameters, source files)",
            inputSchema={
                "type": "object",
                "properties": {
                    "vip_name": {
                        "type": "string",
                        "description": "VIP name, e.g. apb_vip, axi4_lite_vip, uart_vip",
                    }
                },
                "required": ["vip_name"],
            },
        ),
        types.Tool(
            name="get_vip_api",
            description="Get API method signatures for a VIP component",
            inputSchema={
                "type": "object",
                "properties": {
                    "vip_name": {
                        "type": "string",
                        "description": "VIP name, e.g. apb_vip",
                    },
                    "component": {
                        "type": "string",
                        "description": "Component name (optional). If omitted, shows all components.",
                    },
                },
                "required": ["vip_name"],
            },
        ),
        types.Tool(
            name="get_vip_interface",
            description="Get interface signal definitions for a VIP",
            inputSchema={
                "type": "object",
                "properties": {
                    "vip_name": {
                        "type": "string",
                        "description": "VIP name, e.g. apb_vip",
                    }
                },
                "required": ["vip_name"],
            },
        ),
        types.Tool(
            name="generate_testbench",
            description="Generate a SystemVerilog testbench template for a VIP",
            inputSchema={
                "type": "object",
                "properties": {
                    "vip_name": {
                        "type": "string",
                        "description": "VIP name, e.g. apb_vip",
                    },
                    "dut_name": {
                        "type": "string",
                        "description": "DUT module name (default: my_dut)",
                    },
                    "signals": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "width": {"type": "string"},
                            },
                        },
                        "description": "List of DUT signals to connect",
                    },
                },
                "required": ["vip_name"],
            },
        ),
        types.Tool(
            name="generate_run_py",
            description="Generate a VUnit run.py script for a VIP",
            inputSchema={
                "type": "object",
                "properties": {
                    "vip_name": {
                        "type": "string",
                        "description": "VIP name, e.g. apb_vip",
                    }
                },
                "required": ["vip_name"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any] | None
) -> list[types.TextContent]:
    """Dispatch tool calls to the appropriate handler."""
    if arguments is None:
        arguments = {}

    handlers = {
        "list_vips": _handle_list_vips,
        "get_vip_info": _handle_get_vip_info,
        "get_vip_api": _handle_get_vip_api,
        "get_vip_interface": _handle_get_vip_interface,
        "generate_testbench": _handle_generate_testbench,
        "generate_run_py": _handle_generate_run_py,
    }

    handler = handlers.get(name)
    if handler is None:
        return [types.TextContent(type="text", text=f"Error: unknown tool '{name}'")]

    return handler(arguments)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


async def main() -> None:
    """Run the MCP server with the specified transport."""
    parser = argparse.ArgumentParser(description="sv-light-vip MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport protocol (default: stdio)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for SSE transport (default: 8000)",
    )
    args = parser.parse_args()

    if args.transport == "sse":
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.routing import Mount

        sse = SseServerTransport("/messages/")

        async def handle_sse(request):
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await server.run(
                    streams[0], streams[1], server.create_initialization_options()
                )

        app = Starlette(
            routes=[
                Mount("/", app=handle_sse),
                Mount("/messages/", app=sse.handle_post_message),
            ]
        )

        import uvicorn

        print(f"Starting SSE server on port {args.port}...", file=sys.stderr)
        uvicorn.run(app, host="0.0.0.0", port=args.port)
    else:
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
