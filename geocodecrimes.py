# Requires ephem, pytz, pyodbc, and sdeconn
import datetime, pytz, ephem
import pyodbc
import arcpy
import sdeconn
def connectionstring():
    _driver = "SQL Server Native Client 10.0" #SQL Server 2008
    _computername="sql server location" 
    _databasename="database" 
    _username="username"
    _password='password'
    constr = r"DRIVER={%s};SERVER=%s;DATABASE=%s;UID=%s;PWD=%s" % (_driver, _computername, _databasename, _username, _password)
    return constr
def setenvironment(workspace = "C:\\arcgis\\TestBed.gdb"):
    arcpy.env.workspace = workspace
    arcpy.env.overwriteOutput = True
# ------------------------ START HERE -------------------------------------
def rowToTuple(row):
    #overwrite based on template strucure
    try:
        tz = getLocalTimeZone()
        oid = ''
        cn = row.CompNum
        j = row.Juris
        cc = row.CrimeCode
        cg = row.COGIS
        o = row.Offense
        do = tz.localize(row.DateOccurred)
        a = standardize(row.Address)
        ci = row.SZCITY
        z = row.SZZIP
        ds = tz.localize(row.DTSTATUSCHANGED)
        rid = row.IREPORTID
        ucr = row.iGroupDomainId
        ccdesc = row.szDesc
        jdesc = row.Jurisdiction
        odesc = row.OffenseDesc
        tod = timeOfDay(do)
        return (oid, cn, j, cc, cg, o, do, a, ci, z, ds, rid, ucr, ccdesc, jdesc, odesc, tod)
    except:
        print row
        raise
def standardize(address):
    try:
        if not address:
            return 'UNKNOWN'
        if (address[:2] == "0 "):
            address = address[2:]
        intersections = [' AT ', ' AND ', '@', '&', '/']
        for i in intersections:
            address = address.replace(i," / ")
        address = ' '.join(address.split()) #Reduce whitespace
        streets = {'LUCAS / HUNT':"LUCAS AND HUNT",
                   'LUCAS HUNT':"LUCAS AND HUNT",
                   'NORTH / SOUTH':"NORTH AND SOUTH",
                   'LEWIS / CLARK':"LEWIS AND CLARK",
                   'EDDIE / PARK':"EDDIE AND PARK",
                   'TOWN / COUNTRY':"TOWN AND COUNTRY",
                   'TOWN / FOUR':"TOWN AND FOUR",
                   'CURRIER / IVES':"CURRIER AND IVES",
                   'LAMP / LANTERN':"LAMP AND LANTERN",
                   'MCBRIDE / SON':"MCBRIDE AND SON",
                   'W / B':"W ",
                   'E / B':"E ",
                   'N / B':"N ",
                   'S / B':"S ",
                   'W FLORISSANT':"WEST FLORISSANT",
                   'N OUTER':"NORTH OUTER",
                   'S OUTER':"SOUTH OUTER"}
        for i,j in streets.iteritems():
            address = address.replace(i,j)
        return address
    except:
        print address
        raise
def makeTable(sql, sde, template):
    t = arcpy.CreateTable_management("in_memory", template, sde + "\\" + template)
    tc = arcpy.da.InsertCursor(t, "*")
    con = pyodbc.connect(connectionstring()) #Make odbc connection from connection string
    c = con.cursor() #Make odbc cursor
    c.execute(sql) #Run sql statement on odbc cursor
    #get the results and insert into table
    dbs = c.fetchall()
    for db in dbs:
        #insert into table
        tc.insertRow(rowToTuple(db))
    #Close up ado connection
    c.close()
    con.close()
    #close up insert cursor
    del c, con, tc
    return t
def geocode(table, path, locator, fieldmap):
    print("Geocoding table " + table + " with locator " + locator)
    match = arcpy.CreateScratchName("mt","","FeatureClass","in_memory")
    nomatch = arcpy.CreateScratchName("nm","","FeatureClass","in_memory")
    gresult = arcpy.CreateScratchName("gr","","FeatureClass","in_memory")
    locatorpath = path + "\\" + locator
    arcpy.geocoding.GeocodeAddresses(table, locatorpath, fieldmap, gresult)
    #set aside no match
    arcpy.Select_analysis(gresult, nomatch, """ "Status" IN ('U') """)
    #set aside match
    arcpy.Select_analysis(gresult, match, """ "Status" IN ('M', 'T') """)
    return (match, nomatch)
    
def validateIdentity(result, idtest, idtrue, idfalse):
    print("Running Identify")
    arcpy.Describe(result)
    iresult = arcpy.CreateScratchName("ir","","FeatureClass","in_memory")
    mismatch = arcpy.CreateScratchName("mm","","FeatureClass","in_memory")
    idmatch = arcpy.CreateScratchName("id","","FeatureClass","in_memory")
    arcpy.Identity_analysis(result, idtest, iresult, "NO_FID")
    arcpy.Describe(iresult)
    arcpy.Select_analysis(iresult, mismatch, idfalse)
    arcpy.Select_analysis(iresult, idmatch, idtrue)
    return(idmatch, mismatch)
