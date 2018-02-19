#!/usr/bin/python
# -*- coding: utf-8 -*-

# The following backs up ALL the DynamoDb tables for the given aws region
# This is a tweaked version of Amazon blog https://aws.amazon.com/blogs/database/a-serverless-solution-to-schedule-your-amazon-dynamodb-on-demand-backup/
# Deployment of this Lambda is via run.sh <env> which sets up the env vars, role, and policies.
from __future__ import print_function
from datetime import date, datetime, timedelta
import json
import boto3
from botocore.exceptions import ClientError
import os

ddbRegion = os.environ['ddb_region']
ddb = boto3.client('dynamodb', region_name=ddbRegion)

# The backup retention period is set by the DELETEAFTER variable in setenv-<environment> file
daysToLookBackup= int(os.environ['delete_after'])

def lambda_handler(event, context):
    try:

        # Get a list of all the tables in ddbRegion
        response = ddb.list_tables()

        # Create a backup for each
        for key in response['TableNames']:
            timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
            backup_name = key + "_" + timestamp
            print(key,' : Creating new Backup')
            ddb.create_backup(TableName=key,BackupName=backup_name)
            print(key,' : Backup completed')
            
            # Check for backups older than the 'delete_after' setting and delete if they are
            # TimeRangeLowerBound is the release of Amazon DynamoDB Backup and Restore - Nov 29, 2017
            upperDate=datetime.now()
            responseLatest = ddb.list_backups(TableName=key, TimeRangeLowerBound=datetime(2017, 11, 29), TimeRangeUpperBound=datetime(upperDate.year, upperDate.month, upperDate.day))
            latestBackupCount=len(responseLatest['BackupSummaries'])
            print(key,' : Backup Count before today =',latestBackupCount)

            deleteupperDate = datetime.now() - timedelta(days=daysToLookBackup)
            print(key,' : Backups older than ',deleteupperDate, 'will be deleted')
            delresponse = ddb.list_backups(TableName=key, TimeRangeLowerBound=datetime(2017, 11, 29), TimeRangeUpperBound=datetime(deleteupperDate.year, deleteupperDate.month, deleteupperDate.day))
            
            #check whether latest backup count is more than two before removing the old backup
            if latestBackupCount>=2:
                if 'LastEvaluatedBackupArn' in delresponse:
                    lastEvalBackupArn = delresponse['LastEvaluatedBackupArn']
                else:
                    lastEvalBackupArn = ''
                    
                while (lastEvalBackupArn != ''):
                    print('Deleting Old Backups...')
                    for record in delresponse['BackupSummaries']:
                        backupArn = record['BackupArn']
                        ddb.delete_backup(BackupArn=backupArn)
                        print(backupArn,' : has been deleted:')
                        
                    delresponse = ddb.list_backups(TableName=key, TimeRangeLowerBound=datetime(2017, 11, 29), TimeRangeUpperBound=datetime(deleteupperDate.year, deleteupperDate.month, deleteupperDate.day), ExclusiveStartBackupArn=lastEvalBackupArn)
                    if 'LastEvaluatedBackupArn' in delresponse:
                        lastEvalBackupArn = delresponse['LastEvaluatedBackupArn']
                    else:
                        lastEvalBackupArn = ''
                        print ('Old backups have been cleared.')
            else:
                 print (key,' : No backups have been cleared.')
                 
    except  ClientError as e:
        print(e)  

