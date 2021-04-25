import argparse
import socket
from threading import Thread
from time import sleep
import sys
import json

#These RPC calls below allow you to query the webbox
#Get Plant overview ie current/daily/total power from inverter
GetPlantOverview = '{"version":"1.0","proc":"GetPlantOverview","id":"1","format":"JSON"}'

#Gets list of SMA devices connected to RS-485 Bus
GetDevices = '{"version" : "1.0","proc" : "GetDevices","id" : "1","format" : "JSON"}'

#Get list of Channels from a device
#GetSensor has a replaceable string --DEVICE-- to be replaced with the device you wish to query
GetSensor = '{"version":"1.0","proc":"GetProcessData","id":"1","format":"JSON","params":{"devices":[{"key":"--DEVICE--","channels":null}]}}'

# These are examples of data returned from the various Sunny Sensors
#Sunny Sensor {Pannel Temp / Ambiemt Temp / Irradiation / Wind Speed}
#https://files.sma.de/downloads/Sensorbox-IEN100914.pdf
#'{"format":"JSON","result":{"devices":[{"key":"SENS0700:17403","channels":[{"unit":"W/m^2","meta":"ExlSolIrr","name":"ExlSolIrr","value":"0"},{"unit":"W/m^2","meta":"IntSolIrr","name":"IntSolIrr","value":"0"},{"unit":"h","meta":"SMA-h-On","name":"SMA-h-On","value":"72091.2252117420"},{"unit":"°C","meta":"TmpAmb C","name":"TmpAmb C","value":"19.23"},{"unit":"°C","meta":"TmpMdul C","name":"TmpMdul C","value":"18.13"},{"unit":"m/s","meta":"WindVel m/s","name":"WindVel m/s","value":"3.3"}]}]},"proc":"GetProcessData","version":"1.0","id":"3"}'

#School Meter Box {Counts S/0 signal from Energy Meter}
#https://files.sma.de/downloads/METERBOX-IEN110611.pdf
#I use an LDR placed over the flashing LED on my meter to count KW/H pulses
#'{"format":"JSON","result":{"devices":[{"key":"SMBAU008:154002012","channels":[{"unit":"h","meta":"m_OpTm","name":"m_OpTm","value":"43726"},{"unit":"W","meta":"m_Pac","name":"m_Pac","value":"0"},{"unit":"","meta":"m_Reset_Count","name":"m_Reset_Count","value":"21"},{"unit":"","meta":"m_S0 Count","name":"m_S0 Count","value":"70667899"},{"unit":"kWh","meta":"m_S0 kWh","name":"m_S0 kWh","value":"37212.520"}]}]},"proc":"GetProcessData","version":"1.0","id":"4"}'
#'{"format":"JSON","result":{"devices":[{"key":"SMBAU008:154002091","channels":[{"unit":"h","meta":"m_OpTm","name":"m_OpTm","value":"43727"},{"unit":"W","meta":"m_Pac","name":"m_Pac","value":"0"},{"unit":"","meta":"m_Reset_Count","name":"m_Reset_Count","value":"23"},{"unit":"","meta":"m_S0 Count","name":"m_S0 Count","value":"2326375"},{"unit":"kWh","meta":"m_S0 kWh","name":"m_S0 kWh","value":"5043.970"}]}]},"proc":"GetProcessData","version":"1.0","id":"5"}'

