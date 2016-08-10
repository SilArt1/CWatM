# -------------------------------------------------------------------------
# Name:       CWAT Model Dynamic
# Purpose:
#
# Author:      burekpe
#
# Created:     16/05/2016
# Copyright:   (c) burekpe 2016
# -------------------------------------------------------------------------


#from global_modules.add1 import *
from pcraster import*
from pcraster.framework import *



from management_modules.data_handling import *
from management_modules.improvepcraster import *
from management_modules.messages import *





class CWATModel_dyn(DynamicModel):

    # =========== DYNAMIC ====================================================

    def dynamic(self):
        """ Dynamic part of LISFLOOD
            calls the dynamic part of the hydrological modules
        """

        #self.CalendarDate = dateVar['dateStart'] + datetime.timedelta(days=dateVar['curr'])
        #self.CalendarDay = int(self.CalendarDate.strftime("%j"))
        timestep_dynamic()



        del timeMes[:]
        timemeasure("Start dynamic")


        if Flags['loud']:
            print "%-6i %10s" %(dateVar['currStart'],dateVar['currDatestr']),
        else:
            if not(Flags['check']):
                if (Flags['quiet']) and (not(Flags['veryquiet'])):
                    sys.stdout.write(".")
                if (not(Flags['quiet'])) and (not(Flags['veryquiet'])):
                    sys.stdout.write("\r%d" % dateVar['currStart'])
                    sys.stdout.flush()
        print

        # ************************************************************
        """ up to here it was fun, now the real stuff starts
        """
        self.readmeteo_module.dynamic()
        timemeasure("Read meteo") # 1. timing after read input maps

        #if Flags['check']: return  # if check than finish here

        """ Here it starts with hydrological modules:
        """
        # ***** RAIN AND SNOW *****************************************
        self.snowfrost_module.dynamic()
        timemeasure("Snow")  # 2. timing

        # ***** READ land use fraction maps***************************

        self.landcoverType_module.dynamic_fracIrrigation()
        self.capillarRise_module.dynamic()
        timemeasure("Soil 1.Part")  # 3. timing

        # *********  WATER Demand   *************************
        self.waterdemand_module.dynamic()
        timemeasure("Water demand")  # 4. timing

        # *********  Soil splitted in different land cover fractions *************
        self.landcoverType_module.dynamic()
        timemeasure("Soil main")  # 5. timing

        self.groundwater_module.dynamic()
        timemeasure("Groundwater")  # 6. timing

        self.routing_module.dynamic()
        timemeasure("Routing")  # 7. timing


        self.output_module.dynamic()
        timemeasure("Output")  # 7. timing



        for i in xrange(len(timeMes)):
            if self.currentTimeStep() == self.firstTimeStep():
                timeMesSum.append(timeMes[i] - timeMes[0])
            else: timeMesSum[i] += timeMes[i] - timeMes[0]



        self.sumsum_directRunoff +=  self.sum_directRunoff
        self.sumsum_Runoff += self.sum_directRunoff
        self.sumsum_Precipitation += self.Precipitation
        self.sumsum_gwRecharge += self.sum_gwRecharge
        runoff = self.baseflow + self.sum_landSurfaceRunoff
        self.sumsum_Runoff += runoff

        #print self.sum_directRunoff,  self.sum_interflowTotal, self.sum_landSurfaceRunoff, self.baseflow, runoff
        #print self.sumsum_Precipitation, self.sumsum_Runoff


          #report(decompress(self.var.sum_potTranspiration), "c:\work\output/trans.map")
          #r eport(decompress(self.var.directRunoff[3 ]), "c:\work\output\dir.map")
        #report(decompress(runoff), "c:\work\output\dirsum.map")
        #report(decompress(self.sumsum_Precipitation), "c:\work\output\prsum.map")
           #report(decompress(runoff), "c:\work\output/runoff.map")


        """
        self.landusechange_module.dynamic()

        # ***** READ LEAF AREA INDEX DATA ****************************
        self.leafarea_module.dynamic()

        # ***** READ variable water fraction ****************************
        self.evapowater_module.dynamic_init()

        # ***** READ INFLOW HYDROGRAPHS (OPTIONAL)****************
        self.inflow_module.dynamic()
        timemeasure("Read LAI") # 2. timing after LAI and inflow

        # ***** RAIN AND SNOW *****************************************
        self.snow_module.dynamic()
        timemeasure("Snow")  # 3. timing after LAI and inflow

        # ***** FROST INDEX IN SOIL **********************************
        self.frost_module.dynamic()
        timemeasure("Frost")  # 4. timing after frost index

        # ************************************************************
        # ****Looping soil 2 times - second time for forest fraction *
        # ************************************************************

        for soilLoop in xrange(3):
            self.soilloop_module.dynamic(soilLoop)
            # soil module is repeated 2 times:
            # 1. for remaining areas: no forest, no impervious, no water
            # 2. for forested areas
            timemeasure("Soil",loops = soilLoop + 1) # 5/6 timing after soil

        # -------------------------------------------------------------------
        # -------------------------------------------------------------------

        # ***** ACTUAL EVAPORATION FROM OPEN WATER AND SEALED SOIL ***
        self.opensealed_module.dynamic()

        # *********  WATER USE   *************************
        self.riceirrigation_module.dynamic()
        self.waterabstraction_module.dynamic()
        timemeasure("Water abstraction")

        # ***** Calculation per Pixel ********************************
        self.soil_module.dynamic_perpixel()
        timemeasure("Soil done")

        self.groundwater_module.dynamic()
        timemeasure("Groundwater")

        # ************************************************************
        # ***** STOP if no routing is required    ********************
        # ************************************************************
        if option['InitLisfloodwithoutSplit']:
            # InitLisfloodwithoutSplit
            # Very fast InitLisflood
            # it is only to compute Lzavin.map and skip completely the routing component
            self.output_module.dynamic() # only lzavin

            timemeasure("After fast init")
            for i in xrange(len(timeMes)):
                if self.currentTimeStep() == self.firstTimeStep():
                   timeMesSum.append(timeMes[i] - timeMes[0])
                else: timeMesSum[i] += timeMes[i] - timeMes[0]

            return


        # *********  EVAPORATION FROM OPEN WATER *************
        self.evapowater_module.dynamic()
        timemeasure("open water eva.")

        # ***** ROUTING SURFACE RUNOFF TO CHANNEL ********************
        self.surface_routing_module.dynamic()
        timemeasure("Surface routing")  # 7 timing after surface routing

        # ***** POLDER INIT **********************************
        self.polder_module.dynamic_init()

        # ***** INLETS INIT **********************************
        self.inflow_module.dynamic_init()
        timemeasure("Before routing")  # 8 timing before channel routing

        # ************************************************************
        # ***** LOOP ROUTING SUB TIME STEP   *************************
        # ************************************************************
        self.sumDisDay = globals.inZero.copy()
        # sums up discharge of the sub steps
        for NoRoutingExecuted in xrange(self.NoRoutSteps):
            self.routing_module.dynamic(NoRoutingExecuted)
            #   routing sub steps
        timemeasure("Routing",loops = NoRoutingExecuted + 1)  # 9 timing after routing

        # ----------------------------------------------------------------------

        if option['inflow']:
            self.QInM3Old = self.QInM3
            # to calculate the parts of inflow for every routing timestep
            # for the next timestep the old inflow is preserved
            self.sumIn += self.QInDt*self.NoRoutSteps

        # if option['simulatePolders']:
        # ChannelToPolderM3=ChannelToPolderM3Old;

        if option['InitLisflood'] or (not(option['SplitRouting'])):
            self.ChanM3 = self.ChanM3Kin.copy()
                # Total channel storage [cu m], equal to ChanM3Kin
        else:
            self.ChanM3 = self.ChanM3Kin + self.Chan2M3Kin - self.Chan2M3Start
            #self.ChanM3 = self.ChanM3Kin + self.Chan2M3Kin - self.Chan2M3Start
                # Total channel storage [cu m], equal to ChanM3Kin
                # sum of both lines
            #CrossSection2Area = pcraster.max(scalar(0.0), (self.Chan2M3Kin - self.Chan2M3Start) / self.ChanLength)

        self.sumDis += self.sumDisDay
        self.ChanQAvg = self.sumDisDay/self.NoRoutSteps
        TotalCrossSectionAreaKin = self.ChanM3 * self.InvChanLength
            # New cross section area (kinematic wave)
            # This is the value after the kinematic wave, so we use ChanM3Kin here
            # (NOT ChanQKin, which is average discharge over whole step, we need state at the end of all iterations!)

        timemeasure("After routing")  # 10 timing after channel routing

        # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        if not(option['dynamicWave']):
            # Dummy code if dynamic wave is not used, in which case the total cross-section
            # area equals TotalCrossSectionAreaKin, ChanM3 equals ChanM3Kin and
            # ChanQ equals ChanQKin
            self.TotalCrossSectionArea = TotalCrossSectionAreaKin
            # Total cross section area [cu m / s]
            WaterLevelDyn = -9999
            # Set water level dynamic wave to dummy value (needed

        if option['InitLisflood'] or option['repAverageDis']:
            self.CumQ += self.ChanQ
            self.avgdis = self.CumQ/self.TimeSinceStart
            # to calculate average discharge

        self.DischargeM3Out += np.where(self.AtLastPointC ,self.ChanQ * self.DtSec,0)
           # Cumulative outflow out of map

        # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        # Calculate water level
        self.waterlevel_module.dynamic()

        # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

        # ************************************************************
        # *******  Calculate CUMULATIVE MASS BALANCE ERROR  **********
        # ************************************************************
        self.waterbalance_module.dynamic()



        self.indicatorcalc_module.dynamic()



        # ************************************************************
        # ***** WRITING RESULTS: TIME SERIES AND MAPS ****************
        # ************************************************************

        self.output_module.dynamic()
        timemeasure("Water balance")



        ### Report states if EnKF is used and filter moment
        self.stateVar_module.dynamic()
        timemeasure("State report")

        timemeasure("All dynamic")


        for i in xrange(len(timeMes)):
            if self.currentTimeStep() == self.firstTimeStep():
                timeMesSum.append(timeMes[i] - timeMes[0])
            else: timeMesSum[i] += timeMes[i] - timeMes[0]



        self.indicatorcalc_module.dynamic_setzero()
           # setting monthly and yearly dindicator to zero at the end of the month (year)





        """
		