# SV-Light VIP 验证工作流程

> 用于 **RTL Design 项目** 的验证工作流 — 利用 sv-light-vip 自动生成 testbench、编写 run.py、运行仿真
>
> 角色: Roo — FPGA/ASIC RTL 验证工程师 (Code/Architect 模式)
> 语言: 简体中文 (zh-CN) — 与用户沟通语言
> Commit 语言: 英语 — 代码提交信息使用英语
>
> 版本: v1.0

---

## 前置条件

1. **sv-light-vip 仓库已克隆** — 假设路径为 `../sv_vip/` 或通过环境变量 `SV_LIGHT_VIP_PATH` 指定
2. **Python 环境已配置** — 安装了 `vunit_hdl` 和 `mcp` 依赖
3. **Modelsim/Questa 已安装** — 或通过 Docker 运行
4. **MCP Server 已启动**（可选）— 用于查询 VIP API 和生成代码

### 环境变量

```bash
export SV_LIGHT_VIP_PATH=/path/to/sv_vip    # sv-light-vip 仓库路径
export SV_LIGHT_VIP_VENV=~/Project/venv      # Python 虚拟环境路径（可选）
```

---

## 核心原则

1. **自动生成** — 利用 sv-light-vip 的 Python API 和 MCP Server 自动生成 testbench 和 run.py
2. **参考成熟实现** — 生成代码前先分析 sv-light-vip 中已有的 testbench 作为模板
3. **仿真验证必须** — 所有生成的 testbench 必须通过仿真
4. **用户确认设计** — 复杂 DUT 应先确认接口映射和测试方案
5. **文档同步** — 生成的 testbench 需要有对应的使用说明

---

## 工作流程

### Phase 0: 环境检查与任务确认

```
输入: 用户需求（DUT 名称 + 接口类型）
```

1. **确认 sv-light-vip 路径**:
   ```bash
   # 检查环境变量或默认路径
   if [ -z "$SV_LIGHT_VIP_PATH" ]; then
       export SV_LIGHT_VIP_PATH="../sv_vip"
   fi
   ls "$SV_LIGHT_VIP_PATH/README.md" || echo "请设置 SV_LIGHT_VIP_PATH"
   ```

2. **确认 Python 环境**:
   ```bash
   # 检查 sv-light-vip 包是否可用
   python3 -c "from sv_light_vip import list_vips; print([v.name for v in list_vips()])" 2>/dev/null \
     || pip install -e "$SV_LIGHT_VIP_PATH"
   ```

3. **确认 MCP Server 可用**（可选）:
   ```bash
   python3 "$SV_LIGHT_VIP_PATH/mcp_server/server.py" --help 2>/dev/null \
     && echo "MCP Server 可用" || echo "MCP Server 未安装"
   ```

4. **理解 DUT** — 明确以下信息：
   - DUT 模块名和端口列表
   - 使用的总线协议（APB、AXI4-Lite、AXI4-Full、SPI、I2C、UART、I2S、AXI4-Stream）
   - 需要测试的功能点
   - 时钟和复位信号

5. **输出**: 确认的 DUT 信息 + 测试方案

### Phase 1: 分析参考实现

```
输入: DUT 接口信息 + 使用的总线协议
```

1. **查询 VIP API** — 使用 MCP Server 或直接阅读文档：
   ```bash
   # 使用 MCP Server 查询
   python3 -c "
   from sv_light_vip import get_vip_info, get_vip_path
   info = get_vip_info('apb_vip')
   print(f'VIP: {info.name}')
   print(f'Components: {[c.name for c in info.components]}')
   print(f'Path: {get_vip_path(info.name)}')
   "
   ```

2. **阅读参考 testbench** — 分析 sv-light-vip 中同协议 VIP 的 testbench：
   ```bash
   cat "$SV_LIGHT_VIP_PATH/apb_vip/tb/apb_mem_vip_tb.sv"
   cat "$SV_LIGHT_VIP_PATH/apb_vip/tb/run.py"
   ```

