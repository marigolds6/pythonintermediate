import sys,urllib2, re, arcpy

###The geoprocessor class is ArcGIS ArcInfo dependent.
#Replacing with a different writing function if not using ArcGIS (see main()).
class geoprocessor:
    '''Extends an arcgis scripting object to add workspace write methods'''
    def __init__(self,workspace="D:/ArcGIS/ArcMap_Projects/OEM/PowerOutage.gdb"):
        '''Initialize the target workspace for the outage information'''
        try:
            arcpy.env.overwriteOutputoverwriteOutput = True
            arcpy.env.workspace = workspace
            self.outagetable = workspace + "/Ameren"
        except RuntimeError:
            print 'Initialization error. Check that an ArcInfo license if available.'
            raise
        except:
            print 'Failed to initialize geoprocessor.'
            raise

    def updaterows(self,dataset):
        '''Updates the existing outagetable based on current website data'''
        try:
            updaterows = arcpy.UpdateCursor(self.outagetable)
        except:
            print 'Failed to create update cursor.'
            raise
        try:
            updaterow = updaterows.next()
            while updaterow:
                if updaterow.OUTAGE > 0:
                    if updaterow.ZIPNUM in dataset:
                        if updaterow.OUTAGE != dataset[updaterow.ZIPNUM][1]:
                            updaterow.OUTAGE = dataset[updaterow.ZIPNUM][0]
                            if dataset[updaterow.ZIPNUM][1] > 0:
                                updaterow.SERVED = dataset[updaterow.ZIPNUM][1]
                            updaterows.updateRow(updaterow)
                        del dataset[updaterow.ZIPNUM]
                    else:
                        updaterow.OUTAGE = 0
                        updaterows.updateRow(updaterow)
                else:
                    if updaterow.ZIPNUM in dataset:
                        if updaterow.OUTAGE != dataset[updaterow.ZIPNUM][1]:
                            updaterow.OUTAGE = dataset[updaterow.ZIPNUM][0]
                            if dataset[updaterow.ZIPNUM][1] > 0:
                                updaterow.SERVED = dataset[updaterow.ZIPNUM][1]
                            updaterows.updateRow(updaterow)
                        del dataset[updaterow.ZIPNUM]
                updaterow = updaterows.next()
        finally:
            del updaterows
##End ArcGIS dependent section
    
class ameren:
    '''Initialization object. Holds URL for Ameren outagemap.'''
    def __init__(self,state = 'MO'):
        self.state=state
        self.url='https://www2.ameren.com/outagemap/default.aspx?state=' + state

            
def main():
    '''Pull outage information from Ameren website and feed to geodatabase workspace.
    Optional first argument to define a different ArcGIS workspace.'''
    #Main procedural program

    #Set debug to 1 to receive messages on program flow during execution
    debug = 1
    
    #Create ameren url holder
    amerenue = ameren()

    ###Start ArcGIS dependent section
    #Create extended geoprocessor object
    #Optional argument to define a different workspace
    if len(sys.argv) > 1:
        gp = geoprocessor(sys.argv[1])
    else:
        gp = geoprocessor()

    ###End ArcGIS dependent section

    #Build compiled REGEX objects to match to html from ameren website
    #If the script breaks, this may need updating
    web_start = re.compile('^\s*<table id="tblOutages"')
    web_end = re.compile('^\s*</table>')
    row_start = re.compile('^\s*<tr>\s*')
    row_end = re.compile('^\s*</tr>\s*')
    line_zip = re.compile(r'^\s*<td align="left" width="\d\d">(?P<zip>\d\d\d\d\d)')
    line_out = re.compile(r'^\s*<td style="font-weight:bold; width:50px; text-align:right">(?P<outage>\d*)</td>')
    line_ser = re.compile(r'^\s*<td align="Right" width="60">(?P<served>\d*)</td>')
    dataset = {}

    #Loop through webpage and create array of zip code returns
    try:
        outtable = urllib2.urlopen(amerenue.url)
    except urllib2.URLError, (strerror):
        print "URLError: Address failed or internet not accessible.\nReason: %s" % (strerror)
        print "URL Used: %s" % (amerenue.url)
        raise
    except:
        print "Unexpected error: ", sys.exc_info()[0]
        raise
        
    f = outtable.readline()
    intable = 0

    #Search for the start of the outage table
    while f and not intable:
        intable = web_start.match(f)
        f = outtable.readline()

    rowon = 0

    #Go to the end of the webpage
    while f and not web_end.match(f):
        rowstart = row_start.match(f)
        if rowstart:
            rowon = 1
            zipcode = ''
            outage = ''
            served = ''
        else:
            rowend = row_end.match(f)
            if rowend:
                rowon = 0

                #Debugging message
                if debug==1:
                    print "Zip code " + str(zipcode) + " has " + str(outage) + " of " + str(served) + " customers out."
                dataset[zipcode] = [outage,served]
            else:
                if rowon:
                    z = line_zip.match(f)
                    o = line_out.match(f)
                    s = line_ser.match(f)
                    if z:
                        try:
                            zipcode = float(z.group('zip'))
                        except:
                            zipcode = 0
                    elif o:
                        try:
                            outage = int(o.group('outage'))
                        except:
                            outage = 0
                    elif s:
                        try:
                            served = int(s.group('served'))
                        except:
                            served = 0
        f = outtable.readline()

    #Debugging messages
    if debug==1:
        if web_end.match(f):
            print 'end of web table reached'
        else:
            print 'end of webpage reached'

    ###Start ArcGIS Dependent section

    #Update the outage table using the dataset from the web site
    print dataset
    for entry in dataset:
        print "entry"
        print entry
        print "dataset"
        print dataset[entry]
    gp.updaterows(dataset)
    

    #To replace this section, you must write dataset to a different output
    #Currently this writes to a table in an ArcGIS workspace
    ###End ArcGIS Dependent section

#Executes main() when script is run
if __name__ == "__main__":
    main()