def writeOutput(workspace, match, mismatch, nomatch):
    #arcpy.CopyFeatures_management(nomatch, "nomatch")
    #arcpy.CopyFeatures_management(mismatch, "mismatch")
    #arcpy.Append_management(nomatch, workspace + "\\nomatch", "NO_TEST")
    #arcpy.Append_management(mismatch, workspace + "\\mismatch", "NO_TEST")   
    #arcpy.Append_management(match, workspace + "\\CrimesWGS", "NO_TEST")
    arcpy.Append_management(nomatch, workspace + "\\unmatched", "NO_TEST")
    arcpy.Append_management(mismatch, workspace + "\\mismatched", "NO_TEST")   
    arcpy.Append_management(match, workspace + "\\Crimes", "NO_TEST")
def getLocalTimeZone():
    return pytz.timezone('US/Central')
def timeOfDay(dt = datetime.datetime.now(getLocalTimeZone())):
    if (dt.tzinfo == None):
        dt = getLocalTimeZone().localize(dt)
    dt_utc = pytz.utc.normalize(dt.astimezone(pytz.utc))
    sun = ephem.Sun()
    clayton = ephem.Observer()
    clayton.lon = "-90.392"
    clayton.lat = "38.643"
    clayton.date = dt_utc.strftime("%Y/%m/%d %H:%M")
    sun.compute(clayton)
    return (sun.alt > 0)

def sqltext(daysback = 0):
    #Done back to 2007-01-01
    date1 = (datetime.datetime.now() - datetime.timedelta(1) - datetime.timedelta(daysback)).strftime("'%Y-%m-%d 00:00:00.000'")
    #date1 = "'2007-01-01 00:00:00.000'"
    print date1
    date2 = (datetime.datetime.now() - datetime.timedelta(daysback)).strftime("'%Y-%m-%d 00:00:00.000'")
    #date2 = "'2008-01-01 00:00:00.000'"
    print date2
    sqldate = date1 + " AND " + date2
    sql1 ="SELECT DISTINCT N.*, OG.iGroupDomainId, OG.szDesc, J.SZDESC AS Jurisdiction, "
    sql2 ="OCC.SZDESC AS OffenseDesc FROM careAdmin.vwNotification N LEFT OUTER JOIN "
    sql3 ="CAREADMIN.tblOffenseGroupXRef XR on XR.iOffenseCrimeId = N.CrimeCode JOIN CAREADMIN.tblOffenseGroup "
    sql4 ="OG on OG.iId = XR.iOffenseGroupId and iGroupDomainId in (-32766, -32767, -32768) JOIN "
    sql5 ="CAREADMIN.tblJurisCode J on N.juris = J.iId AND J.bExportToMap != 0 JOIN CAREADMIN.TBLOFFENSECRIMECODE "
    sql6 ="OCC on N.CrimeCode = OCC.IID and OCC.BPUBLICSENSATIVE = 0 WHERE DTSTATUSCHANGED BETWEEN "
    sql7 =" AND SEXCRIME = 0 ORDER BY DateEntered, District"
    sql = sql1 + sql2 + sql3 + sql4 + sql5 + sql6 + sqldate + sql7
    return sql
    
if __name__ == "__main__":
    #Better modularization
    #Need Logging
    print datetime.datetime.now()
    print("Setting up environment")
    setenvironment()
    print("Connecting to CARE")
    
    policesde = sdeconn.connect("police_sde_prod") #Connection to police database 10.0
    newpolicesde = sdeconn.connect("police_sde_prod","sssgisdb10") #Connection to police database 10.1
    dwsde = sdeconn.connect("stlco_sde_dw","sssgisdb10") #Connection to datawarehouse 10.1

    tableworkspace = newpolicesde
    tablename = "CareTemplate"
    reports = makeTable(sqltext(), tableworkspace, tablename)

    print("Entering geocoding")
    locatorlocation1 = dwsde
    locater1 = "SingleAddress101"
    locatorlocation2 = "R:\\Locator.gdb"
    locator2 = "DualRangeLocal"
    fieldmap1 = "Street Address VISIBLE NONE;City <None> VISIBLE NONE;State <None> VISIBLE NONE;ZIP <None> VISIBLE NONE"
    fieldmap2 = "Street Address VISIBLE NONE;City <None> VISIBLE NONE;ZIP <None> VISIBLE NONE"
    print datetime.datetime.now()
    (match, nomatch) = geocode(reports.getOutput(0), locatorlocation1, locater1, fieldmap1)
    print datetime.datetime.now()
    (match2, nomatch2) = geocode(nomatch, locatorlocation2, locator2, fieldmap2)
    arcpy.Append_management(match2, match, "NO_TEST")
    print("Exiting geocoding")
    print datetime.datetime.now()
    print("Testing COGIS")
    cogispath = dwsde + "\\COGIS\\COGIS"
    (match, mismatch) = validateIdentity(match, cogispath, """ "COGIS" = "COGIS_1" """, """ "COGIS" <> "COGIS_1" """)
    print("Writing output")
    ws = policesde + "\\CrimeReports"
    writeOutput(ws, match, mismatch, nomatch2)
    ws = newpolicesde + "\\CrimeReports"
    #writeOutput(ws, match, mismatch, nomatch2)
    print datetime.datetime.now()
