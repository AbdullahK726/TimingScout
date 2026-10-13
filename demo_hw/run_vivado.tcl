# run_vivado.tcl
# Manual, non-project Vivado flow used to generate a real
# report_timing_summary report that can be uploaded to Timing Scout.
#
# Run this from the Vivado Tcl console or with:
#   vivado -mode batch -source run_vivado.tcl
#
# The Flask app never runs this script automatically. It is only here
# to show how a real timing report could be produced.

# Start an in-memory project (nothing is written to a project directory)
create_project -in_memory -part xc7a35tcpg236-1

# Read the SystemVerilog source for the demo datapath
read_verilog -sv top.sv

# Read the clock and I/O timing constraints
read_xdc top.xdc

# Tell Vivado which module is the top of the design
set_property top top [current_fileset]

# Run synthesis so the design has real logic and delays to analyze
synth_design -top top -part xc7a35tcpg236-1

# Run implementation (optimize, place, and route) so routing delays
# are included in the timing numbers, not just logic delays
opt_design
place_design
route_design

# Write the timing summary report that Timing Scout expects as input
report_timing_summary -file demo_timing_summary.rpt
