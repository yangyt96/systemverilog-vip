onerror {resume}
quietly WaveActivateNextPane {} 0
add wave -noupdate /uart_vip_tb/CLKS_PER_BIT
add wave -noupdate /uart_vip_tb/DATA_BITS
add wave -noupdate /uart_vip_tb/STIMULUS_COUNT
add wave -noupdate /uart_vip_tb/CONTINUOUS_FRAME_COUNT
add wave -noupdate /uart_vip_tb/INTER_TRANSACTION_PAUSE
add wave -noupdate /uart_vip_tb/clk
add wave -noupdate /uart_vip_tb/rstn
add wave -noupdate /uart_vip_tb/tx_vip
add wave -noupdate /uart_vip_tb/rx_vip
TreeUpdate [SetDefaultTree]
WaveRestoreCursors {{Cursor 1} {318965517 ps} 0}
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
