onerror {resume}
quietly WaveActivateNextPane {} 0
add wave -noupdate /axi4_stream_dut_tb/dut/DATA_WIDTH
add wave -noupdate /axi4_stream_dut_tb/dut/KEEP_WIDTH
add wave -noupdate /axi4_stream_dut_tb/dut/TID_WIDTH
add wave -noupdate /axi4_stream_dut_tb/dut/TDEST_WIDTH
add wave -noupdate /axi4_stream_dut_tb/dut/TUSER_WIDTH
add wave -noupdate /axi4_stream_dut_tb/dut/aclk
add wave -noupdate /axi4_stream_dut_tb/dut/aresetn
add wave -noupdate /axi4_stream_dut_tb/dut/s_axis_tdata
add wave -noupdate /axi4_stream_dut_tb/dut/s_axis_tvalid
add wave -noupdate /axi4_stream_dut_tb/dut/s_axis_tready
add wave -noupdate /axi4_stream_dut_tb/dut/s_axis_tkeep
add wave -noupdate /axi4_stream_dut_tb/dut/s_axis_tstrb
add wave -noupdate /axi4_stream_dut_tb/dut/s_axis_tlast
add wave -noupdate /axi4_stream_dut_tb/dut/s_axis_tid
add wave -noupdate /axi4_stream_dut_tb/dut/s_axis_tdest
add wave -noupdate /axi4_stream_dut_tb/dut/s_axis_tuser
add wave -noupdate /axi4_stream_dut_tb/dut/m_axis_tdata
add wave -noupdate /axi4_stream_dut_tb/dut/m_axis_tvalid
add wave -noupdate /axi4_stream_dut_tb/dut/m_axis_tready
add wave -noupdate /axi4_stream_dut_tb/dut/m_axis_tkeep
add wave -noupdate /axi4_stream_dut_tb/dut/m_axis_tstrb
add wave -noupdate /axi4_stream_dut_tb/dut/m_axis_tlast
add wave -noupdate /axi4_stream_dut_tb/dut/m_axis_tid
add wave -noupdate /axi4_stream_dut_tb/dut/m_axis_tdest
add wave -noupdate /axi4_stream_dut_tb/dut/m_axis_tuser
TreeUpdate [SetDefaultTree]
WaveRestoreCursors {{Cursor 1} {216748768 ps} 0}
quietly wave cursor active 1
configure wave -namecolwidth 150
configure wave -valuecolwidth 100
configure wave -justifyvalue left
configure wave -signalnamewidth 0
configure wave -snapdistance 10
configure wave -datasetprefix 0
configure wave -rowmargin 4
configure wave -childrowmargin 2
configure wave -gridoffset 0
configure wave -gridperiod 1
configure wave -griddelta 40
configure wave -timeline 0
configure wave -timelineunits us
update
WaveRestoreZoom {0 ps} {1 ms}
