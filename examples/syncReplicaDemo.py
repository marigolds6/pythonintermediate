# Import script modules
import arcpy
from sdeconn import connect
# Add logging
import logging, datetime


if __name__ == "__main__":

    arcpy.env.overwriteOutput = True

def main(arcpy):
    print "Running Main"
    # Local variables:
    stlco_sde_prod = connect("stlco_sde_prod", "sssgisdb1")    
    stlco_sde_dw = connect("stlco_sde_dw", "sssgisdb1")
    e911_sde_prod_10 = connect("e911_sde_prod", "sssgisdb1")
  #Replica Names
    prod_to_e911_10 = "SDEDBO.prod_to_e911"
    Prod_DataWarehouse_1 = "SDEDBO.Prod_DataWarehouse_1"
    Prod_DataWarehouse_2 = "SDEDBO.Prod_DataWarehouse_2"
    Prod_DataWarehouse_3 = "SDEDBO.Prod_DataWarehouse_3"

    sync_dir = "FROM_GEODATABASE1_TO_2"
    conflict_policy = "" #Not Applicable for One Way Replica
    conflict_detection = "" #Not Applicable for One Way Replica
    reconcile = "" #Not Applicable for One Way Replica

    try:
        print "Starting Sync"
        logging.debug(datetime.datetime.now().isoformat() + ": " + "Start Prod_DataWarehouse_1")
        # Process: Synchronize Jurisdictions, Trails, Zoning Petitions, and Zoning from prod to dw
        arcpy.SynchronizeChanges_management(stlco_sde_prod, Prod_DataWarehouse_1, stlco_sde_dw, sync_dir, conflict_policy, conflict_detection, reconcile)

        logging.debug(datetime.datetime.now().isoformat() + ": " + "Start Prod_DataWarehouse_2")
        # Process: Synchronize AddrPts and Street_Centerlines from prod to dw
        arcpy.SynchronizeChanges_management(stlco_sde_prod, Prod_DataWarehouse_2, stlco_sde_dw, sync_dir, conflict_policy, conflict_detection, reconcile)

        logging.debug(datetime.datetime.now().isoformat() + ": " + "Start prod_to_e911_10")
        # Process: Synchronize COGIS Dataset, ESN, and PSAP from prod to e911 v10
        arcpy.SynchronizeChanges_management(stlco_sde_prod, prod_to_e911_10, e911_sde_prod_10, sync_dir, conflict_policy, conflict_detection, reconcile)

        logging.debug(datetime.datetime.now().isoformat() + ": " + "Start Prod_DataWarehouse_3")
        # Process: Synchronize COGIS, ESN, and PSAP from prod to dw
        arcpy.SynchronizeChanges_management(stlco_sde_prod, Prod_DataWarehouse_3, stlco_sde_dw, sync_dir, conflict_policy, conflict_detection, reconcile)
        logging.debug(datetime.datetime.now().isoformat() + ": " + "End Synchronization")
    except Exception as e:
        print e
        logging.debug(datetime.datetime.now().isoformat() + ": " + "ERROR in Synchronization")
        logging.error(e)
        
    # Call Next Script
    #print "Calling PostSync"
    #PostSync.main(arcpy)

if __name__ == "__main__":
    logging.basicConfig(filename='Sync_ProdDW.log', level=logging.DEBUG)
    logging.debug(datetime.datetime.now().isoformat() + ": " + "Start Sync_ProdDW.py")
    main(arcpy)

