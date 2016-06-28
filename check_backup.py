# script to check each ebs volume for a recent snapshot.
# logging to cloudwatch
# notification to sns


import boto3
import pytz
from datetime import datetime,timedelta

#alias = "ntoomey"
#accountfilter = [{'Name':'owner-alias','Values':[alias]}] 

try:
    ec2 = boto3.client('ec2')
except ec2exception:
    print "Error connecting to ec2"

print "Getting Volumes...."
ebs = ec2.describe_volumes()


def CheckSnapshotDate(snapshotdate,checkdate): 
    if snapshotdate:
        if snapshotdate > checkdate:
            return 1
        else:
            return 0
 
    else:
        return 0


def CheckSnapShot(snapshots):
    
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
        ret = datetime.now(pytz.utc) - timedelta(days=1)
    return ret


#print key,value returns because docs are a pain in the arse.
#for key,value in ebs.iteritems():
#   print key

print "Looking for recent backups...."
for volumes in ebs['Volumes']:
    volumeid = volumes['VolumeId']
    # get snapshots for volume
    snapshots = ec2.describe_snapshots(Filters=[{'Name':'volume-id','Values':[volumeid]}])
    snaps = snapshots['Snapshots']
    # returned structure has a list of all snapshots.  loop through to identify the newest.
    # then compare that newest to the current date.  
    print "Volume id: " + volumeid

    a = CheckSnapShot(snaps)    
    print a
