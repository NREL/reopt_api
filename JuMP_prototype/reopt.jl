## REopt port to Julia

# Data
include("utils.jl")
jsonToVariable("all_data.json")
#allData = importDict("all_data.json")

# Optimization
using JuMP
using Xpress
using IndexedTables

REopt = Model(with_optimizer(Xpress.Optimizer))

# Counting Sets
CapCostSegCount = 2
FuelBinCount = 1
DemandBinCount = 1
DemandMonthsBinCount = 1
BattLevelCount = 1
TimeStepScaling = 1.0
TimeStepCount =8760
Obj = 5
REoptTol = 5e-5
NumRatchets = 12


Seg = 1:CapCostSegCount
Points = 0:CapCostSegCount
Month = 1:12
Ratchets = 1:NumRatchets
FuelBin = 1:FuelBinCount
DemandBin = 1:DemandBinCount
DemandMonthsBin = 1:DemandMonthsBinCount
BattLevel=1:BattLevelCount
TimeStep=1:TimeStepCount
TimeStepBat=0:TimeStepCount

##### Sets and Parameter #####
##############################

#initializations from DAT1 ! constants
#Tech
#Load ##Had to change JSON from "load" to "Load"
TechIsGrid = set1param(Tech, TechIsGrid)
TechToLoadMatrix = set2param(Tech, Load, TechToLoadMatrix)
#TechClass
TurbineDerate = set1param(Tech, TurbineDerate)
TechToTechClassMatrix = set2param(Tech, TechClass, TechToTechClassMatrix)
#NMILRegime

#initializations from DAT2 ! economics
#r_tax_owner
#r_tax_offtaker
#pwf_om
#pwf_e
pwf_prod_incent = set1param(Tech, pwf_prod_incent)
LevelizationFactor = set1param((Tech), LevelizationFactor)
LevelizationFactorProdIncent = set1param(Tech, LevelizationFactorProdIncent)
StorageCostPerKW = set1param(BattLevel, [StorageCostPerKW])
StorageCostPerKWH = set1param(BattLevel, [StorageCostPerKWH])
OMperUnitSize = set1param(Tech, OMperUnitSize)
CapCostSlope = set2param(Tech, Seg, CapCostSlope)
CapCostYInt = set2param(Tech, Seg, CapCostYInt)
CapCostX = set2param(Tech, Points, CapCostX)
ProdIncentRate = set2param(Tech, Load, ProdIncentRate)
MaxProdIncent = set1param(Tech, MaxProdIncent)
MaxSizeForProdIncent = set1param(Tech, MaxSizeForProdIncent)
#two_party_factor
#analysis_years

#initializations from DAT3
#AnnualElecLoad

#initializations from DAT4
LoadProfile = set2param(Load, TimeStep, LoadProfile)

#initializations from DAT5 ! GIS
ProdFactor = set3param(Tech, Load, TimeStep, ProdFactor)

#initializations from DAT6 ! storage <--NEED A BAU VERSION WITH EMPTY PARAMS?
#StorageMinChargePcent
EtaStorIn = set2param(Tech, Load, EtaStorIn)
EtaStorOut = set1param(Load, EtaStorOut)
BattLevelCoef = set2param(BattLevel, 1:2, BattLevelCoef)
#InitSOC

#initializations from DAT7 ! maxsizes
MaxSize = set1param(Tech, MaxSize)
#MinStorageSizeKW
#MaxStorageSizeKW
#MinStorageSizeKWH
#MaxStorageSizeKWH
TechClassMinSize = set1param(TechClass, TechClassMinSize)
MinTurndown = set1param(Tech, MinTurndown)

#initializations from DAT8
#TimeStepRatchets = set1param(Ratchets, TimeStepRatchets) #not populated

#initializations from DAT9
#DemandRates = set2param(Ratchets, DemandBin, DemandRates) #not populated

#initializations from DAT10 ! FuelCost
FuelRate = set3param(Tech, FuelBin, TimeStep, FuelRate)
FuelAvail = set2param(Tech, FuelBin, FuelAvail)
#FixedMonthlyCharge
#AnnualMinCharge
#MonthlyMinCharge

#initializations from DAT11
ExportRates = set3param(Tech, Load, TimeStep, ExportRates)

#initializations from DAT12
TimeStepRatchetsMonth = set1param(Month, TimeStepRatchetsMonth)

#initializations from DAT13
DemandRatesMonth = set2param(Month, DemandMonthsBin, DemandRatesMonth)

#initializations from DAT14 ! LookbackMonthsAndPercent
#DemandLookbackMonths
#DemandLookbackPercent

#initializations from DAT15 ! UtilityTiers
MaxDemandInTier = set1param(DemandBin, MaxDemandInTier)
MaxDemandMonthsInTier = set1param(DemandMonthsBin, MaxDemandMonthsInTier)
MaxUsageInTier = set1param(FuelBin, MaxUsageInTier)

#initializations from DAT16
FuelBurnRateM = set3param(Tech, Load, FuelBin, FuelBurnRateM)
FuelBurnRateB = set3param(Tech, Load, FuelBin, FuelBurnRateB)

#initializations from DAT17  ! net metering
NMILLimits = set1param(NMILRegime, NMILLimits)
TechToNMILMapping = set2param(Tech, NMILRegime, TechToNMILMapping)

### Begin Variable Initialization ###
######################################

@variables REopt begin
    binNMLorIL[NMILRegime], Bin
    binSegChosen[Tech, Seg], Bin
    dvSystemSize[Tech, Seg] >= 0

 #!"exist" formatting
#forall (t in Tech,LD in Load,ts in TimeStep, s in Seg, fb in FuelBin | MaxSize(t)* LoadProfile(LD,ts) *  TechToLoadMatrix(t, LD) <> 0)  !* ceil( max(Loc, TimeStep) ProdFactor (t,LD,ts))
#	create (dvRatedProd (t,LD,ts,s,fb))   dvGrid[Load, TimeStep, DemandBin, FuelBin, DemandMonthsBin] >= 0
    #Exist formatting, causes difficulty writing constraints
    #dvRatedProd[t in Tech, LD in Load, ts in TimeStep, Seg, FuelBin; MaxSize[t] * LoadProfile[LD, ts] * TechToLoadMatrix[t, LD] !=0 ] >= 0

    dvGrid[Load, TimeStep, DemandBin, FuelBin, DemandMonthsBin] >= 0
    dvRatedProd[Tech, Load, TimeStep, Seg, FuelBin] >= 0
    dvProdIncent[Tech] >= 0
    binProdIncent[Tech], Bin
    binSingleBasicTech[Tech,TechClass], Bin
    dvPeakDemandE[Ratchets, DemandBin] >= 0
    dvPeakDemandEMonth[Month, DemandMonthsBin] >= 0
    dvElecToStor[TimeStep] >= 0
    dvElecFromStor[TimeStep] >= 0
    dvStoredEnergy[TimeStepBat] >= 0
    dvStorageSizeKWH[BattLevel] >= 0
    dvStorageSizeKW[BattLevel] >= 0
    dvMeanSOC >= 0
    binBattCharge[TimeStep], Bin
    binBattDischarge[TimeStep], Bin
    dvFuelCost[Tech, FuelBin]
    dvFuelUsed[Tech, FuelBin]
    binTechIsOnInTS[Tech, TimeStep], Bin
    MinChargeAdder >= 0
    binDemandTier[Ratchets, DemandBin], Bin
    binDemandMonthsTier[Month, DemandMonthsBin], Bin
    binUsageTier[Month, FuelBin], Bin
    dvPeakDemandELookback >= 0
    binBattLevel[BattLevel], Bin

