#=
reo_structs:
- Julia version: 1.0.3
- Author: Sakshi Mishra
- Date: 2019-04-21
=#

using Revise
include("utils.jl")
include("reo_structs.jl")

jsonToVariable("./all_data_new.json")


pv = RenewableGenReo("PV", "PV", Int8(0), Int8(1), PowerSystems.Bus(),
TimeSeries.TimeArray(Dates.today(), ones(1)),
250.0, Int8.([1,1,1,1]), Int8.([0,1,0]),
TechReo((min=25.0, max=200.0),nothing,nothing,nothing),
EconGenReo([0.0], [0.0], [0.0], [(0.0,0.1)], nothing))


util =ThermalGenReo("UTIL", "UTIL", Int8(0), Int8(1), PowerSystems.Bus(),
TimeSeries.TimeArray(Dates.today(), ones(1)),[1,1,1,1], [0,1,0],0.96,
[1,0.6,1.1,0.98],[1,0.6,1.1,0.98], [100000],[1,2,3],0,
TechReo((min=25.0, max=200.0),nothing,nothing,nothing),
EconGenReo([0.0], [0.0], [0.0], [(0.0,0.1)], nothing))

batt= GenericBatteryReo("batt", Int8(0), PowerSystems.Bus(),
(min=0.0, max=0.9),(min=0.0, max=0.9), Float16(0.1), Float32(0.2), Float32(0.2),
Float16.([0.1,0.2]), Float16.([0.0,0.1]), EconBattReo(25.0,32.0))

load = StaticLoadReo("load1", Int8(0), PowerSystems.Bus(),
TimeSeries.TimeArray(Dates.today(), ones(1)),
50000.0, nothing)

println(pv)
