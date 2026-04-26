import sys
from pathlib import Path
from itertools import product
from vunit import VUnit

ROOT = Path(__file__).resolve().parents[1]

argv = list(sys.argv[1:])

vu = VUnit.from_argv(argv=argv, compile_builtins=False)
vu.add_verilog_builtins()

lib = vu.add_library("lib")
lib.add_source_files(
    [
        ROOT / "tb/spi_vip_tb.sv",
    ],
    include_dirs=[
        (ROOT / "sim").as_posix(),
        (ROOT / "tb").as_posix(),
    ],
)

lib.set_sim_option(
    name="modelsim.init_file.gui",
    value=str(ROOT / "tb/spi_vip_tb.do"),
)


tb = lib.test_bench("spi_vip_tb")

for cpol, cpha in product(range(2), range(2)):
    tb.add_config(
        name=f"cpol={cpol}cpha={cpha}", generics={"TEST_CPOL": cpol, "TEST_CPHA": cpha}
    )


vu.main()
