
# UVM VIP: AXI Stream Master Verification IP Project

A complete **UVM 1.2-based verification framework** for AXI Stream protocol testing, featuring a reusable Master VIP, comprehensive testbench infrastructure, and ModelSim/VUnit integration.

## Quick Start

### Prerequisites
- **Docker** with ModelSim image: `modelsim:20.1`
- **Python 3** with VUnit installed
- **Linux** with X11 support (for GUI mode)

### Run Simulations
```bash
cd axis_vip_tb
python3 run.py              # Run all tests
python3 run.py -g test_random  # Run specific test
python3 run.py --gui        # Run with ModelSim GUI
python3 run.py --help       # Show all options
```

### Docker Environment
```bash
docker run -it --rm \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v .:/workspace \
  modelsim:20.1
```

## Project Structure

```
axis_master/                        # AXI Stream Master VIP (UVM 1.2)
├── axis_master_defines.svh         # Global defines and parameters
├── axis_master_pkg.sv              # Main package with all VIP components
├── axis_master_test.sv             # Base test class
├── agent/
│   ├── axis_master_agent.sv        # Top-level agent orchestration
│   ├── axis_master_driver.sv       # Master interface driver
│   ├── axis_master_monitor.sv      # Passive bus monitor
│   └── axis_master_sequencer.sv    # Transaction sequencer
├── env/
│   ├── axis_master_env.sv          # UVM environment (scoreboard, coverage, etc.)
│   └── axis_master_interface.sv    # SystemVerilog interface definition
├── sequences/
│   ├── axis_master_seq_item.sv     # Transaction/sequence item definition
│   └── axis_master_sequences.sv    # Pre-built stimulus sequences
└── README.md                       # VIP-specific documentation

axis_vip_tb/                        # Test Infrastructure (VUnit)
├── run.py                          # VUnit test runner (main entry point)
├── tb/
│   └── tb_axis_master_vip.sv       # Top-level testbench
├── rtl/
│   └── axis_slave_dut.sv           # Simple AXI Stream slave (DUT for testing)
└── vunit_out/                      # Generated simulation outputs
    ├── modelsim/                   # ModelSim logs and database
    ├── preprocessed/               # Preprocessed source files
    └── test_output/                # Test reports and coverage

UVM/                                # UVM Reference Library
├── 1.1d/                           # UVM 1.1d release
├── 1.2/                            # UVM 1.2 release (used by this VIP)
├── 1800.2-2017/                    # IEEE 1800.2-2017 standard
└── 1800.2-2020/                    # IEEE 1800.2-2020 standard

doc/                                # Documentation
example_vunit/                      # Example VUnit testbench (reference)
```

## AXI Stream Protocol Support

The Master VIP fully supports the AXI Stream protocol with:

### Core Signals
- **tdata**: Data payload (configurable width, default 32 bits)
- **tvalid**: Valid signal (master asserts when data is valid)
- **tready**: Ready signal (slave asserts when ready to accept)
- **tlast**: End of burst indicator
- **tstrb**: Byte strobes (valid bytes in transaction)
- **tkeep**: Byte enable mask

### Optional Signals
- **tuser**: User-defined sideband data
- **tid**: Transaction ID for tracking
- **tdest**: Destination ID

### Protocol Features
- Back-pressure handling (tready/tvalid handshake)
- Burst transfer support (multiple transactions with tlast)
- Variable data width configuration
- Sideband signal support for extended use cases

## VIP Architecture

### UVM Hierarchy
```
axis_master_env (uvm_env)
├── axis_master_agent (uvm_agent)
│   ├── axis_master_sequencer (uvm_sequencer)
│   ├── axis_master_driver (uvm_driver) [active mode]
│   └── axis_master_monitor (uvm_monitor) [always active]
├── scoreboard (uvm_scoreboard)
└── coverage_collector (uvm_component)
```

### Key Components

| Component | Purpose | Mode |
|-----------|---------|------|
| **Driver** | Applies stimulus to DUT (tdata, tvalid, tlast, etc.) | Active |
| **Monitor** | Passively observes AXI Stream transactions | Passive (always) |
| **Sequencer** | Generates transaction streams from sequences | Active |
| **Agent** | Orchestrates driver, monitor, sequencer | Active/Passive |
| **Environment** | Contains agents, scoreboard, coverage | Top-level |

### Configuration

Use UVM config_db to customize VIP behavior:
```systemverilog
// Set data width (default 32)
axis_master_env::type_id::set_config_db("data_width", 64);

// Set address width (if using tdest)
axis_master_env::type_id::set_config_db("dest_width", 8);

// Enable coverage collection
axis_master_agent::type_id::set_config_db("collect_coverage", 1);
```

