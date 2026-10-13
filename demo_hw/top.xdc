# top.xdc
# Basic clock constraint for the top module.
#
# create_clock sets the clock period in nanoseconds. Frequency and
# period are related by: period_ns = 1000 / frequency_MHz
# A 100 MHz clock has a period of 1000 / 100 = 10 ns, which is the value
# used below. Tightening this period (a smaller number) makes timing
# harder to meet, which is a good way to intentionally generate a
# failing report to test Timing Scout with.

create_clock -period 10.000 -name clk [get_ports clk]
