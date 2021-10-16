# finalProject.py
# Input: Keyword, Start and End Date.
# Author: Dylan Wingler 11/5/2020
# Unity ID: dnwingle

import sys, datetime, urllib2, urllib, arcpy, imageio, os

keyword = sys.argv[1]
startDate = sys.argv[2]
endDate = sys.argv[3]
direct = arcpy.env.workspace = 'C:/gispy/scratch/'

dumpCSV = 'C:/gispy/scratch/dumpCSV/'
arcpy.CheckOutExtension("Spatial")

# Thanks to
# https://docs.python.org/2/library/datetime.html
# for the following code
# Create date objects
from datetime import datetime
dateObj1 = datetime.strptime(startDate, '%m/%d/%Y')
dateObj2 = datetime.strptime(endDate, '%m/%d/%Y')
# Get difference between date objects
dateDifference = dateObj2 - dateObj1
# Get number of days as integer 
numDays = dateDifference.days

def mapPoints(result):
    # Thanks to
    # https://desktop.arcgis.com/en/arcmap/10.3/tools/data-management-toolbox/make-xy-event-layer.htm
    # for the following code:
    # Create a temporary point feature layer.
    inputTable = result
    xCoords = 'Longitude' 
    yCoords = 'Latitude'
    outName = result[-11:-4]
    outLayer = '{0}_layer'.format(outName) 
    arcpy.MakeXYEventLayer_management(inputTable, xCoords, yCoords, outLayer)
    
    # Thanks to
    # https://desktop.arcgis.com/en/arcmap/10.3/tools/conversion-toolbox/feature-class-to-feature-class.htmhtm
    # for the following code:
    # Convert temporary feature to permanent feature class.
    outputShp = '{0}.shp'.format(outName)
    arcpy.FeatureClassToFeatureClass_conversion(outLayer, direct, outputShp)
    message = '{0} created.'.format(outputShp)
    arcpy.AddMessage(message)

    # Thanks to
    # https://desktop.arcgis.com/en/arcmap/10.3/tools/spatial-analyst-toolbox/point-density.htm
    # for the following code:
    # Create a density map of the points
    arcpy.env.mask = 'C:\gispy\scratch\countries\countriesDissolve.shp'
    densityOut = arcpy.sa.PointDensity(outputShp, "NONE", 1)
    densityOut.save("C:\gispy\scratch\dumpTIF\density" + outName + ".tif")
    message = 'Day Training density analysis complete.'
    arcpy.AddMessage(message)
    print message
    exportMap(densityOut)

def exportMap(day):
    '''Add data to a map document and export the document'''
    # Add data to the map document
    inputFile = day
    myMap = 'C:\gispy\scratch\DayTemp.mxd'
    mxd = arcpy.mapping.MapDocument(myMap)
    dfs = arcpy.mapping.ListDataFrames(mxd)
    df = dfs[0]
    rast = '{0}'.format(inputFile)
    layerObj = arcpy.mapping.Layer(rast)
    arcpy.mapping.AddLayer(df, layerObj, "TOP")
    copyName = 'C:/gispy/scratch/' + rast[-18:-4] + '.mxd' 
    mxd.saveACopy(copyName)
    message = 'Map of {0} created'.format(day)

    # Export Map to PNG Image
    outName = rast[-18:-4]
    outputDir = 'C:/gispy/scratch/dumpMaps/{0}'.format(outName)
    arcpy.mapping.ExportToPNG(mxd, outputDir)
    message = 'Map of {0} created and exported.'.format(day)
    arcpy.AddMessage(message)
    print message

def makeGIF():
    ''' Create a GIF of the exported PNG files'''
    direct = 'C:/gispy/scratch/'
    outputDir = 'C:/gispy/scratch/'
    imageDir = "C:/gispy/scratch/dumpMaps/"
    images = []
    filenames = os.listdir(imageDir)
    filenames = [imageDir + f for f in filenames]
    for filename in filenames:
        images.append(imageio.imread(filename))
    movieName = "densityHotspotsFor{0}.gif".format(keyword)
    imageio.mimsave(outputDir + movieName, images, format='GIF', duration=0.6)
    message = ("{0} created!").format(movieName)
    arcpy.AddMessage(message)


