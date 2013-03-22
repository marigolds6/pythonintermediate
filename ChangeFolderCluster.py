# Change all the services in an ArcGIS Server 10.1 directory from one cluster to another

# For Http calls
import httplib, urllib, json

# For system tools
import sys

# For reading passwords without echoing
import getpass


def main(argv=None):

    # Ask for admin/publisher user name and password
    username = raw_input("Enter user name: ")
    password = getpass.getpass("Enter password: ")
    
    # Ask for server name
    serverName = raw_input("Enter Server name: ")
    serverPort = 6080

    folder = raw_input("Enter the folder name or ROOT for the root location: ")
    cluster = raw_input("Enter the cluster to move services to: ")
    
    # Get a token
    token = getToken(username, password, serverName, serverPort)
    if token == "":
        print "Could not generate a token with the username and password provided."    
        return

    # Construct URL to read folder
    if str.upper(folder) == "ROOT":
        folder = ""
    else:
        folder += "/"
    folderURL = "/arcgis/admin/services/" + folder
    
    
    # This request only needs the token and the response formatting parameter 
    params = urllib.urlencode({'token': token, 'f': 'json'})
    
    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
    
    # Connect to folder to get its current JSON definition    
    httpConn = httplib.HTTPConnection(serverName, serverPort)
    httpConn.request("POST", folderURL, params, headers)
    
    # Read response
    response = httpConn.getresponse()
    if (response.status != 200):
        httpConn.close()
        print "Could not read service information."
        return
    else:
        data = response.read()
        
        # Check that data returned is not an error object
        if not assertJsonSuccess(data):          
            print "Error when reading service information. " + str(data)
        else:
            print "Service information read successfully. Now changing properties..."

        # Deserialize response into Python object
        dataObj = json.loads(data)
        httpConn.close()

        #Loop through each service in the folder and move its cluster
        for item in dataObj['services']:
            fullSvcName = item['serviceName'] + "." + item['type']

            # Construct service URL, then gets its current JSON definition               
            serviceURL = "/arcgis/admin/services/" + folder + fullSvcName
            httpConn.request("POST", serviceURL, params, headers)
            
            # Read response
            serviceResponse = httpConn.getresponse()
            if (serviceResponse.status != 200):
                httpConn.close()
                print "Error while reading service." + str(fullSvcName) + "Please check the URL and try again."
                return
            else:
                serviceData = serviceResponse.read()
                
                # Check that data returned is not an error object
                if not assertJsonSuccess(serviceData):
                    print "Error when reading service information. " + str(serviceData)                    
                else:
                    print "Service " + fullSvcName + " read successfully. Now changing properties..."
            serviceObj = json.loads(serviceData)
            httpConn.close()

            # Edit desired properties of the service
            if (serviceObj["clusterName"] != cluster):
                serviceObj["clusterName"] = cluster

                # Serialize back into JSON
                updatedSvcJson = json.dumps(serviceObj)

                # Call the edit operation on the service. Pass in modified JSON.
                editSvcURL = "/arcgis/admin/services/" + folder + fullSvcName + "/edit"
                params = urllib.urlencode({'token': token, 'f': 'json', 'service': updatedSvcJson})
                httpConn.request("POST", editSvcURL, params, headers)
                
                # Read service edit response
                editResponse = httpConn.getresponse()
                if (editResponse.status != 200):
                    httpConn.close()
                    print "Error while executing edit."
                    return
                else:
                    editData = editResponse.read()
                    
                    # Check that data returned is not an error object
                    if not assertJsonSuccess(editData):
                        print "Error returned while editing service" + str(editData)        
                    else:
                        print "Service edited successfully."
                    httpConn.close()
            else:
                print "Service already in default cluster."

        return

# A function to generate a token given username, password and the adminURL.

def getToken(username, password, serverName, serverPort):
    # Token URL is typically http://server[:port]/arcgis/admin/generateToken
    tokenURL = "/arcgis/admin/generateToken"
    
    params = urllib.urlencode({'username': username, 'password': password, 'client': 'requestip', 'f': 'json'})
    
    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
    
    # Connect to URL and post parameters
    httpConn = httplib.HTTPConnection(serverName, serverPort)
    httpConn.request("POST", tokenURL, params, headers)
    
    # Read response
    response = httpConn.getresponse()
    if (response.status != 200):
        httpConn.close()
        print "Error while fetching tokens from admin URL. Please check the URL and try again."
        return
    else:
        data = response.read()
        httpConn.close()
        
        # Check that data returned is not an error object
        if not assertJsonSuccess(data):            
            return
        
        # Extract the token from it
        token = json.loads(data)        
        return token['token']            
        

# A function that checks that the input JSON object 
#  is not an error object.
    
def assertJsonSuccess(data):
    obj = json.loads(data)
    if 'status' in obj and obj['status'] == "error":
        print "Error: JSON object returns an error. " + str(obj)
        return False
    else:
        return True
    
        
# Script start 
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
