onerror {resume}
quietly WaveActivateNextPane {} 0
add wave -noupdate /i2s_vip_tb/SAMPLE_WIDTH
add wave -noupdate /i2s_vip_tb/HALF_BCLK_CYCLES
add wave -noupdate /i2s_vip_tb/STIMULUS_COUNT
add wave -noupdate /i2s_vip_tb/clk
add wave -noupdate /i2s_vip_tb/rstn
add wave -noupdate -group i2s_link /i2s_vip_tb/i2s_link/clk
add wave -noupdate -group i2s_link /i2s_vip_tb/i2s_link/rstn
add wave -noupdate -group i2s_link /i2s_vip_tb/i2s_link/bclk
add wave -noupdate -group i2s_link /i2s_vip_tb/i2s_link/ws
add wave -noupdate -group i2s_link /i2s_vip_tb/i2s_link/sd
TreeUpdate [SetDefaultTree]
WaveRestoreCursors {{Cursor 1} {0 ps} 0}
quietly wave cursor active 1
configure wave -namecolwidth 180
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
WaveRestoreZoom {0 ps} {100 us}