3. **阅读 VIP 文档** — 了解 API 使用方法：
   - [`API_REFERENCE.md`](API_REFERENCE.md) — API 签名和参数
   - 对应 VIP 的 [`doc/README.md`](.) — 使用示例

4. **输出**: 参考 testbench 结构分析 + 待生成的代码清单

### Phase 2: 设计测试方案

```
输入: 参考分析结果 + DUT 接口
```

1. **确定接口映射** — DUT 端口到 VIP 接口的映射关系：

   | DUT 端口 | VIP 信号 | 方向 |
   |----------|----------|------|
   | `pclk` | `apb_if.pclk` | 时钟 |
   | `prst_n` | `apb_if.prst_n` | 复位 |
   | `psel` | `apb_if.psel` | Master→DUT |
   | `penable` | `apb_if.penable` | Master→DUT |
   | `paddr` | `apb_if.paddr` | Master→DUT |
   | `pwdata` | `apb_if.pwdata` | Master→DUT |
   | `prdata` | `apb_if.prdata` | DUT→Slave |
   | `pready` | `apb_if.pready` | DUT→Slave |
   | `pslverr` | `apb_if.pslverr` | DUT→Slave |

2. **确定测试用例** — 基于 DUT 功能点：

   | 测试用例 | 描述 | 优先级 |
   |----------|------|--------|
   | 基本读写 | 验证 DUT 寄存器读写 | P0 |
   | 错误响应 | 验证地址越界返回 SLVERR | P0 |
   | 背压测试 | 验证 DUT 插入等待周期 | P1 |
   | 边界地址 | 验证地址边界行为 | P1 |
   | 复位测试 | 验证复位后行为 | P2 |

3. **确定文件结构**:

   ```
   project_root/
   ├── rtl/
   │   └── dut.sv              # DUT RTL 代码
   ├── tb/
   │   ├── dut_tb.sv           # 自动生成的 testbench
   │   ├── dut_tb.do           # ModelSim 波形配置（可选）
   │   └── run.py              # VUnit 运行脚本
   └── .agent/
       └── verification_workflow.md  # 本工作流文档
   ```

4. **输出**: 测试方案文档 + 文件创建清单

### Phase 3: 生成 Testbench

```
输入: 测试方案 + 接口映射
```

