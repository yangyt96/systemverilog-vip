onerror {resume}
quietly WaveActivateNextPane {} 0
add wave -noupdate /apb_vip_tb/ADDR_WIDTH
add wave -noupdate /apb_vip_tb/DATA_WIDTH
add wave -noupdate /apb_vip_tb/STIMULUS_COUNT
add wave -noupdate /apb_vip_tb/clk
add wave -noupdate /apb_vip_tb/rstn
add wave -noupdate -group apb_link /apb_vip_tb/apb_link/pclk
add wave -noupdate -group apb_link /apb_vip_tb/apb_link/presetn
add wave -noupdate -group apb_link /apb_vip_tb/apb_link/paddr
add wave -noupdate -group apb_link /apb_vip_tb/apb_link/psel
add wave -noupdate -group apb_link /apb_vip_tb/apb_link/penable
add wave -noupdate -group apb_link /apb_vip_tb/apb_link/pwrite
add wave -noupdate -group apb_link /apb_vip_tb/apb_link/pwdata
add wave -noupdate -group apb_link /apb_vip_tb/apb_link/pstrb
add wave -noupdate -group apb_link /apb_vip_tb/apb_link/pprot
add wave -noupdate -group apb_link /apb_vip_tb/apb_link/prdata
add wave -noupdate -group apb_link /apb_vip_tb/apb_link/pready
add wave -noupdate -group apb_link /apb_vip_tb/apb_link/pslverr
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
