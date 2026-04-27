import sys
from pathlib import Path

from vunit import VUnit

ROOT = Path(__file__).resolve().parents[1]

vu = VUnit.from_argv(argv=list(sys.argv[1:]), compile_builtins=False)
vu.add_verilog_builtins()

lib = vu.add_library("lib")
inc_dirs = [(ROOT / "sim").as_posix(), (ROOT / "tb").as_posix()]

for tb in ["apb_vip_tb.sv", "apb_mem_vip_tb.sv"]:
    lib.add_source_files([str(ROOT / "tb" / tb)], include_dirs=inc_dirs)

lib.set_sim_option("modelsim.init_file.gui", str(ROOT / "tb/apb_vip_tb.do"))

vu.main()
