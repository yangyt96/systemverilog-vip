import sys
from vunit import VUnit
from pathlib import Path

ROOT = Path(__file__).parents[0]
DEFAULT_OUTPUT_PATH = Path("/tmp/axi_stream_vip_vunit_out")

argv = list(sys.argv[1:])
if "--output-path" not in argv:
    argv.extend(["--output-path", str(DEFAULT_OUTPUT_PATH)])

vu = VUnit.from_argv(argv=argv, compile_builtins=False)

vu.add_verilog_builtins()

lib = vu.add_library("lib")

lib.add_source_files(
    [
        ROOT / "*.sv",
    ],
    # include_dirs=ROOT.as_posix()
)


vu.main()