def mySplit(aLine, delimChar):
    '''delimited by commas.'''
    fields = aLine.split(delimChar)
    
    processedFields = []
    fieldBuild = ''
    combineFlag = False
    
    for field in fields:
        # Any field starting and ending with double quotes shall just have the double
        # quotes removed.
        if len(field)>0 and field[0] == '"' and '"' in field[1:]:
            fieldBuild = field[1:len(field)-1]
        # A field that starts with a double quote but does not end with one causes us to
        # recognize that a false delimiter comma separates the following fields until one
        # is found that ends with a double quote. We strip the leading double quote and add
        # the comma that was falsely treated as a delimiter.    
        elif len(field)>0 and field[0] == '"':
            fieldBuild = field[1:] + ','
            combineFlag = True
            continue
        elif combineFlag:
            # If we are combining and a field ends with a double quote we combine it and
            # remove the trailing double quote.
            if len(field)>0 and field[len(field)-1] == '"':
                fieldBuild = fieldBuild + field[0:len(field)-1]
                combineFlag = False
            else:
                # When combining an ordinary field (no trailing double quote) we add
                # it with a trailing comma.
                fieldBuild = fieldBuild + field + ','
        else:
            fieldBuild = field
        
        if combineFlag == False:                
            processedFields.append(fieldBuild)    
    
    return processedFields 

# The GDELT url I use for this test. There are other GDELT URLs.
url = 'https://api.gdeltproject.org/api/v2/geo/geo'

# Save the number of results for each day in dayCounts
dayCounts = []

# Obtain data for each day up to the required number of days.
for dayNum in range(1, numDays+1):
    # Look for articles about the subject named in 'query'
    # Get data back in csv format
    # API docs I used are seen at:
    # https://blog.gdeltproject.org/gdelt-geo-2-0-api-debuts/
    values = {'query': keyword,
              'format': 'csv',
              'timespan': str(dayNum)+'d', 
              'sortby': 'date' }

    # Thanks to
    # https://docs.python.org/2/library/urllib.html
    # for explaining urllib.
    # The data in the values specified above needs to be put into special format so it can be
    # passed to the url successfully
    data = urllib.urlencode(values)
    
    # Set up the request including the encoded values that tell the url what you want
    req = urllib2.Request(url, data)
    
    # Issue the request and receive response data
    response = urllib2.urlopen(req)
    
    results = []
    for result in response:
        results.append(mySplit(result, ','))
    
    # Prepare a list that will contain response data
    resultList = []
    
    # Save each response line in a list. 
    for result in results:
        resultList.append(result)
        
    # resultList = resultList[1:]
    # Each day needs a header line with the column names, save this for
    # later use
    headerLine = resultList[0]
    
    # Save the count of results for each day in dayCounts
    dayCounts.append(len(resultList))
    
    if dayNum == numDays:
        # Print the list of result counts for each day
        message = 'Daily result counts: {0}'.format(dayCounts)
        print message
        arcpy.AddMessage(message)
        
        # dailyResults is a list of lists, where each sub-list is sliced from the
        # full resultList according to the count of results for each day.
        dailyResults = []
        dailyStart = 0
        for day in range(0,numDays):
            print '['+str(dailyStart)+':'+str(dayCounts[day])+']'
            
            if day == 0:
                header=[]
            else:
                header = [headerLine]    

            dailyResults.append(header+resultList[dailyStart:dayCounts[day]])
            if day > 0:
                dailyStart += dayCounts[day] - dayCounts[day-1]
            else:
                dailyStart = dayCounts[day]
            
        # Print sub-lists in CSV and call mapPoints
        dayIdx = 0
        filenameBase = 'out.csv'
        for result in dailyResults:
            resultString = ''
            for rowData in result:
                for columnIndex in range(2,4):
                    resultString = resultString + rowData[columnIndex] + ','
                resultString = resultString[:len(resultString)-1]+'\n'
            outfile = open(dumpCSV +'day'+str(dayIdx)+filenameBase, "w")
            outfile.writelines(resultString)
            dayIdx += 1
            outfile.close()
            mapPoints(dumpCSV +'day'+str(dayIdx-1)+filenameBase)
            
makeGIF()
message = 'Tool completed. GIF made.'
arcpy.AddMessage(message)
print message

      
        