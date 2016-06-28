# script to check each ebs volume for a recent snapshot.
# logging to cloudwatch
# notification to sns


import boto3
import pytz
from datetime import datetime,timedelta
from time import time,gmtime
from calendar import timegm

LogGroup = "EBS-Snapshot"


def CheckSnapshotDate(snapshotdate,checkdate): 
    if snapshotdate:
        if snapshotdate > checkdate:
            return 1
        else:
            return 0
 
    else:
        return 0


def CheckSnapShot(snapshots):
    # How many days old the snapshot can't be.  This is more than 1 day old 
    backupdate = GetCheckDate(1)

    if snapshots:
        for snap in snapshots:
            if snap['State'] == "completed":
                if CheckSnapshotDate(snap['StartTime'],backupdate):
                    return 1
                else:
                    return 0
    else:
        return 0
    
def GetCheckDate(deltadays):
    if deltadays :
        ret = datetime.now(pytz.utc) - timedelta(days=deltadays)
    else:
        #default to 1 day.  no idea why this is here
        ret = datetime.now(pytz.utc) - timedelta(days=1)
    return ret

def CheckLogGroups(botoclient,loggroupname):
    res = botoclient.describe_log_groups(logGroupNamePrefix=loggroupname)
    if ( len(res['logGroups']) == 0):
        return 0
    else:
        return 1

def CreateLogGroup(botoclient,loggroupname):
    botoclient.create_log_group(logGroupName=loggroupname)

def CreateLogStream(botoclient,loggroupname):
    d = datetime.now(pytz.utc)
    streamName = d.strftime("%d/%m/%Y_%H%M%S")
    botoclient.create_log_stream(logGroupName=loggroupname,logStreamName=streamName)
    return streamName

def Epoch():
    return timegm(gmtime()) * 1000
    
    
def lambda_handler(event, context):
    # Initialize CloudWatch Logging
    cwlogs = boto3.client('logs')
    if (CheckLogGroups(cwlogs,LogGroup) == 0):
        CreateLogGroup(cwlogs,LogGroup) 

    LogStream = CreateLogStream(cwlogs,LogGroup)
    try:
        ec2 = boto3.client('ec2')
    except ec2exception:
        print "Error connecting to ec2"

    print "Getting Volumes...."
    ebs = ec2.describe_volumes()

    logEvents = list()

    print "Looking for recent backups...."
    for volumes in ebs['Volumes']:
        volumeid = volumes['VolumeId']
        # get snapshots for volume
        snapshots = ec2.describe_snapshots(Filters=[{'Name':'volume-id','Values':[volumeid]}])
        snaps = snapshots['Snapshots']
        print "Volume id: " + volumeid
        a = CheckSnapShot(snaps)    

        message = volumeid, a

        status = {'timestamp' : Epoch(),'message' : str(message)}
        print status
        logEvents.append(status) 
    
    ret = cwlogs.put_log_events(logGroupName=LogGroup,logStreamName=LogStream,logEvents=logEvents)

    print ret