#SMA Inverter
#'{"format":"JSON","result":{"devices":[{"key":"WR6KA-05:2001124007","channels":[{"unit":"","meta":"Balancer","name":"Balancer","value":""},{"unit":"kWh","meta":"E-Total","name":"E-Total","value":""},{"unit":"Hz","meta":"Fac","name":"Fac","value":""},{"unit":"","meta":"Fehler","name":"Fehler","value":""},{"unit":"h","meta":"h-On","name":"h-On","value":""},{"unit":"h","meta":"h-Total","name":"h-Total","value":""},{"unit":"A","meta":"Iac-Ist","name":"Iac-Ist","value":""},{"unit":"A","meta":"Ipv","name":"Ipv","value":""},{"unit":"","meta":"Netz-Ein","name":"Netz-Ein","value":""},{"unit":"W","meta":"Pac","name":"Pac","value":""},{"unit":"kOhm","meta":"Riso","name":"Riso","value":""},{"unit":"","meta":"Seriennummer","name":"Seriennummer","value":""},{"unit":"","meta":"Status","name":"Status","value":""},{"unit":"V","meta":"Uac","name":"Uac","value":""},{"unit":"V","meta":"Upv-Ist","name":"Upv-Ist","value":""},{"unit":"V","meta":"Upv-Soll","name":"Upv-Soll","value":""},{"unit":"Ohm","meta":"Zac","name":"Zac","value":""}]}]},"proc":"GetProcessData","version":"1.0","id":"6"}'

#Sunny Webbox Plant Overview
#https://www.solar-electric.com/lib/wind-sun/SunnyWebbox-manual.pdf
#https://www.sunnyportal.com/Documents/SPortal-WB-CC-BA-US_en-27.pdf
#'{"format":"JSON","result":{"overview":[{"unit":"W","meta":"GriPwr","name":"GriPwr","value":"0"},{"unit":"kWh","meta":"GriEgyTdy","name":"GriEgyTdy","value":"12.384"},{"unit":"kWh","meta":"GriEgyTot","name":"GriEgyTot","value":"67812.215"},{"unit":"","meta":"OpStt","name":"OpStt","value":""},{"unit":"","meta":"Msg","name":"Msg","value":""}]},"proc":"GetPlantOverview","version":"1.0","id":"7"}'


#Generate a UDP transmit socket object
txSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

dataready = False
exit = False
result = ""

def WaitForData ():
    global dataready

    dataready = False

    while dataready == False:
        dummy = 0


def txData (IPAddr,portNum,txChar):
    global txSocket
    
    txSocket.sendto(txChar.encode('utf-16'),(IPAddr,portNum))


def QueryPlantOverview (IPAddr,portNum):
    global GetPlantOverview
    global result

    txData (IPAddr,portNum,GetPlantOverview)
    WaitForData()
    #print (result)

    Device = json.loads(result)
    DeviceChannels = len(Device['result']['overview'])
    print ("Device:\tOverview")

    for c in range ( 0 , DeviceChannels):
        Channel = Device['result']['overview'][c]['name']
        Uom = Device['result']['overview'][c]['unit']
        Value = Device['result']['overview'][c]['value']
        print ('\tChannel: ' + Channel + ' (' + Uom +') [' + Value + ']')

def QueryChannels (IPAddr,portNum,Device):
    global GetSensor
    global result

    Sensor = GetSensor.replace ('--DEVICE--',Device)
    txData (IPAddr,portNum,Sensor)
    WaitForData()
    #print (result)

    Device = json.loads(result)
    DeviceChannels = len(Device['result']['devices'][0]['channels'])
    #print (DeviceChannels)

    for c in range ( 0 , DeviceChannels):
        Channel = Device['result']['devices'][0]['channels'][c]['name']
        Uom = Device['result']['devices'][0]['channels'][c]['unit']
        Value = Device['result']['devices'][0]['channels'][c]['value']
        print ('\tChannel: ' + Channel + ' (' + Uom +') [' + Value + ']')
        #print()

def QueryDevices (IPAddr,portNum):
    global GetDevices
    global result

    txData (IPAddr,portNum,GetDevices)

    WaitForData()

    Devices = json.loads(result)
    DeviceNum = Devices['result']['totalDevicesReturned']

    for c in range ( 0 , DeviceNum):
        Device = Devices['result']['devices'][c]['key']
        print ("Device:\t" + Device)
        result = ""
        QueryChannels (IPAddr,portNum,Device)


