"""sv-light-vip — Lightweight SystemVerilog Verification IPs.

Python integration package that provides:
- `add_vip_to_vunit()` — Add VIP sources to a VUnit project
- `list_vips()` / `get_vip_info()` — Query VIP metadata
"""

from .registry import (
    VipInfo,
    VipComponent,
    VipParameter,
    list_vips,
    get_vip_info,
    get_vip_path,
    get_vip_sim_path,
)
from .vunit_helper import add_vip_to_vunit, add_vip_sources

__all__ = [
    "VipInfo",
    "VipComponent",
    "VipParameter",
    "list_vips",
    "get_vip_info",
    "get_vip_path",
    "get_vip_sim_path",
    "add_vip_to_vunit",
    "add_vip_sources",
]