# ADDED due to implied types
    ElecToBatt[Tech] >= 0
    UsageInTier[Month, FuelBin] >= 0
    TotalTechCapCosts >= 0
    TotalStorageCapCosts >= 0
    TotalOMCosts >= 0
    TotalEnergyCharges >= 0
    DemandTOUCharges >= 0
    DemandFlatCharges >= 0
    TotalDemandCharges >= 0
    TotalFixedCharges >= 0
    TotalEnergyExports >= 0
    TotalProductionIncentive >= 0
end



### Begin Constraints###
########################
@constraints(REopt, begin
#!!!! Fuel tracking
#! Define dvFuelUsed by each tech by summing over timesteps.  Constrain it to be less than FuelAvail.
#forall (t in Tech, fb in FuelBin) do
#     sum (ts in TimeStep, LD in Load, s in Seg |exists (dvRatedProd (t,LD,ts,s,fb)))
#     	ProdFactor(t,LD,ts) * LevelizationFactor(t) * dvRatedProd (t,LD,ts,s,fb) * FuelBurnRateM(t,LD,fb) * TimeStepScaling  +
#     sum(ts in TimeStep, LD in Load)
#     	binTechIsOnInTS(t,ts) * FuelBurnRateB(t,LD,fb) * TimeStepScaling = dvFuelUsed(t,fb)
#
#	dvFuelUsed(t,fb) <= FuelAvail(t,fb)
#end-do
    [t in Tech, fb in FuelBin],
    sum(ProdFactor[t,LD,ts] * LevelizationFactor[t] * dvRatedProd[t,LD,ts,s,fb] * FuelBurnRateM[t,LD,fb] * TimeStepScaling
        for ts in TimeStep, LD in Load, s in Seg) +
    sum(binTechIsOnInTS[t,ts] * FuelBurnRateB[t,LD,fb] * TimeStepScaling
        for ts in TimeStep, LD in Load) == dvFuelUsed[t,fb]
    [t in Tech, fb in FuelBin],
    dvFuelUsed[t,fb] <= FuelAvail[t,fb]

#! FuelUsed * FuelRate = FuelCost.  Since FuelRate can vary by timestep, cannot use dvFuelUsed in the following definition
#forall (t in Tech, fb in FuelBin) do
#     sum (ts in TimeStep, LD in Load, s in Seg |exists (dvRatedProd (t,LD,ts,s,fb)))
#     	ProdFactor(t, LD, ts) * LevelizationFactor(t) * dvRatedProd (t,LD,ts,s,fb) * FuelBurnRateM(t,LD,fb) * TimeStepScaling * FuelRate(t,fb,ts) * pwf_e +
#     sum(ts in TimeStep, LD in Load)
#     	binTechIsOnInTS(t,ts) * FuelBurnRateB(t,LD,fb) * TimeStepScaling * FuelRate(t,fb,ts) * pwf_e = dvFuelCost(t,fb)
#end-do
    [t in Tech, fb in FuelBin],
    sum(ProdFactor[t, LD, ts] * LevelizationFactor[t] * dvRatedProd[t,LD,ts,s,fb] * FuelBurnRateM[t,LD,fb] * TimeStepScaling * FuelRate[t,fb,ts] * pwf_e
        for ts in TimeStep, LD in Load, s in Seg) +
    sum(binTechIsOnInTS[t,ts] * FuelBurnRateB[t,LD,fb] * TimeStepScaling * FuelRate[t,fb,ts] * pwf_e
        for ts in TimeStep, LD in Load) == dvFuelCost[t,fb]

#!! The following 2 constraints define binTechIsOnInTS to be the binary corollary to dvRatedProd,
#!! i.e. binTechIsOnInTS = 1 for dvRatedProd > 0, and binTechIsOnInTS = 0 for dvRatedProd = 0
#!CONSTRAINT 4A
#forall (t in Tech, ts in TimeStep) do
#  sum (LD in Load, s in Seg, fb in FuelBin | exists(dvRatedProd (t,LD,ts,s,fb)))
#  		ProdFactor (t,LD,ts) * dvRatedProd (t,LD,ts,s,fb) <= MaxSize(t) * 100 * binTechIsOnInTS (t,ts)
#!CONSTRAINT 5A
#   sum (s in Seg) (MinTurndown(t) * dvSystemSize (t,s)) -
#  		sum (LD in Load, s in Seg, fb in FuelBin | exists (dvRatedProd (t,LD,ts,s,fb)))
#  		dvRatedProd (t,LD,ts,s,fb) <= MaxSize(t) * (1 - binTechIsOnInTS (t,ts))
#end-do

    [t in Tech, ts in TimeStep],
    sum(ProdFactor[t,LD,ts] * dvRatedProd[t,LD,ts,s,fb] for LD in Load, s in Seg, fb in FuelBin) <=
    MaxSize[t] * 100 * binTechIsOnInTS[t,ts]

#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#
#!the state of the storage system at the beginning is 0
#
#	! boundary condition.  State of charge must begin and end the same.
#	dvStoredEnergy(0) = InitSOC * sum(b in BattLevel) dvStorageSizeKWH(b) / TimeStepScaling !SOCt0(l) !dvStoredEnergy(TimeStepCount)
#	!next to lines set the SOC of the battery at time of GridOutage
#	sum(b in BattLevel) dvStorageSizeKWH(b) <=  MaxStorageSizeKWH
#	sum(b in BattLevel) dvStorageSizeKWH(b) >=  MinStorageSizeKWH
#	sum(b in BattLevel) dvStorageSizeKW(b) <=  MaxStorageSizeKW
#	sum(b in BattLevel) dvStorageSizeKW(b) >= MinStorageSizeKW

    MinStorageSizeKWH <= sum(dvStorageSizeKWH[b] for b in BattLevel) <=  MaxStorageSizeKWH
    MinStorageSizeKW <= sum(dvStorageSizeKW[b] for b in BattLevel) <=  MaxStorageSizeKW

#forall ( ts in TimeStep) do
#	! Electricity to be stored is the sum of the electricity in the S-bin for that timestep
#	dvElecToStor( ts) = (sum(t in Tech, s in Seg, fb in FuelBin | exists (dvRatedProd(t,"1S",ts,s,fb))) ProdFactor(t,"1S",ts) * LevelizationFactor(t) * dvRatedProd (t,"1S",ts,s,fb) * EtaStorIn(t,"1S"))
#	! state of charge at each timestep is sum of previous state and electiricy coming in, and less electricity going out
#	dvStoredEnergy(ts) =   dvStoredEnergy(ts-1) +  dvElecToStor( ts) - dvElecFromStor(ts) / EtaStorOut("1S")
#	! energy coming out of the storage system cannot be greater than the current state of charge
#	dvElecFromStor(ts) / EtaStorOut("1S") <=  dvStoredEnergy(ts-1)
#	! the state of charge always has to be greater than 0
#	dvStoredEnergy(ts) >=  StorageMinChargePcent * sum(b in BattLevel) dvStorageSizeKWH(b) / TimeStepScaling  ! / TimeStepScaling
#	dvElecFromStor( ts) >= 0
#end-do

    [ts in TimeStep],
	dvElecToStor[ts] == sum(ProdFactor[t,LD,ts] * LevelizationFactor[t] * dvRatedProd[t,LD,ts,s,fb] * EtaStorIn[t,LD]
                            for t in Tech, LD in [Symbol("1S")], s in Seg, fb in FuelBin)
    [ts in TimeStep],
	dvStoredEnergy[ts] == dvStoredEnergy[ts-1] + dvElecToStor[ts] - dvElecFromStor[ts] / EtaStorOut[Symbol("1S")]
    [ts in TimeStep],
	dvElecFromStor[ts] / EtaStorOut[Symbol("1S")] <=  dvStoredEnergy[ts-1]
    [ts in TimeStep],
	dvStoredEnergy[ts] >=  StorageMinChargePcent * sum(dvStorageSizeKWH[b] / TimeStepScaling for b in BattLevel)
    [ts in TimeStep],
	dvElecFromStor[ts] >= 0

#forall ( ts in TimeStep )  do
#	sum(b in BattLevel) dvStorageSizeKW(b) >=  dvElecToStor( ts)
#	sum(b in BattLevel) dvStorageSizeKW(b) >=  dvElecFromStor( ts)
#end-do

    [ts in TimeStep],
	sum(dvStorageSizeKW[b] for b in BattLevel) >=  dvElecToStor[ts]
    [ts in TimeStep],
	sum(dvStorageSizeKW[b] for b in BattLevel) >=  dvElecFromStor[ts]

#dvMeanSOC = sum(ts in TimeStep) dvStoredEnergy(ts) / TimeStepCount

    dvMeanSOC == sum(dvStoredEnergy[ts] / TimeStepCount for ts in TimeStep)

#! the physical size of the storage system is the max amount of charge at any timestep.
#forall (  ts in TimeStep) do
#	sum(b in BattLevel) dvStorageSizeKWH(b) >=  dvStoredEnergy(ts) * TimeStepScaling
#end-do

    [ts in TimeStep],
	sum(dvStorageSizeKWH[b] for b in BattLevel) >=  dvStoredEnergy[ts] * TimeStepScaling

#!Prevent storage from charging and discharging within same timestep
#forall ( ts in TimeStep) do
#  dvElecToStor(ts) <= MaxStorageSizeKW * binBattCharge(ts)
#  dvElecFromStor(ts) <= MaxStorageSizeKW * binBattDischarge(ts)
#  binBattDischarge(ts) + binBattCharge(ts) <= 1
#  binBattCharge (ts) is_binary
#  binBattDischarge (ts) is_binary
#end-do

    [ts in TimeStep],
    dvElecToStor[ts] <= MaxStorageSizeKW * binBattCharge[ts]
    [ts in TimeStep],
    dvElecFromStor[ts] <= MaxStorageSizeKW * binBattDischarge[ts]
    [ts in TimeStep],
    binBattDischarge[ts] + binBattCharge[ts] <= 1

#forall ( t in Tech) do
#	ElecToBatt(t) := sum(ts in TimeStep,  s in Seg, fb in FuelBin) dvRatedProd(t,"1S",ts,s,fb) * ProdFactor(t,"1S",ts) * LevelizationFactor(t)
#end-do

    [t in Tech],
	ElecToBatt[t] == sum(dvRatedProd[t,LD,ts,s,fb] * ProdFactor[t,LD,ts] * LevelizationFactor[t]
                        for ts in TimeStep, LD in [Symbol("1S")], s in Seg, fb in FuelBin)

#forall ( b in BattLevel) do
#   !!!!!!!NEED TO ADD THIS TO FORMULATION!!!!!!!!
#	BattLevelCoef(b,1)*sum(t in Tech | TechIsGrid(t)=1) ElecToBatt(t)-sum(t in Tech | TechIsGrid(t)<>1)BattLevelCoef(b,2)*ElecToBatt(t)   <= (1-binBattLevel(b)) *MaxStorageSizeKWH/TimeStepScaling*365*2  !assume that the maximum size battery can make 2 complete cycles per day.  May need to bump this up in select situations
#	binBattLevel(b) is_binary
#end-do

#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#!! This section is declaring binary variables and constraining them
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#
#!CONSTRAINT 2
#forall (t in Tech) do
#   sum (s in Seg) binSegChosen (t,s) = 1
#end-do

    [t in Tech],
    sum(binSegChosen[t,s] for s in Seg) == 1

#!CONSTRAINT 3
#! can only hve one tech from each tech class
#forall ( b in TechClass) do
#   sum (t in Tech) binSingleBasicTech (t,b) <= 1
#end-do

    [b in TechClass],
    sum(binSingleBasicTech[t,b] for t in Tech) <= 1

#!binary declarations
#forall ( t in Tech, b in TechClass) binSingleBasicTech (t,b) is_binary
#forall ( t in Tech, s in Seg) binSegChosen(t, s) is_binary
#forall ( t in Tech, ts in TimeStep) binTechIsOnInTS(t,ts) is_binary
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#!! End declaring binary variables and constraining them
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#
#forall (b in BattLevel) do
#   dvStorageSizeKWH(b) <= MaxStorageSizeKWH* binBattLevel(b)
#   dvStorageSizeKW(b) <= MaxStorageSizeKW* binBattLevel(b)
#end-do

    [b in BattLevel],
    dvStorageSizeKWH[b] <= MaxStorageSizeKWH * binBattLevel[b]
    [b in BattLevel],
    dvStorageSizeKW[b] <= MaxStorageSizeKW * binBattLevel[b]

#sum(b in BattLevel) binBattLevel(b) = 1

    sum(binBattLevel[b] for b in BattLevel) == 1

#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#!! CapCost constraints
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#
#! Determine which segment of the PWL cost curve.  binSegChosen is 1 for that segment, 0 else.
#forall (t in Tech, s in Seg) do
#!CONSTRAINT 20
#   dvSystemSize (t,s) <= CapCostX (t,s)   * binSegChosen (t,s)
#!CONSTRAINT 21
#   dvSystemSize (t,s) >= CapCostX (t,s-1) * binSegChosen (t,s)
#end-do

    [t in Tech, s in Seg],
    dvSystemSize[t,s] <= CapCostX[t,s] * binSegChosen[t,s]
    [t in Tech, s in Seg],
    dvSystemSize[t,s] >= CapCostX[t,s-1] * binSegChosen[t,s]

#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#!! End CapCost constraints
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#!  Production Incentive Cap Module
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#
#forall (t in Tech) binProdIncent (t) is_binary
#
#!CONSTRAINT 22
#! Number 1: The Production Incentive can't exceed a certain dollar max (and is "0" if system size is too big)
#forall (t in Tech) dvProdIncent (t) <= binProdIncent (t) * MaxProdIncent (t) * pwf_prod_incent(t)

    [t in Tech],
    dvProdIncent[t] <= binProdIncent[t] * MaxProdIncent[t] * pwf_prod_incent[t]

#!CONSTRAINT 23
#! Number 2: Calculate the production incentive based on the energy produced.  Then dvProdIncent must be less than that.
#! added LD to Prod Incent ExportRates 8912
#forall (t in Tech) do
#     dvProdIncent (t) <= sum (LD in Load, ts in TimeStep, s in Seg, fb in FuelBin |exists (dvRatedProd (t,LD,ts,s,fb)))
#     	ProdFactor(t, LD, ts) * LevelizationFactorProdIncent(t) *  dvRatedProd (t,LD,ts,s,fb) * TimeStepScaling * ProdIncentRate (t, LD) * pwf_prod_incent(t)
#end-do

    [t in Tech],
    dvProdIncent[t] <= sum(ProdFactor[t, LD, ts] * LevelizationFactorProdIncent[t] * dvRatedProd[t,LD,ts,s,fb] *
                           TimeStepScaling * ProdIncentRate[t, LD] * pwf_prod_incent[t]
                           for LD in Load, ts in TimeStep, s in Seg, fb in FuelBin)


#!CONSTRAINT 24
#! Number 3: If system size is bigger than MaxSizeForProdIncent, binProdIncent is 0, meaning you don't get the Prod Incent.
#forall (t in Tech, LD in Load,ts in TimeStep  ) do
#    sum (s in Seg) dvSystemSize (t,s) <= MaxSizeForProdIncent (t) + MaxSize(t) * (1 - binProdIncent (t))
#end-do

    [t in Tech, LD in Load,ts in TimeStep],
    sum(dvSystemSize[t,s] for s in Seg) <= MaxSizeForProdIncent[t] + MaxSize[t] * (1 - binProdIncent[t])

#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#!  End Production Incentive Cap Module
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#!! This section defining system size and production constraints
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#
# !!System size cannot exceed MaxSize and must equal or exceed MinSize
# !CONSTRAINT 27
#forall (t in Tech,s in Seg)   dvSystemSize (t,s) <=  MaxSize (t)
#

    [t in Tech, s in Seg],
    dvSystemSize[t,s] <=  MaxSize[t]

#forall (b in TechClass) do
#    sum (t in Tech, s in Seg) dvSystemSize(t, s) * TechToTechClassMatrix(t,b) >= TechClassMinSize(b)
#end-do

    [b in TechClass],
    sum(dvSystemSize[t, s] * TechToTechClassMatrix[t,b] for t in Tech, s in Seg) >= TechClassMinSize[b]

#!!dvRatedProduction must be >= 0, or if MinTurndown is > 0, use semi-continuous variable
#!CONSTRAINT 27a
#forall (t in Tech, LD in Load, ts in TimeStep, s in Seg, fb in FuelBin | MinTurndown(t) = 0 and exists (dvRatedProd (t,LD,ts,s,fb))) do
#    dvRatedProd(t,LD,ts,s,fb) >= 0
#end-do
#############NEED TO ADD############################
#forall (t in Tech, LD in Load, ts in TimeStep, s in Seg, fb in FuelBin | MinTurndown(t) > 0 and exists (dvRatedProd (t,LD,ts,s,fb))) do
#    dvRatedProd(t,LD,ts,s,fb) is_semcont MinTurndown(t)
#end-do
#!Per conversation with DC 7 6 12, changed below line to following 2 lines to capture size limit constraint based only on
#! electric output of a CoGen with mandatory thermal tech
#!For most techs, Rated Production across all loads cannot exceed System size
#!CONSTRAINT 33A
#forall (t in Tech,s in Seg,ts in TimeStep)  !for variable effiency gensets
#	 sum (LD in Load, fb in FuelBin |exists (dvRatedProd (t,LD,ts,s,fb))) dvRatedProd (t,LD,ts,s,fb) <= dvSystemSize (t, s)
#

    [t in Tech, s in Seg, ts in TimeStep],
    sum(dvRatedProd[t,LD,ts,s,fb] for LD in Load, fb in FuelBin) <= dvSystemSize[t, s]

#!CONSTRAINT 35
#! sum of everything but retail electric produced by all techs must be less than max load for each fuel type
#!TS 31513 should this exclude SHW?
#forall (LD in Load,ts in TimeStep | LD <> "1R" and LD <>"1S") do
#  sum (t in Tech, s in Seg, fb in FuelBin |exists (dvRatedProd (t,LD,ts,s,fb)))
#  		 ProdFactor (t,LD,ts) * LevelizationFactor(t) * dvRatedProd (t,LD,ts,s,fb) <= LoadProfile (LD,ts)
#end-do

    [LD in Load, ts in TimeStep; LD != "1R" && LD != "1S"],
    sum(ProdFactor[t,LD,ts] * LevelizationFactor[t] * dvRatedProd[t,LD,ts,s,fb]
        for t in Tech, s in Seg, fb in FuelBin) <= LoadProfile[LD,ts]

#!CONSTRAINT 38
#!companion to the above.  Electric load can be met from generation OR from the storage
#forall (LD in Load,ts in TimeStep  | LD = "1R") do
#  sum (t in Tech, s in Seg,fb in FuelBin |exists (dvRatedProd (t,LD,ts,s,fb)) ) dvRatedProd (t,LD,ts,s,fb) * ProdFactor (t,LD,ts) * LevelizationFactor(t) + dvElecFromStor( ts) >=
#  		  LoadProfile (LD,ts)
#end-do

##########NEED TO UNCOMMENT ELECFROM##############3
    [LD in Load, ts in TimeStep; LD == Symbol("1R")],
    sum(dvRatedProd[t,LD,ts,s,fb] * ProdFactor[t,LD,ts] * LevelizationFactor[t] + dvElecFromStor[ts]
        for t in Tech, s in Seg, fb in FuelBin) >= LoadProfile[LD,ts]
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#!! End system size and production constraints
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#!!!!  Net Meter Module
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#
# forall ( n in NMILRegime) binNMLorIL(n) is_binary
#
# !can only be in regime at a time.
# !CONSTRAINT 43
#sum (n in NMILRegime) binNMLorIL(n) = 1

    sum(binNMLorIL[n] for n in NMILRegime) == 1

#! The sum of the electricity output of all techs must be less than the limit for the regime
#!CONSTRAINT 44
#forall (n in NMILRegime | n <> "AboveIL") do
#      sum (t in Tech, s in Seg)
#      		TechToNMILMapping (t,n)*TurbineDerate(t)*dvSystemSize(t, s) <= NMILLimits(n) * binNMLorIL(n)
#end-do

    [n in NMILRegime; n != :AboveIL],
    sum(TechToNMILMapping[t,n] * TurbineDerate[t] * dvSystemSize[t,s]
        for t in Tech, s in Seg) <= NMILLimits[n] * binNMLorIL[n]

####NEED TO ADD###
#indicator(-1, binNMLorIL("AboveIL"), sum(t in Tech, s in Seg) TechToNMILMapping(t,"AboveIL") * TurbineDerate(t) * dvSystemSize(t, s) <= 0)

#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#!!!!  Demand Rate Module
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#
#forall ( LD in Load, fb in FuelBin, ts in TimeStep) do
#	sum(s in Seg) dvRatedProd("UTIL1",LD,ts,s,fb) = sum(db in DemandBin, dbm in DemandMonthsBin) dvGrid(LD,ts,db,fb,dbm)
#end-do

    [t in [Symbol("UTIL1")], LD in Load, fb in FuelBin, ts in TimeStep],
	sum(dvRatedProd[t,LD,ts,s,fb] for s in Seg) == sum(dvGrid[LD,ts,db,fb,dbm] for db in DemandBin, dbm in DemandMonthsBin)

#! Compute tiered energy rates
#forall (fb in FuelBin, m in Month)  do
#	UsageInTier(m, fb) :=  sum(LD in Load, ts in TimeStepRatchetsMonth(m), s in Seg) dvRatedProd("UTIL1",LD,ts,s,fb)
#   	UsageInTier(m, fb) >= 0
#end-do

    [t in [Symbol("UTIL1")], fb in FuelBin, m in Month],
	UsageInTier[m, fb] ==  sum(dvRatedProd[t,LD,ts,s,fb] for LD in Load, ts in TimeStepRatchetsMonth[m], s in Seg)


#forall (fb in FuelBin, m in Month) do
#	binUsageTier(m, fb) is_binary
#end-do
#
#forall (m in Month, fb in FuelBin | fb < FuelBinCount) do
#    UsageInTier(m, fb) <= binUsageTier(m, fb) * MaxUsageInTier(fb)
#end-do

    [m in Month, fb in FuelBin; fb < FuelBinCount],
    UsageInTier[m, fb] <= binUsageTier[m, fb] * MaxUsageInTier[fb]

####NEED TO ADD
#forall (m in Month) do
#	indicator(-1, binUsageTier(m, FuelBinCount), UsageInTier(m, FuelBinCount) <= 0)
#end-do
#forall (fb in FuelBin | fb >= 2, m in Month) do
#	binUsageTier(m, fb) - binUsageTier(m, fb-1) <= 0
#	binUsageTier(m, fb) * MaxUsageInTier(fb-1) - UsageInTier(m, fb-1) <= 0
#end-do

    [fb in FuelBin, m in Month; fb >= 2],
	binUsageTier[m, fb] - binUsageTier[m, fb-1] <= 0

    [fb in FuelBin, m in Month; fb >= 2],
	binUsageTier[m, fb] * MaxUsageInTier[fb-1] - UsageInTier[m, fb-1] <= 0

#! Compute tiered demand rates
#forall (db in DemandBin, r in Ratchets) do
#	binDemandTier(r, db) is_binary
#end-do
#forall (db in DemandBin, r in Ratchets | db < DemandBinCount) do
#	dvPeakDemandE(r, db) <= binDemandTier(r,db) * MaxDemandInTier(db)
#end-do

    [db in DemandBin, r in Ratchets; db < DemandBinCount],
    dvPeakDemandE[r, db] <= binDemandTier[r,db] * MaxDemandInTier[db]

#### NEED TO ADD
#forall (r in Ratchets) do
#	indicator(-1, binDemandTier(r, DemandBinCount), dvPeakDemandE(r, DemandBinCount) <= 0)
#end-do
#forall ( db in DemandBin | db >= 2, r in Ratchets) do
#	binDemandTier(r, db) - binDemandTier(r, db-1) <= 0
#	binDemandTier(r, db)*MaxDemandInTier(db-1) - dvPeakDemandE(r, db-1) <= 0
#end-do


    [db in DemandBin, r in Ratchets; db >= 2],
    binDemandTier[r, db] - binDemandTier[r, db-1] <= 0

    [db in DemandBin, r in Ratchets; db >= 2],
    binDemandTier[r, db]*MaxDemandInTier[db-1] - dvPeakDemandE[r, db-1] <= 0

#forall ( db in DemandBin, r in Ratchets, ts in TimeStepRatchets(r))  do
#	dvPeakDemandE(r,db) >= sum(LD in Load, fb in FuelBin, dbm in DemandMonthsBin) dvGrid(LD,ts,db,fb,dbm)
#   	dvPeakDemandE(r,db) >= 0
#   	dvPeakDemandE(r,db) >= DemandLookbackPercent * dvPeakDemandELookback
#end-do


####### NEED UPDATED JSON FOR THESE
#    [db in DemandBin, r in Ratchets, ts in TimeStepRatchets[r]],
#	dvPeakDemandE[r,db] >= sum(dvGrid[LD,ts,db,fb,dbm] for LD in Load, fb in FuelBin, dbm in DemandMonthsBin)
#
#    [db in DemandBin, r in Ratchets, ts in TimeStepRatchets[r]],
#   	dvPeakDemandE[r,db] >= 0
#
#    [db in DemandBin, r in Ratchets, ts in TimeStepRatchets[r]],
#   	dvPeakDemandE[r,db] >= DemandLookbackPercent * dvPeakDemandELookback

#! Compute tiered monthly demand rates
#forall (dbm in DemandMonthsBin, m in Month) do
#	binDemandMonthsTier(m, dbm) is_binary
#end-do
#forall ( dbm in DemandMonthsBin, m in Month | dbm < DemandMonthsBinCount) do
#	dvPeakDemandEMonth(m, dbm) <= binDemandMonthsTier(m,dbm) * MaxDemandMonthsInTier(dbm)
#end-do

    [dbm in DemandMonthsBin, m in Month; dbm < DemandMonthsBinCount],
	dvPeakDemandEMonth[m, dbm] <= binDemandMonthsTier[m,dbm] * MaxDemandMonthsInTier[dbm]

### NEED TO ADD
#forall (m in Month) do
#	indicator(-1, binDemandMonthsTier(m, DemandMonthsBinCount), dvPeakDemandEMonth(m, DemandMonthsBinCount) <= 0)
#end-do

#forall ( dbm in DemandMonthsBin | dbm >= 2, m in Month) do
#	binDemandMonthsTier(m, dbm) - binDemandMonthsTier(m, dbm-1) <= 0
#	binDemandMonthsTier(m, dbm)*MaxDemandMonthsInTier(dbm-1) <= dvPeakDemandEMonth(m, dbm-1) ! enforces full bins
#end-do

    [dbm in DemandMonthsBin, m in Month; dbm >= 2],
	binDemandMonthsTier[m, dbm] - binDemandMonthsTier[m, dbm-1] <= 0

    [dbm in DemandMonthsBin, m in Month; dbm >= 2],
	binDemandMonthsTier[m, dbm] * MaxDemandMonthsInTier[dbm-1] <= dvPeakDemandEMonth[m, dbm-1]

#forall ( dbm in DemandMonthsBin, m in Month, ts in TimeStepRatchetsMonth(m))  do
#	dvPeakDemandEMonth(m, dbm) >=  sum(LD in Load, db in DemandBin, fb in FuelBin) dvGrid(LD,ts,db,fb,dbm) ! validate
#   	dvPeakDemandEMonth(m, dbm) >= 0
#end-do

    [dbm in DemandMonthsBin, m in Month, ts in TimeStepRatchetsMonth[m]],
	dvPeakDemandEMonth[m, dbm] >=  sum(dvGrid[LD,ts,db,fb,dbm] for LD in Load, db in DemandBin, fb in FuelBin)

#! find the peak demand of the lookback months (lbm)
#forall (LD in Load, lbm in DemandLookbackMonths)  do
#	dvPeakDemandELookback >= sum(dbm in DemandMonthsBin) dvPeakDemandEMonth(lbm, dbm)
#end-do

####NEED UPDATED JSON
#    [LD in Load, lbm in DemandLookbackMonths],
#	dvPeakDemandELookback >= sum(dvPeakDemandEMonth[lbm, dbm] for dbm in DemandMonthsBin)

#!! 1/2/13  TS  Sum of Electric R and W must be less than the Site Load for the year.
#!! Once site load is met, excess electricity goes into X bin with lower sellback rate
#!!4313 TS.  Adding elec penalty to annual site load
#!!41513 TS.  Excluding Grid.
#
#   sum (t in Tech, LD in Load, ts in TimeStep, s in Seg, fb in FuelBin | exists (dvRatedProd(t,LD,ts,s,fb)) and (LD="1R" or LD="1W" or LD="1S") and TechIsGrid(t) = 0)

    sum(dvRatedProd[t,LD,ts,s,fb] * ProdFactor[t, LD, ts] * LevelizationFactor[t] *  TimeStepScaling
        for t in Tech, LD in [Symbol("1R"), Symbol("1W"), Symbol("1S")],
        ts in TimeStep, s in Seg, fb in FuelBin if TechIsGrid[t] == 0) <=  AnnualElecLoad

#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#!!!!!!!  End Electric Net Zero Module
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#
#! Added 8912, modified 81012 by TS
#! Can only have one tech from each tech class
#!CONSTRAINT 46
######NEED TO ADD
#forall (t in Tech,  b in TechClass) do
#   indicator(-1, binSingleBasicTech (t,b), sum (s in Seg) dvSystemSize (t, s) * TechToTechClassMatrix(t,b) <=  0)
#end-do

#!Curtailment 91212 added by TS written by Helwig.  Corrected by TS 91612.
#!This prevents PV and wind from 'turning down'.  They always produce at max.
#!CONSTRAINT 47
#forall ( t in Tech, ts in TimeStep, s in Seg | TechToTechClassMatrix(t, "PV") = 1 or TechToTechClassMatrix(t, "WIND") = 1) do
#	sum (fb in FuelBin, LD in Load |exists (dvRatedProd (t,LD,ts,s,fb)) and (LD = "1R" or LD = "1W" or LD = "1X" or LD = "1S"))
#		dvRatedProd (t,LD,ts,s,fb) =  dvSystemSize (t, s)
#end-do

    [t in Tech, ts in TimeStep, s in Seg; TechToTechClassMatrix[t, :PV] == 1 | TechToTechClassMatrix[t, :WIND] == 1],
	sum(dvRatedProd[t,LD,ts,s,fb] for fb in FuelBin,
        LD in [Symbol("1R"), Symbol("1W"), Symbol("1X"), Symbol("1S")]) ==  dvSystemSize[t, s]

###LEFT THESE OUT
#! System production
#Year1ElecProd := sum( t in Tech, s in Seg, fb in FuelBin, ts in TimeStep, LD in Load | (TechToTechClassMatrix (t, "PV") = 1 and (LD = "1R" or LD = "1W" or LD = "1X" or LD = "1S")))
#                 dvRatedProd (t,LD,ts,s,fb)*ProdFactor(t, LD, ts) *  TimeStepScaling
#AverageElecProd := sum( t in Tech, s in Seg, fb in FuelBin, ts in TimeStep, LD in Load | (TechToTechClassMatrix (t, "PV") = 1 and (LD = "1R" or LD = "1W" or LD = "1X" or LD = "1S")))
#                   dvRatedProd (t,LD,ts,s,fb)*ProdFactor(t, LD, ts) *  TimeStepScaling  * LevelizationFactor(t)
#Year1WindProd := sum( t in Tech, s in Seg, fb in FuelBin, ts in TimeStep, LD in Load | (TechToTechClassMatrix (t, "WIND") = 1 and (LD = "1R" or LD = "1W" or LD = "1X" or LD = "1S")))
#                 dvRatedProd (t,LD,ts,s,fb)*ProdFactor(t, LD, ts) *  TimeStepScaling
#AverageWindProd := sum( t in Tech, s in Seg, fb in FuelBin, ts in TimeStep, LD in Load | (TechToTechClassMatrix (t, "WIND") = 1 and (LD = "1R" or LD = "1W" or LD = "1X" or LD = "1S")))
#                   dvRatedProd (t,LD,ts,s,fb)*ProdFactor(t, LD, ts) *  TimeStepScaling  * LevelizationFactor(t)
#
#! Capital Costs
#TotalTechCapCosts := sum(t in Tech, s in Seg) (CapCostSlope(t, s) * dvSystemSize(t, s) + CapCostYInt(t,s) * binSegChosen(t,s))
#TotalStorageCapCosts := sum( b in BattLevel) dvStorageSizeKWH(b) * StorageCostPerKWH(b) + sum( b in BattLevel) dvStorageSizeKW(b) *  StorageCostPerKW(b)
#TotalOMCosts := sum(t in Tech, s in Seg) OMperUnitSize(t) * pwf_om * dvSystemSize(t, s)

    TotalTechCapCosts == sum(CapCostSlope[t, s] * dvSystemSize[t, s] + CapCostYInt[t,s] * binSegChosen[t,s]
                             for t in Tech, s in Seg)

    TotalStorageCapCosts == sum(dvStorageSizeKWH[b] * StorageCostPerKWH[b] + dvStorageSizeKW[b] *  StorageCostPerKW[b]
                                for b in BattLevel)

    TotalOMCosts == sum(OMperUnitSize[t] * pwf_om * dvSystemSize[t, s]
                        for t in Tech, s in Seg)
#TotalEnergyCharges := sum( t in Tech, fb in FuelBin) dvFuelCost(t,fb)
#DemandTOUCharges := sum( r in Ratchets, db in DemandBin) dvPeakDemandE( r, db) * DemandRates(r,db) * pwf_e
#DemandFlatCharges := sum( m in Month, dbm in DemandMonthsBin) dvPeakDemandEMonth( m, dbm) * DemandRatesMonth( m, dbm) * pwf_e
#TotalDemandCharges :=  DemandTOUCharges + DemandFlatCharges
#TotalFixedCharges := FixedMonthlyCharge * 12 * pwf_e

    TotalEnergyCharges == sum(dvFuelCost[t,fb]
                              for t in Tech, fb in FuelBin)

    #NEED UPDATED JSON
    #DemandTOUCharges == sum(dvPeakDemandE[r, db] * DemandRates[r,db] * pwf_e
    #                        for r in Ratchets, db in DemandBin)

    #DemandFlatCharges == sum(dvPeakDemandEMonth[m, dbm] * DemandRatesMonth[m, dbm] * pwf_e
    #                         for m in Month, dbm in DemandMonthsBin)

    TotalDemandCharges ==  DemandTOUCharges + DemandFlatCharges

    TotalFixedCharges == FixedMonthlyCharge * 12 * pwf_e

#! Utility and Taxable Costs
#
#! Incentives
#TotalEnergyExports := (sum (t in Tech,LD in Load,ts in TimeStep, s in Seg, fb in FuelBin | exists (dvRatedProd(t,LD,ts,s,fb)))
#					dvRatedProd (t,LD,ts,s,fb)* TimeStepScaling *ProdFactor(t, LD, ts) * LevelizationFactor(t) *   ExportRates(t,LD,ts)) * pwf_e
#TotalProductionIncentive := sum(t in Tech ) dvProdIncent (t)

    TotalEnergyExports == sum(dvRatedProd[t,LD,ts,s,fb] * TimeStepScaling * ProdFactor[t, LD, ts] * LevelizationFactor[t] * ExportRates[t,LD,ts] * pwf_e
                           for t in Tech, LD in Load, ts in TimeStep, s in Seg, fb in FuelBin)

    TotalProductionIncentive == sum(dvProdIncent[t] for t in Tech)

end)

