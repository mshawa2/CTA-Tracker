import urllib
import urllib.request
import xml.etree.ElementTree as ET
import datetime
import csv,sqlite3
import serial
import time
import io


"""
urllib                  - To send API Request
xml.etree.ElementTree   - Parse XML Response 
datetime                - Calculate ETA
csv,sqlite3             - Querying cta_L_stop Database
serial                  - Serial Read/Write
time                    - Loop the code to update
"""

""" DONE ONCE, NO LONGER NEEDED (Build Database from CTA_Lines csv)
To create Database
con = sqlite3.connect("ctadb.db")
cur = con.cursor()
cur.execute("CREATE TABLE t (STOP_ID, STOP_NAME);") # use your column names here

with open('cta_L_stops.csv','r') as fin: # `with` statement available in 2.5+
    # csv.DictReader uses first line in file for column headings by default
    dr = csv.DictReader(fin) # comma is default delimiter
    to_db = [(i['STOP_ID'], i['STOP_NAME']) for i in dr]

cur.executemany("INSERT INTO t (STOP_ID, STOP_NAME) VALUES (?, ?);", to_db)
con.commit()
con.close()
"""


# Set Default settings for CTA API
key = "08cdd6025b1645d89be20f6791cfb3fe"
stpid = str(30042) #stop
rt = "Blue" #stopName.split(',')[0]
maxr = "2"

inString = "Blue,Western (Forest Pk Branch),(O'Hare-bound),NONE"

# Default Settings for Buzzer
buzz = "NONE"


# Set Looping Variables 
counter = 0
prev = ""
freq = 5

ser2 = serial.Serial()
ser2.baudrate = 9600
ser2.port = 'COM3'
ser2.timeout = 5
ser2.open()
while True:
    # Update Displays with new query after freq seconds, reset counter to 0
    if(counter == 1):
        counter = 0
        
        
        print("From Bluetooth Arduino:\n" + inString)
        stopName = ""
        
        # Double any "'" to make SQL Query work
        if "'" in inString:
            temp = inString.split("'")
            stopName = temp[0]
            for i in range (1,len(temp)):
                stopName += "''" + temp[i]
                i+=1
        else:
            stopName = inString
        
        # To Query Database with
        sqlString = stopName.split(',')[1] + " " + stopName.split(',')[2]
        # Extract Buzzer Parameter
        rt = stopName.split(',')[0]
        buzz = stopName.split(',')[3]
        
        print("SQL-friendly query:\n" + sqlString)
        
        # Query CTA API for Stop Updates
        con = sqlite3.connect("ctadb.db")
        cur = con.cursor()
        cur.execute("SELECT STOP_ID FROM t WHERE STOP_NAME = '%s'" % sqlString);
        stop = cur.fetchone()[0]
        cur.execute("SELECT STOP_NAME FROM t");
        names = cur.fetchall()
        con.close()
        
        stpid = str(stop)
        
        # Send API Reqeust
        query = urllib.request.urlopen(
                "http://lapi.transitchicago.com/api/1.0/ttarrivals.aspx?key="
                + key + "&rt=" + rt + "&stpid=" + stpid  + "&max=" + maxr)
        
        print("Query:\nhttp://lapi.transitchicago.com/api/1.0/ttarrivals.aspx?key="
                + key + "&stpid=" + stpid + "&rt=" + rt + "&max=" + maxr + "\n")
        
        # Parse through XML Response
        tree = ET.parse(query)
        root = tree.getroot()
        
        # Get Current Time
        currHr,currMin,currSec = str(datetime.datetime.now().time()).split(":")
        currSec = currSec.split(".")[0]
        
        # Print Time in HH:MM
        print(str(currHr) + ":" + str(currMin))
        # Print Line, Stop
        print(root[3][2].text,root[3][5].text)
            
        print("================")
        # Printe out next 2 ETAs for DEBUG
        for i in range(3,3+int(maxr)):
            if(i < len(root)):
                arrHr,arrMin,arrSec = root[i][10].text.split(" ")[1].split(":")
                if(int(arrHr) != int(currHr)):
                    eta = int(arrMin) - int(currMin) + 60
                else:
                    eta = int(arrMin) - int(currMin)
                #print(root[i][3].text)  #stpDe
                if(root[i][11].text == "1"):
                    print(root[i][7].text,  "DUE")  #destNm
                    
                else:
                    print(root[i][7].text,  eta)  #destNm
        # Calculate first ETA
        arrHr,arrMin,arrSec = root[3][10].text.split(" ")[1].split(":")
        if(int(arrHr) != int(currHr)):
            eta = str(int(arrMin) - int(currMin) + 60)
        else:
            eta = str(int(arrMin) - int(currMin))
        if(root[3][11].text == "1"):
            eta1 = root[3][7].text + " " + "DUE"  #destNm
            
        else:
            eta1 = root[3][7].text + " " + eta  #destNm
            
        # Calculate Second ETA
        arrHr,arrMin,arrSec = root[4][10].text.split(" ")[1].split(":")
        if(int(arrHr) != int(currHr)):
            eta = str(int(arrMin) - int(currMin) + 60)
        else:
            eta = str(int(arrMin) - int(currMin))
        if(root[4][11].text == "1"):
            eta2 = root[4][7].text + " " +  "DUE"  #destNm
            
        else:
            eta2 = root[4][7].text + " " + eta  #destNm
            
        # Make line color more understandable for Display
        line = root[3][5].text
        if(line == "P"):
            line = "Purple"
        if(line == "Pnk"):
            line = "Pink"
        if(line == "O"):
            line = "Orange"
        if(line == "G"):
            line = "Green"
        if(line == "Y"):
            line = "Yellow"
        if(line == "BRN"):
            line = "Brown"
        outString = str(currHr) + ":" + str(currMin) + "," + line +  "," + root[3][2].text + "," + str(eta1) + "," + str(eta2) + "," + buzz
        
        # Send output to Arduino Displays
        print("To arduino:\n" + outString)
        #print(outString.encode())
        

        #sio = io.TextIOWrapper(io.BufferedRWPair(ser2, ser2))
        #sio.write(outString)
        ser2.write(outString.encode())
        #ser2.close()
        
    # End of Update Display
        
    ser = serial.Serial()
    ser.baudrate = 9600
    ser.port = 'COM6'
    ser.timeout = 5
    #ser = serial.Serial('/dev/tty.usbserial', 9600)
    
    print("Counter: " + str(counter))
    print("connected to: " + ser.portstr)
    
    ser.open()
    updateString = ser.readline().decode()
    ser.close()
    
    if(updateString == ""):
        print("Nothing to update")
    else:
        print("GOT NEW STRING: " + updateString)
        inString = updateString
    
    time.sleep(1)
    counter += 1


#Send as 4:35,BLUE,Rosemont,O'Hare 15,O'Hare 20
            
"""
Structure:
    <ctatt>
        0<tmst>
        1<errCd>
        2<errNm>
        3<eta>
            00<staId>
            01<stpId>
            02<staNm>   Station Name
            03<stpDe>   
            04<rn>
            05<rt>      Route (Blue, Red, etc.)
            06<destSt>
            07<destNm>
            08<trDr>    1 - Northbound, 5 - Southbound
            09<prdt>
            10<arrT>
            11<isApp>   is approaching (0,1)
            ...
        4...
        5...
        6...
        n<eta>
root [3][2] will have the staNm
root [3][3] will have the stpDe
root [3][7] will have the destNm
root [3][10] will have the arrT

"""