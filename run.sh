#!/usr/bin/env bash

#
# The following creates a lambda function that should be run via a Cloudwatch schedule rule.
# It creates a IAM role (if it doesn't exist) and policies required to run.
# The script requires a setenv-staging or setenv-production file to exist with the correct variables for each env.
# It sets DDBREGION and DELETEAFTER as Environment variables for the Lambda function.
#

set -e

if [ $# -ne 1 ]; then
  echo "Usage: ./run.sh <staging|production>"
  exit 1;
fi

# Get Input Variables
source ./setenv-$1

# Check es-cleanup-lambda role exists
if aws iam get-role --role-name dynamodb-backup-lambda --profile ${PROFILE} 2>/dev/null; then
  echo -e "\ndynamodb-backup-lambda role already exists\n"
else
  echo -e "\nCreate the IAM Role\n"
  # Create the IAM Role
  aws iam create-role --role-name dynamodb-backup-lambda \
      --profile ${PROFILE} \
      --assume-role-policy-document file://json_file/trust_policy.json
  # Introduce sleep to give time for the new role to become available to be assumed by the lambda function below!
  sleep 10
fi

# Add or update inline policy for the IAM role
echo -e "\nAdd or update inline policy for the IAM role\n"
aws iam put-role-policy --role-name dynamodb-backup-lambda \
    --profile ${PROFILE} \
    --policy-name DDBBackupLambdaRolePolicy \
    --policy-document file://json_file/DDBBackupLambdaRolePolicy.json
sleep 5

# Create your Lambda package
echo -e "\nPackaging Lambda\n"
zip dynamodb-backup-lambda.zip dynamodb-backup.py

# Check if function exists and update if it does
if aws lambda get-function --function-name dynamodb-backup-lambda --profile ${PROFILE} 2>/dev/null; then
  echo -e "\ndynamodb-backup-lambda function already exists\n"
  aws lambda update-function-code \
      --profile ${PROFILE} \
      --function-name dynamodb-backup-lambda \
      --zip-file fileb://dynamodb-backup-lambda.zip
else
  echo -e "\nLambda deployment\n"
  # Lambda deployment
  aws lambda create-function \
      --profile ${PROFILE} \
      --function-name dynamodb-backup-lambda \
      --environment "Variables={ddb_region=$DDBREGION,delete_after=$DELETEAFTER}" \
      --zip-file fileb://dynamodb-backup-lambda.zip \
      --description "DynamoDb Backup All Tables in Region" \
      --role arn:aws:iam::$AWSACCOUNTID:role/dynamodb-backup-lambda \
      --handler dynamodb-backup.lambda_handler \
      --runtime python2.7 \
      --timeout 180
fi