println("Model built, moving on to optimizer...")

#! Tax benefit to system owner
#r_tax_fraction_owner := (1 - r_tax_owner)
#r_tax_fraction_offtaker := (1 - r_tax_offtaker)
#
#! Utility min charges
#if AnnualMinCharge > 12 * MonthlyMinCharge
#then TotalMinCharge := AnnualMinCharge * pwf_e
#else TotalMinCharge := 12 * MonthlyMinCharge * pwf_e
#end-if
#
#MinChargeAdder >= TotalMinCharge - (TotalEnergyCharges + TotalDemandCharges + TotalEnergyExports + TotalFixedCharges)
#MinChargeAdder >= 0
#
#! Note: 0.999*MinChargeAdder in Obj b/c when TotalMinCharge > (TotalEnergyCharges + TotalDemandCharges + TotalEnergyExports + TotalFixedCharges)
#!       it is arbitrary where the min charge ends up (eg. could be in TotalDemandCharges or MinChargeAdder).
#!       0.001*MinChargeAdder is added back into LCC when writing to results JSON.
#
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#!!!! OBJECTIVE FUNCTION VALUE
#
#! Lifecycle Costs (LCC)
#RECosts :=
#
#!Capital Costs
#TotalTechCapCosts + TotalStorageCapCosts +
#
#! Fixed O&M, tax deductible for owner
#TotalOMCosts * r_tax_fraction_owner +
#
#! Utility Bill, tax deductible for offtaker
#(TotalEnergyCharges + TotalDemandCharges + TotalEnergyExports + TotalFixedCharges + 0.999*MinChargeAdder) * r_tax_fraction_offtaker -
#
#! Subtract Incentives, which are taxable
#TotalProductionIncentive * r_tax_fraction_owner
#
#


