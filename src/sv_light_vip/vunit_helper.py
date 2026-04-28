"""VUnit integration helpers for sv-light-vip.

Provides `add_vip_to_vunit()` to easily add VIP source files to a VUnit
project from an external testbench (e.g., in an RTL Design repo).
"""

from __future__ import annotations

import os
from typing import List, Optional, TYPE_CHECKING

from .registry import get_vip_info, get_vip_sim_path, list_vips

if TYPE_CHECKING:
    from vunit import VUnit
    from vunit.ui import Library


def add_vip_to_vunit(
    vu: "VUnit",
    lib: "Library",
    vip_name: str,
    include_tb_paths: bool = False,
) -> None:
    """Add all source files of a VIP to a VUnit library.

    This is the primary API for external projects to integrate sv-light-vip.

    Args:
        vu: The VUnit instance.
        lib: The VUnit library to add sources to.
        vip_name: Name of the VIP (e.g., 'apb_vip', 'axi4_full_vip').
        include_tb_paths: If True, also add the VIP's tb/ directory as an
                          include path (needed when testbench uses `include
                          "vunit_defines.svh"`).

    Raises:
        ValueError: If vip_name is not found or its sim/ directory doesn't exist.
    """
    info = get_vip_info(vip_name)
    if info is None:
        raise ValueError(
            f"Unknown VIP '{vip_name}'. Available: {', '.join(list_vips())}"
        )

    sim_path = get_vip_sim_path(vip_name)
    if sim_path is None:
        raise ValueError(
            f"VIP '{vip_name}' sim/ directory not found. "
            f"Set SV_LIGHT_VIP_ROOT environment variable if the repo is not "
            f"at the expected location."
        )

    # Build include directories
    inc_dirs = [sim_path]
    if include_tb_paths:
        tb_path = os.path.join(os.path.dirname(sim_path), "tb")
        if os.path.isdir(tb_path):
            inc_dirs.append(tb_path)

    # Add source files in dependency order (interface first, package last)
    for sf in info.source_files:
        file_path = os.path.join(sim_path, sf.path)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Expected source file not found: {file_path}")
        lib.add_source_files(
            str(file_path),
            include_dirs=[d for d in inc_dirs],
        )


def add_vip_sources(
    vu: "VUnit",
    lib: "Library",
    vip_names: List[str],
    include_tb_paths: bool = False,
) -> None:
    """Add multiple VIPs to a VUnit library.

    Args:
        vu: The VUnit instance.
        lib: The VUnit library to add sources to.
        vip_names: List of VIP names to add.
        include_tb_paths: If True, include tb/ directories as include paths.

    Example:
        >>> from sv_light_vip import add_vip_sources
        >>> add_vip_sources(vu, lib, ["apb_vip", "uart_vip"])
    """
    for name in vip_names:
        add_vip_to_vunit(vu, lib, name, include_tb_paths=include_tb_paths)