def QueryWebBox(IPAddr,portNum):
    global GetPlantOverview
    global GetDevices
    global GetSensor

    QueryPlantOverview (IPAddr,portNum)
    QueryDevices (IPAddr,portNum)
    print ('Usage: please specify --device="Device" --channel="Channel"')


def FindPlantOverviewChannel (IPAddr,portNum,SearchChannel):
    global GetPlantOverview
    global result

    txData (IPAddr,portNum,GetPlantOverview)
    WaitForData()

    Device = json.loads(result)
    DeviceChannels = len(Device['result']['overview'])

    for c in range ( 0 , DeviceChannels):
        Channel = Device['result']['overview'][c]['name']
        Uom = Device['result']['overview'][c]['unit']
        Value = Device['result']['overview'][c]['value']

        if SearchChannel == Channel:
            print (Channel + ' (' + Uom +') [' + Value + ']')

def FindDeviceChannel (IPAddr,portNum,Device,SearchChannel):
    global GetSensor
    global result

    Sensor = GetSensor.replace ('--DEVICE--',Device)
    txData (IPAddr,portNum,Sensor)
    WaitForData()
    #print (result)

    Device = json.loads(result)
    DeviceChannels = len(Device['result']['devices'][0]['channels'])
    #print (DeviceChannels)

    for c in range ( 0 , DeviceChannels):
        Channel = Device['result']['devices'][0]['channels'][c]['name']
        Uom = Device['result']['devices'][0]['channels'][c]['unit']
        Value = Device['result']['devices'][0]['channels'][c]['value']

        if SearchChannel == Channel:
            print (Channel + ' (' + Uom +') [' + Value + ']')

def FindChannel (IPAddr,portNum,Device,SearchChannel):
    if Device.upper() == "OVERVIEW":
        FindPlantOverviewChannel (IPAddr,portNum,SearchChannel)    
    else:
        FindDeviceChannel (IPAddr,portNum,Device,SearchChannel)    
    

def rxThread(portNum):
    global exit
    global result
    global dataready
    
    #Generate a UDP receive socket
    rxSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
                             
    #Bind to any available address on port *portNum*
    rxSocket.bind(("",portNum))
    
    #Prevent the socket from blocking until it receives all the data it wants
    #Note: Instead of blocking, it will throw a socket.error exception if it
    #doesn't get any data
    rxSocket.setblocking(0)

    while not exit:
        try:
            #Attempt to receive up to 4096 bytes of data
            data, addr = rxSocket.recvfrom(4096) 
            #print (addr)
            #print ("RX: " + str(data.decode('utf-16')) )
            result = str(data.decode('utf-16'))
            dataready = True

        except socket.error:
            #If no data is received, you get here, but it's not an error
            #Ignore and continue
            pass

        sleep(.1)
    
    
def main(args):    
    global exit
    global dataready
    global result
    global txSocket
    
    parser = argparse.ArgumentParser(description="Test the SMA WebBox.")
    parser.add_argument("ip", type=str, help="IP address of the WebBox")
    parser.add_argument("port", default=34268,type=int, help="UDP Port Number of the WebBox")
    parser.add_argument("--device", help="Device Id")
    parser.add_argument("--channel", help="Device Channel")

    args = parser.parse_args()

    IPAddr = args.ip
    portNum = args.port

    Device = args.device
    Channel = args.channel



    udpRxThreadHandle = Thread(target=rxThread,args=(portNum,))    
    udpRxThreadHandle.start()
        
    sleep(.1)

    #Generate a transmit socket object
    txSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    #Do not block when looking for received data (see above note)
    txSocket.setblocking(0) 

    if Device == None or Channel == None :
        QueryWebBox (IPAddr,portNum)
    else:
        FindChannel (IPAddr,portNum,Device,Channel)

    #set exit flag so that our receive thread can exit
    exit = True
   
if __name__=="__main__":
    main(sys.argv[1:0]) 