# Prototype Objective Function
cost = set1param(Tech, [50, 100, 75])

@objective(REopt, Min,
            sum(cost[t] * dvRatedProd[t,LD,ts,s,fb] * ProdFactor[t,LD,ts] * LevelizationFactor[t]
                for t in Tech, LD in Load, ts in TimeStep, s in Seg, fb in FuelBin))

optimize!(REopt)


println(JuMP.termination_status(REopt))
println(JuMP.objective_value(REopt))

let x = 0
    for ts in 1100:1110
        println(JuMP.value(dvRatedProd[:UTIL1, Symbol("1R"), ts, 1, 1]))
    end
end


#!! END OBJECTIVE FUNCTION VALUE
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#
#!!!  Objectives   -- chose only 1, and comment the others
#!!!  1.  Minimize LCC
#!!!  2.  Maximize rated electric production project size
#!!!  3.  Maximize electric production project size
#
#if Obj = 1 then
#	! to minimize RE LCC, uncomment this line  (and comment others)
#	minimize (RECosts)
#elif Obj = 5 then
#	! Keep SOC high
#	minimize (RECosts - 1*dvMeanSOC)
#end-if
#
#!End timing
#EndTime:= gettime
#
#case getprobstat of
#  XPRS_OPT: status:="optimal"
#  XPRS_UNF: status:="unfinished"
#  XPRS_INF: status:="infeasible"
#  XPRS_UNB: status:="unbounded"
#  XPRS_OTH: status:="failed"
#  else status:="???"
#end-case
#writeln(status)
#exportprob(EP_MAX, "explout", RECosts)
#
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#!!!  Output Module
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#
#ExportedElecPV := sum(t in Tech, LD in Load, ts in TimeStep, s in Seg, fb in FuelBin | (TechToTechClassMatrix (t, "PV") = 1 and (LD = "1W" or LD = "1X" )))
#                dvRatedProd(t,LD,ts,s,fb) * ProdFactor(t, LD, ts) * LevelizationFactor(t) *  TimeStepScaling
#
#ExportedElecWIND := sum(t in Tech, LD in Load, ts in TimeStep, s in Seg, fb in FuelBin | (TechToTechClassMatrix (t, "WIND") = 1 and (LD = "1W" or LD = "1X" )))
#                dvRatedProd(t,LD,ts,s,fb) * ProdFactor(t, LD, ts) * LevelizationFactor(t) *  TimeStepScaling
#
#ExportBenefitYr1 := sum (t in Tech, LD in Load, ts in TimeStep, s in Seg, fb in FuelBin | exists (dvRatedProd(t,LD,ts,s,fb)))
#                    dvRatedProd (t,LD,ts,s,fb) * TimeStepScaling * ProdFactor(t, LD, ts) * ExportRates(t,LD,ts)
#
#Year1EnergyCost := TotalEnergyCharges / pwf_e
#Year1DemandCost := TotalDemandCharges / pwf_e
#Year1DemandTOUCost := DemandTOUCharges / pwf_e
#Year1DemandFlatCost := DemandFlatCharges / pwf_e
#Year1FixedCharges := TotalFixedCharges / pwf_e
#Year1MinCharges := MinChargeAdder / pwf_e
#Year1Bill := Year1EnergyCost + Year1DemandCost + Year1FixedCharges + Year1MinCharges
#
#
#Year1UtilityEnergy := sum(LD in Load, ts in TimeStep, s in Seg, fb in FuelBin)
#                      dvRatedProd("UTIL1", LD, ts, s, fb) * ProdFactor("UTIL1", LD, ts) * TimeStepScaling
#
#
#
#GeneratorFuelUsed := sum(t in Tech, fb in FuelBin | TechToTechClassMatrix (t, "GENERATOR") = 1) dvFuelUsed(t, fb)
#
#!************************** Writing to files ************************************
#
#
#!Time series dispatch output
#
#if sum(b in BattLevel) getsol(dvStorageSizeKWH(b)) > REoptTol then
#
#    fopen(OutputDir + "\\GridToBatt.csv", F_OUTPUT)
#        forall (ts in TimeStep) do
#           writeln (sum (s in Seg, fb in FuelBin)   getsol (dvRatedProd ("UTIL1", "1S", ts, s, fb)) * ProdFactor("UTIL1", "1S", ts) * LevelizationFactor("UTIL1"))
#        end-do
#    fclose(F_OUTPUT)
#
#    fopen(OutputDir + "\\ElecToStore.csv",F_OUTPUT)
#        forall (ts in TimeStep )     do
#           writeln (     getsol (dvElecToStor (ts)))
#        end-do
#    fclose(F_OUTPUT)
#
#    !Time series dispatch output
#    fopen(OutputDir + "\\ElecFromStore.csv",F_OUTPUT)
#        forall (ts in TimeStep )     do
#           writeln (    getsol (dvElecFromStor (ts)))
#        end-do
#    fclose(F_OUTPUT)
#
#    fopen(OutputDir + "\\StoredEnergy.csv",F_OUTPUT)
#        forall (ts in TimeStep )     do
#           writeln (   getsol (dvStoredEnergy (ts)))
#        end-do
#    fclose(F_OUTPUT)
#
#    forall (t in Tech | (TechToTechClassMatrix (t, "PV") = 1 and sum(s in Seg) getsol (dvSystemSize(t,s)) > REoptTol)) do
#
#        fopen(OutputDir + "\\PVtoBatt.csv", F_OUTPUT)
#            forall (ts in TimeStep) do
#               writeln (sum (s in Seg, fb in FuelBin)  getsol (dvRatedProd (t, "1S", ts, s, fb)) * ProdFactor(t, "1S", ts) * LevelizationFactor(t))
#            end-do
#        fclose(F_OUTPUT)
#
#    end-do
#
#    forall (t in Tech | (TechToTechClassMatrix (t, "WIND") = 1 and sum(s in Seg) getsol (dvSystemSize(t,s)) > 0)) do
#
#        fopen(OutputDir + "\\WINDtoBatt.csv", F_OUTPUT)
#            forall (ts in TimeStep) do
#               writeln (sum (s in Seg, fb in FuelBin)  getsol (dvRatedProd (t, "1S", ts, s, fb)) * ProdFactor(t, "1S", ts) * LevelizationFactor(t))
#            end-do
#        fclose(F_OUTPUT)
#
#    end-do
#
#end-if
#
#forall (t in Tech | (TechToTechClassMatrix (t, "PV") = 1 and sum(s in Seg) getsol (dvSystemSize(t,s)) > REoptTol)) do
#
#    fopen(OutputDir + "\\PVtoLoad.csv", F_OUTPUT)
#        forall (ts in TimeStep) do
#           writeln (sum (s in Seg, fb in FuelBin)   getsol (dvRatedProd (t, "1R", ts, s, fb)) * ProdFactor(t, "1R", ts) * LevelizationFactor(t))
#        end-do
#    fclose(F_OUTPUT)
#
#    fopen(OutputDir + "\\PVtoGrid.csv", F_OUTPUT)
#        forall (ts in TimeStep) do
#           writeln (sum (s in Seg, fb in FuelBin)   getsol (dvRatedProd (t, "1W", ts, s, fb)) * ProdFactor(t, "1W", ts) * LevelizationFactor(t) +
#                    sum (s in Seg, fb in FuelBin)   getsol (dvRatedProd (t, "1X", ts, s, fb)) * ProdFactor(t, "1X", ts) * LevelizationFactor(t))
#        end-do
#    fclose(F_OUTPUT)
#
#end-do
#
#forall (t in Tech | (TechToTechClassMatrix (t, "WIND") = 1 and sum(s in Seg) getsol (dvSystemSize(t,s)) > 0)) do
#
#    fopen(OutputDir + "\\WINDtoLoad.csv", F_OUTPUT)
#        forall (ts in TimeStep) do
#           writeln (sum (s in Seg, fb in FuelBin)   getsol (dvRatedProd (t, "1R", ts, s, fb)) * ProdFactor(t, "1R", ts) * LevelizationFactor(t))
#        end-do
#    fclose(F_OUTPUT)
#
#    fopen(OutputDir + "\\WINDtoGrid.csv", F_OUTPUT)
#        forall (ts in TimeStep) do
#           writeln (sum (s in Seg, fb in FuelBin)   getsol (dvRatedProd (t, "1W", ts, s, fb)) * ProdFactor(t, "1W", ts) * LevelizationFactor(t) +
#                    sum (s in Seg, fb in FuelBin)   getsol (dvRatedProd (t, "1X", ts, s, fb)) * ProdFactor(t, "1X", ts) * LevelizationFactor(t))
#        end-do
#    fclose(F_OUTPUT)
#
#end-do
#
#forall (t in Tech | (TechToTechClassMatrix (t, "GENERATOR") = 1 and sum(s in Seg) getsol (dvSystemSize(t,s)) > 0)) do
#
#    fopen(OutputDir + "\\GENERATORtoLoad.csv", F_OUTPUT)
#        forall (ts in TimeStep) do
#           writeln (sum (s in Seg, fb in FuelBin)   getsol (dvRatedProd (t, "1R", ts, s, fb)) * ProdFactor(t, "1R", ts) * LevelizationFactor(t))
#        end-do
#    fclose(F_OUTPUT)
#
#end-do
#
#fopen(OutputDir + "\\GridToLoad.csv", F_OUTPUT)
#    forall (ts in TimeStep) do
#       writeln (sum (s in Seg, fb in FuelBin)   getsol (dvRatedProd ("UTIL1", "1R", ts, s, fb)) * ProdFactor("UTIL1", "1R", ts) * LevelizationFactor("UTIL1"))
#    end-do
#fclose(F_OUTPUT)
#
#fopen(OutputDir + "\\Load.csv",F_OUTPUT)
#    forall (ts in TimeStep )     do
#       writeln (   getsol (LoadProfile("1R",ts)))
#    end-do
#fclose(F_OUTPUT)
#
#
#fopen(OutputDir + "\\DemandPeaks.csv",F_OUTPUT)
#    writeln ("Ratchet,DemandTier,PeakDemand")
#    forall  ( r in Ratchets, db in DemandBin)  do
#       writeln (r, ",", db, ",", getsol(dvPeakDemandE(r,db)),",")
#    end-do
#    writeln(",")
#    writeln("Month,Peak_Demand")
#    forall  ( m in Month, dbm in DemandMonthsBin)  do
#       writeln (m, ",", getsol(dvPeakDemandEMonth(m, dbm)),",")
#    end-do
#fclose(F_OUTPUT)
#
#
#! write outputs in JSON for post processing
#
#    Root:=addnode(out_json, 0, XML_ELT, "jsv")
#
#    Node:=addnode(out_json, Root, "status", status)
#    Node:=addnode(out_json, Root, "lcc", strfmt(getsol(RECosts) + 0.001*getsol(MinChargeAdder), 10, 0))
#
#    forall  (b in BattLevel)  do
#        Node:=addnode(out_json, Root, "batt_kwh", getsol (dvStorageSizeKWH(b)))
#    end-do
#
#    forall  (b in BattLevel)  do
#        Node:=addnode(out_json, Root, "batt_kw", getsol (dvStorageSizeKW(b)))
#    end-do
#
#    forall (t in Tech  | TechToTechClassMatrix(t, "PV") = 1 and sum(s in Seg) getsol (dvSystemSize(t,s)) > REoptTol)  do
#        Node:=addnode(out_json, Root, "pv_kw", sum(s in Seg) getsol (dvSystemSize(t,s)))
#    end-do
#
#    forall (t in Tech  | TechToTechClassMatrix(t, "WIND") = 1 and sum(s in Seg) getsol (dvSystemSize(t,s)) > 0)  do
#        Node:=addnode(out_json, Root, "wind_kw", sum(s in Seg) getsol (dvSystemSize(t,s)))
#    end-do
#
#    Node:=addnode(out_json, Root, "year_one_utility_kwh", strfmt(getsol (Year1UtilityEnergy) , 10, 4))
#    Node:=addnode(out_json, Root, "year_one_energy_cost", strfmt(getsol(Year1EnergyCost), 10, 2))
#    Node:=addnode(out_json, Root, "year_one_demand_cost", strfmt(getsol(Year1DemandCost), 10, 2))
#    Node:=addnode(out_json, Root, "year_one_demand_tou_cost", strfmt(getsol(Year1DemandTOUCost), 10, 2))
#    Node:=addnode(out_json, Root, "year_one_demand_flat_cost", strfmt(getsol(Year1DemandFlatCost), 10, 2))
#    Node:=addnode(out_json, Root, "year_one_export_benefit", strfmt(getsol(ExportBenefitYr1), 10, 0))
#    Node:=addnode(out_json, Root, "year_one_fixed_cost", strfmt(getsol(Year1FixedCharges), 10, 0))
#    Node:=addnode(out_json, Root, "year_one_min_charge_adder", strfmt(getsol(Year1MinCharges), 10, 2))
#    Node:=addnode(out_json, Root, "year_one_bill", strfmt(getsol(Year1Bill), 10, 2))
#    !Node:=addnode(out_json, Root, "year_one_payments_to_third_party_owner", strfmt(getsol(TotalDemandCharges) / pwf_e, 10, 0))
#    Node:=addnode(out_json, Root, "total_energy_cost", strfmt(getsol(TotalEnergyCharges) * r_tax_fraction_offtaker, 10, 2))
#    Node:=addnode(out_json, Root, "total_demand_cost", strfmt(getsol(TotalDemandCharges) * r_tax_fraction_offtaker, 10, 2))
#    Node:=addnode(out_json, Root, "total_fixed_cost", strfmt(getsol(TotalFixedCharges) * r_tax_fraction_offtaker, 10, 2))
#    Node:=addnode(out_json, Root, "total_min_charge_adder", strfmt(getsol(MinChargeAdder) * r_tax_fraction_offtaker, 10, 2))
#    Node:=addnode(out_json, Root, "total_payments_to_third_party_owner", 0)
#    Node:=addnode(out_json, Root, "net_capital_costs_plus_om", strfmt(getsol(TotalTechCapCosts) + getsol(TotalStorageCapCosts) + getsol(TotalOMCosts) * r_tax_fraction_owner, 10, 0))
#    Node:=addnode(out_json, Root, "net_capital_costs", strfmt(getsol(TotalTechCapCosts) + getsol(TotalStorageCapCosts), 10, 0))
#    Node:=addnode(out_json, Root, "average_yearly_pv_energy_produced", strfmt(getsol(AverageElecProd), 10, 0))
#    Node:=addnode(out_json, Root, "average_wind_energy_produced", strfmt(getsol(AverageWindProd), 10, 0))
#    Node:=addnode(out_json, Root, "year_one_energy_produced", strfmt(getsol(Year1ElecProd), 10, 0))
#    Node:=addnode(out_json, Root, "year_one_wind_energy_produced", strfmt(getsol(Year1WindProd), 10, 0))
#    Node:=addnode(out_json, Root, "average_annual_energy_exported", strfmt(getsol(ExportedElecPV), 10, 0))
#    Node:=addnode(out_json, Root, "average_annual_energy_exported_wind", strfmt(getsol(ExportedElecWIND), 10, 0))
#    Node:=addnode(out_json, Root, "fuel_used_gal", strfmt(getsol(GeneratorFuelUsed), 10, 2))
#
#jsonsave(out_json, OutputDir + "\\REopt_results.json")
#
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#!!!  End Output Module
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#
#
#end-model