1. **生成 testbench 框架** — 使用 MCP Server 或手动编写：

   **使用 MCP Server 自动生成**:
   ```bash
   python3 -c "
   import sys
   sys.path.insert(0, '$SV_LIGHT_VIP_PATH')
   from mcp_server.server import _handle_generate_testbench
   result = _handle_generate_testbench({
       'vip_name': 'apb_vip',
       'dut_name': 'my_dut',
       'test_cases': ['basic_rw', 'error_resp', 'backpressure']
   })
   print(result[0].text)
   "
   ```

   **手动编写 testbench 模板**:

   ```systemverilog
   // tb/dut_tb.sv
   // Auto-generated testbench for my_dut using sv-light-vip
   //
   // DUT: my_dut
   // Protocol: APB
   // VIP: apb_vip

   `timescale 1ns/1ps

   module dut_tb;
       // Parameters
       localparam CLK_PERIOD = 10ns;
       localparam ADDR_WIDTH = 12;
       localparam DATA_WIDTH = 32;

       // Clock & Reset
       logic clk;
       logic rst_n;

       // DUT signals
       logic [ADDR_WIDTH-1:0] paddr;
       logic                  psel;
       logic                  penable;
       logic                  pwrite;
       logic [DATA_WIDTH-1:0] pwdata;
       logic [DATA_WIDTH-1:0] prdata;
       logic                  pready;
       logic                  pslverr;

       // Clock generation
       initial begin
           clk = 0;
           forever #(CLK_PERIOD/2) clk = ~clk;
       end

       // Reset generation
       initial begin
           rst_n = 0;
           #(CLK_PERIOD * 5);
           rst_n = 1;
           #(CLK_PERIOD);
       end

       // DUT instantiation
       my_dut #(
           .ADDR_WIDTH(ADDR_WIDTH),
           .DATA_WIDTH(DATA_WIDTH)
       ) u_dut (
           .pclk    (clk),
           .prst_n  (rst_n),
           .psel    (psel),
           .penable (penable),
           .pwrite  (pwrite),
           .paddr   (paddr),
           .pwdata  (pwdata),
           .prdata  (prdata),
           .pready  (pready),
           .pslverr (pslverr)
       );

       // VIP interface
       apb_if #(
           .ADDR_WIDTH(ADDR_WIDTH),
           .DATA_WIDTH(DATA_WIDTH)
       ) vip_if (
           .pclk   (clk),
           .prst_n (rst_n)
       );

       // Connect VIP interface to DUT
       assign vip_if.psel    = psel;
       assign vip_if.penable = penable;
       assign vip_if.pwrite  = pwrite;
       assign vip_if.paddr   = paddr;
       assign vip_if.pwdata  = pwdata;
       assign prdata         = vip_if.prdata;
       assign pready         = vip_if.pready;
       assign pslverr        = vip_if.pslverr;

       // VIP instances
       ApbMasterVIP #(
           .ADDR_WIDTH(ADDR_WIDTH),
           .DATA_WIDTH(DATA_WIDTH)
       ) master;

       ApbSlaveVIP #(
           .ADDR_WIDTH(ADDR_WIDTH),
           .DATA_WIDTH(DATA_WIDTH)
       ) slave;

       // Test sequence
       initial begin
           // Initialize VIPs
           master = new("master", vip_if);
           slave  = new("slave",  vip_if);

           // Wait for reset release
           @(posedge rst_n);
           #(CLK_PERIOD);

           // === Test 1: Basic Write/Read ===
           $info("=== Test 1: Basic Write/Read ===");
           master.write_req_single(.addr(32'h000), .data(32'hA5A5_A5A5));
           master.read_req_single (.addr(32'h000), .data(tmp_data));
           $info("Read data: 0x%0h", tmp_data);

           // === Test 2: Error Response ===
           $info("=== Test 2: Error Response ===");
           master.write_req_single(.addr(32'hFFF), .data(32'hDEAD_BEEF));
           // DUT should return PSLVERR for invalid address

           #(CLK_PERIOD * 20);
           $finish;
       end

       // Waveform dump
       initial begin
           $recordfile("dump.verilog");
           $recordvars();
       end
   endmodule
   ```

2. **生成 run.py** — 使用 VUnit 注册 testbench：

   ```python
   # tb/run.py
   # Auto-generated VUnit run script for my_dut
   import sys
   from pathlib import Path

   # Add sv-light-vip to path
   sv_vip_path = Path("../sv_vip")
   sys.path.insert(0, str(sv_vip_path))

   from sv_light_vip import add_vip_to_vunit
   from vunit import VUnit

   def main():
       vu = VUnit.from_argv()
       lib = vu.add_library("work")

       # Add DUT RTL sources
       lib.add_source_files("../rtl/*.sv")

       # Add VIP sources (APB protocol)
       add_vip_to_vunit(vu, lib, "apb_vip")

       # Add testbench
       lib.add_source_files("dut_tb.sv")

       vu.main()

   if __name__ == "__main__":
       main()
   ```

3. **生成 Makefile**（可选）— 提供 `make test` 入口：

   ```makefile
   # Makefile
   .PHONY: test test-gui clean

   test:
        python3 tb/run.py

   test-gui:
        python3 tb/run.py --gui

   clean:
        rm -rf vunit_out
   ```

4. **输出**: `tb/dut_tb.sv` + `tb/run.py` + `Makefile`（可选）

### Phase 4: 验证

```
输入: 生成的 testbench + run.py
```

1. **语法检查**:
   ```bash
   python3 tb/run.py --list 2>&1 | grep -E "ERROR|WARNING"
   ```

2. **运行仿真**:
   ```bash
   python3 tb/run.py
   ```

3. **检查结果**:
   - 所有测试用例通过（P=全部, S=0, F=0）
   - 波形文件已生成（可选）

4. **调试失败用例**:
   - 检查仿真日志中的错误信息
   - 使用 `--gui` 模式查看波形
   - 检查 DUT 接口时序是否与 VIP 匹配
   - 检查接口映射是否正确

5. **输出**: 仿真通过确认

### Phase 5: 文档

```
输入: 验证通过的 testbench
```

1. **生成 README** — 在 `tb/` 目录下创建使用说明：

   ```markdown
   # DUT 验证环境

   ## 概述
   基于 sv-light-vip 的 APB 验证环境，用于验证 my_dut 模块。

   ## 文件结构
   - `dut_tb.sv` — Testbench
   - `run.py` — VUnit 运行脚本

   ## 运行方法
   ```bash
   python3 tb/run.py
   ```

   ## 测试用例
   | 名称 | 描述 |
   |------|------|
   | basic_rw | 基本读写测试 |
   | error_resp | 错误响应测试 |
   | backpressure | 背压测试 |

   ## 依赖
   - sv-light-vip (APB VIP)
   - vunit_hdl
   - Modelsim/Questa
   ```

2. **输出**: `tb/README.md`

### Phase 6: 提交

```
输入: 验证通过的代码 + 文档
```

1. **查看修改状态**:
   ```bash
   git status
   ```

2. **精确添加文件**:
   ```bash
   git add tb/dut_tb.sv tb/run.py tb/README.md Makefile
   ```

3. **提交**:
   ```bash
   git commit -m "[test](dut): add APB verification environment for my_dut

   - Add auto-generated testbench with basic_rw/error_resp/backpressure tests
   - Add VUnit run.py with sv-light-vip integration
   - Add testbench usage documentation"
   ```

4. **输出**: 提交完成的代码

---

## 常见协议模板

### APB 验证模板

```python
# tb/run.py — APB 协议
from sv_light_vip import add_vip_to_vunit

vu = VUnit.from_argv()
lib = vu.add_library("work")
lib.add_source_files("../rtl/*.sv")
add_vip_to_vunit(vu, lib, "apb_vip")
lib.add_source_files("dut_tb.sv")
vu.main()
```

### AXI4-Lite 验证模板

```python
# tb/run.py — AXI4-Lite 协议
from sv_light_vip import add_vip_to_vunit

vu = VUnit.from_argv()
lib = vu.add_library("work")
lib.add_source_files("../rtl/*.sv")
add_vip_to_vunit(vu, lib, "axi4_lite_vip")
lib.add_source_files("dut_tb.sv")
vu.main()
```

### AXI4-Stream 验证模板

```python
# tb/run.py — AXI4-Stream 协议
from sv_light_vip import add_vip_to_vunit

vu = VUnit.from_argv()
lib = vu.add_library("work")
lib.add_source_files("../rtl/*.sv")
add_vip_to_vunit(vu, lib, "axi4_stream_vip")
lib.add_source_files("dut_tb.sv")
vu.main()
```

### SPI 验证模板

```python
# tb/run.py — SPI 协议
from sv_light_vip import add_vip_to_vunit

vu = VUnit.from_argv()
lib = vu.add_library("work")
lib.add_source_files("../rtl/*.sv")
add_vip_to_vunit(vu, lib, "spi_vip")
lib.add_source_files("dut_tb.sv")
vu.main()
```

### I2C 验证模板

```python
# tb/run.py — I2C 协议
from sv_light_vip import add_vip_to_vunit

vu = VUnit.from_argv()
lib = vu.add_library("work")
lib.add_source_files("../rtl/*.sv")
add_vip_to_vunit(vu, lib, "i2c_vip")
lib.add_source_files("dut_tb.sv")
vu.main()
```

### 多协议验证模板

```python
# tb/run.py — 多协议（如 AXI4-Lite 配置 + AXI4-Stream 数据）
from sv_light_vip import add_vip_sources

vu = VUnit.from_argv()
lib = vu.add_library("work")
lib.add_source_files("../rtl/*.sv")
add_vip_sources(vu, lib, ["axi4_lite_vip", "axi4_stream_vip"])
lib.add_source_files("dut_tb.sv")
vu.main()
```

---

## MCP Server 使用指南

### 启动 MCP Server

```bash
# 方式 1: stdio 模式（用于 Roo Code 等 AI 工具）
python3 $SV_LIGHT_VIP_PATH/mcp_server/server.py

# 方式 2: SSE 模式（用于 Web 端 AI 工具）
python3 $SV_LIGHT_VIP_PATH/mcp_server/server.py --transport sse --port 8765
```

### 可用工具

| 工具名 | 功能 | 适用场景 |
|--------|------|----------|
| `list_vips` | 列出所有可用 VIP | 选择协议时 |
| `get_vip_info` | 获取 VIP 详细信息 | 了解 VIP 组件和参数 |
| `get_vip_api` | 获取 VIP API 签名 | 编写 testbench 时查询 API |
| `get_vip_interface` | 获取 VIP 接口信号定义 | 接口映射时 |
| `generate_testbench` | 自动生成 testbench | 快速生成测试框架 |
| `generate_run_py` | 自动生成 VUnit run.py | 快速生成运行脚本 |

### Roo Code MCP 配置

在 Roo Code 设置中添加 MCP Server：

```json
{
  "mcpServers": {
    "sv-light-vip": {
      "command": "python3",
      "args": ["/path/to/sv_vip/mcp_server/server.py"],
      "env": {
        "SV_LIGHT_VIP_PATH": "/path/to/sv_vip"
      }
    }
  }
}
```

---

## 检查清单

### 环境检查
- [ ] `SV_LIGHT_VIP_PATH` 环境变量已设置
- [ ] sv-light-vip Python 包已安装（`pip install -e $SV_LIGHT_VIP_PATH`）
- [ ] vunit_hdl 已安装
- [ ] Modelsim/Questa 可用

### Testbench 生成
- [ ] DUT 接口映射正确
- [ ] 时钟和复位连接正确
- [ ] VIP 实例化正确
- [ ] 测试用例覆盖基本功能
- [ ] run.py 正确注册所有源文件

### 验证
- [ ] 语法检查通过
- [ ] 仿真全部通过（P=全部, S=0, F=0）
- [ ] 波形可查看（可选）

### 文档
- [ ] tb/README.md 已创建
- [ ] 测试用例说明完整
- [ ] 运行方法说明清晰

---

## 常见问题

### 1. VIP 路径找不到
```bash
# 检查 sv-light-vip 是否安装
python3 -c "import sv_light_vip; print(sv_light_vip.__file__)"
# 如果失败，手动安装
pip install -e /path/to/sv_vip
```

### 2. VUnit 找不到 VIP 源文件
确保 `add_vip_to_vunit()` 在添加 testbench 之前调用，因为 VUnit 需要先解析 VIP 的 package 文件。

### 3. 仿真超时
- 检查时钟是否正常翻转
- 检查复位是否已释放
- 检查 DUT 是否响应 VIP 的请求
- 检查接口映射是否正确（特别是 ready/valid 信号方向）

### 4. Modelsim 许可证错误
```bash
# 使用 Docker 运行
docker run --rm -v $(pwd):/work -w /work modelsim:v1 python3 tb/run.py
```
