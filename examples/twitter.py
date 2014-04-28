##
# Find what people are tweeting about for a specific query or keyword in the top 10 most 
# populated cities in the world and map it.
# The result layer should be a POINT feature class with the following fields:
# tweet_id, text, created_at, query, lat, lon, from_user, from_user_name, city
# Each time you run the script, make the resulting layer append new features.
##
import arcpy
import urllib2
import json
import random
 
query = "obama"
 
# Create or append a feature class
# Define the workspace. ALWAYS CHECK THIS MATCHES AN ACTUAL PATH IN YOUR HARD DRIVE
arcpy.env.workspace = "C:/ArcGIS"
 
# Geographic projection
prj_4326 = "Coordinate Systems/Geographic Coordinate Systems/World/WGS 1984.prj"
 
# Source cities
WorldCities = "world_cities/cities.shp"
 
# Target geodatabase name
WorldTweets = "WorldTweets.gdb"
TweetsByCity = "TweetsByCity" # Actual feature class
 
def setup_database():
    try:
        arcpy.CreateFileGDB_management(arcpy.env.workspace, WorldTweets)
    except:
        # WorldTweets.gdb did exist, pass
        pass
 
    # Create feature class
    try:
       arcpy.CreateFeatureclass_management(WorldTweets,TweetsByCity,"POINT","#","DISABLED","DISABLED",prj_4326)
    except:
        # TweetsByCity was already created
        pass
 
    # Add fields tweet_id, text, created_at, query, lat, lon, from_user, from_user_name
    FIELDS = [
        ['tweet_id', 'TEXT','NON_NULLABLE','REQUIRED'],
        ['text','TEXT','NON_NULLABLE','REQUIRED'],
        ['created_at','TEXT','NON_NULLABLE','REQUIRED'],
        ['query','TEXT','NON_NULLABLE','REQUIRED'],
        ['lat','FLOAT','NON_NULLABLE','REQUIRED'],
        ['lon','FLOAT','NON_NULLABLE','REQUIRED'],
        ['from_user','TEXT','NON_NULLABLE','REQUIRED'],
        ['from_user_name','TEXT','NON_NULLABLE','REQUIRED'],
        ['city','TEXT','NON_NULLABLE','NON_REQUIRED']
    ]
 
    for field_name, field_type, NULLABLE, REQUIRED in FIELDS:
        try:
            arcpy.AddField_management("WorldTweets.gdb/TweetsByCity",field_name, field_type, "#", "#", "#", "#", NULLABLE, REQUIRED,"#")
        except:
            pass
   
def parse_tweets(query, lat, lon, radius = "10mi"):
 
    # The Twitter API search service documentation 
    # https://dev.twitter.com/docs/api/1/get/search
    url = "http://search.twitter.com/search.json?q="+query+"&include_entities=true&geocode="+lat+","+ lon + "," + radius
 
    # Grab the data from Twitter in JSON format
    tweet_data_json = urllib2.urlopen(url).read()
 
    # Parse the JSON into a friendly Python dictionary using the json module
    tweet_data = json.loads(tweet_data_json)
 
    results = []
    for tweet in tweet_data['results']:
        results.append([
            tweet['id'],                # 0
            tweet['text'],              # 1    
            tweet['created_at'],        # 2
            query,                      # 3
            lat,                        # 4
            lon,                        # 5 
            tweet['from_user'],         # 6
            tweet['from_user_name']     # 7
        ])
 
    return results
 
 
def insert_tweets(randomize = True):
 
    cities = []
    if not randomize:
        # Select 10 of the most populated cities in the world
        i = 1
        for city in arcpy.SearchCursor(WorldCities, "POP_RANK = 1"):
            lat = city.Shape.centroid.Y
            lon = city.Shape.centroid.X
            city_name = city.CITY_NAME
            i += 1
            if i > 10:
                break
            else:
                cities.append([lat, lon, city_name])
    else:
        # Select 10 random cities. This is inefficient but works for this demo.
        for city in arcpy.SearchCursor(WorldCities, "POP_RANK < 3"):
            lat = city.Shape.centroid.Y
            lon = city.Shape.centroid.X
            city_name = city.CITY_NAME
            cities.append([lat, lon, city_name])
 
        # randomize the list
        random.shuffle(cities)
        cities = cities[0:10]
        
    print cities
    
    # Now that we have 10 cities, we query Twitter and insert tweets in the table
    for lat, lon, city_name in cities:
 
        # For documentation on insert operations read:
        # http://help.arcgis.com/en/arcgisdesktop/10.0/help/index.html#//002z0000001v000000
      
        # Create an table insertion cursor
        cur = arcpy.InsertCursor("WorldTweets.gdb/TweetsByCity")
 
        # Create an array and point object needed to create features
        
        lineArray = arcpy.Array()
        pnt = arcpy.Point()
  
        for tweet in parse_tweets(query, str(lat), str(lon)):
            
            # Create a new row feature with TweetsByCity's schema
            feat = cur.newRow()
            
            pnt.ID = long(tweet[0])
            pnt.Y = tweet[4]
            pnt.X = tweet[5]
            
            feat.setValue('tweet_id', str(tweet[0]))
            feat.setValue('text', tweet[1])
            feat.setValue('created_at', tweet[2])
            feat.setValue('query', tweet[3])
            feat.setValue('lat', tweet[4])
            feat.setValue('lon', tweet[5])
            feat.setValue('from_user', tweet[6])
            feat.setValue('from_user_name', tweet[7])
            feat.setValue('city', city_name)
            # Insert the feature
            lineArray.add(pnt)
            feat.shape = lineArray[0]
            cur.insertRow(feat)
            lineArray.removeAll()
            
        # flush
        del cur
        
if __name__ == "__main__":
    setup_database()
    insert_tweets(randomize = False)