## Test Development

### Creating Custom Tests

```systemverilog
class my_custom_test extends axis_master_test;
    `uvm_component_utils(my_custom_test)
    
    function new(string name = "my_custom_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction
    
    task run_phase(uvm_phase phase);
        my_custom_seq seq;
        phase.raise_objection(this);
        
        seq = my_custom_seq::type_id::create("seq");
        seq.start(env.agent.sequencer);
        
        phase.drop_objection(this);
    endtask
endclass
```

### Built-in Sequences

The VIP provides pre-built sequences in `axis_master_sequences.sv`:
- **axis_master_random_seq**: Random transaction generation
- **axis_master_burst_seq**: Burst pattern generation
- **axis_master_idle_seq**: Insert idle cycles

### Running Specific Tests

```bash
cd axis_vip_tb
python3 run.py -g test_random          # Run test_random
python3 run.py -g test_burst           # Run test_burst
python3 run.py --list                  # List all available tests
```

## Simulation Tools

### VUnit
- **Entry point**: `axis_vip_tb/run.py`
- **Test orchestration**: Compiles, runs, and reports tests
- **GUI integration**: ModelSim visualization support
- **Coverage**: Can generate coverage reports

### ModelSim
- **Simulator**: VHDL/Verilog/SystemVerilog support
- **GUI**: Interactive waveform debugging
- **Coverage**: Code/functional coverage collection
- **Output**: `vunit_out/modelsim/` directory

### Docker Container
- **Image**: `modelsim:20.1`
- **Display**: X11 forwarding for GUI
- **Workspace**: Mounted at `/workspace`

## Debugging & Troubleshooting

### Simulation Won't Compile
1. Verify UVM path exists: `ls UVM/1.2/src/`
2. Check include directories in `run.py`
3. Verify SystemVerilog syntax in modified files
4. Try compilation only: `python3 run.py --compile`

### Tests Fail
1. Check ModelSim transcript: `vunit_out/modelsim/transcript*`
2. Examine UVM phase execution logs
3. Verify test sequence definition
4. Use `--gui` mode to inspect waveforms: `python3 run.py --gui -g <test_name>`

### Monitor Issues
1. Check signal names match interface definition in `axis_master_interface.sv`
2. Verify driver and monitor are connected to same interface instance
3. Inspect monitor sampling in `axis_master_monitor.sv`

### Driver Won't Apply Data
1. Verify DUT (slave) is ready to accept (tready asserted)
2. Check driver implementation in `axis_master_driver.sv`
3. Confirm sequencer is driving the driver via `seq_item_port`

## Key Files Reference

| File | Purpose | Modify For |
|------|---------|-----------|
| `axis_master_defines.svh` | Global parameters | Protocol width/configuration changes |
| `axis_master_pkg.sv` | Main package | Component imports, new classes |
| `axis_master_test.sv` | Base test | Test base behavior customization |
| `agent/axis_master_driver.sv` | Stimulus application | Protocol state machine, signal timing |
| `sequences/axis_master_seq_item.sv` | Transaction definition | New transaction fields |
| `sequences/axis_master_sequences.sv` | Pre-built sequences | New stimulus patterns |
| `axis_vip_tb/tb_axis_master_vip.sv` | Testbench | DUT instantiation, test instantiation |
| `axis_vip_tb/rtl/axis_slave_dut.sv` | DUT for testing | Reference slave behavior |

## Examples & References

- **Example VUnit testbench**: See `example_vunit/` for VHDL example structure
- **UVM documentation**: `UVM/1.2/docs/` and `UVM/1.2/src/` source
- **IEEE standard**: See `UVM/1800.2-2020/` for latest specification

## Extending the VIP

### Add New Sequence
1. Create class in `sequences/` extending `uvm_sequence#(axis_master_seq_item)`
2. Implement `body()` task to generate transactions
3. Register with factory: `\`uvm_object_utils(my_sequence)\``

### Add Coverage
1. Extend coverage in `env/axis_master_env.sv`
2. Sample transaction in monitor
3. Run tests and examine coverage report: `vunit_out/test_output/`

### Add Assertions
1. Add `assert` statements in `axis_master_interface.sv`
2. Assert protocol invariants (e.g., tvalid/tready behavior)
3. Run simulations to detect violations

## License

See [LICENSE](LICENSE) file for licensing information.

## Support & Documentation

- **VIP Details**: See [axis_master/README.md](axis_master/README.md)
- **UVM Standard**: Refer to IEEE 1800.2 specification
- **VUnit**: https://github.com/VUnit/vunit
- **ModelSim**: Mentor Graphics documentation
