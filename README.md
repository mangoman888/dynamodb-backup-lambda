# DynamoDB Backup

This Lambda function uses the on-demand backup capability introduced by AWS to backup (ALL) our DynamoDb tables in a given region.

It will create a IAM role with the relevant policies for the Lambda function.

It will delete backups older than a given period (DELETEAFTER env setting).

The function should be run via a schedule rule.

To schedule lambda functions use **CloudWatch** `>` **Rules** `>` **Create rule** `>` **Schedule** `>` **Add target** `>` **Function**

# Get started

The deployment process is done through `run.sh <env>`.

You need to ensure that a file named `setenv-staging` and|or `setenv-production` exists with the following variables:

- AWS_DEFAULT_REGION: AWS Region to connect to (eu-west-1 in this case)
- PROFILE: The AWS profile to use to deploy, ensure you set this to an appropriate profile for the environment
- DDBREGION: The DynamoDb region where we want to back up tables
- AWSACCOUNTID: The account id for the aws account you're deploying to
- DELETEAFTER: Integer (days), backups older than this will be deleted

There are example setenv files included for staging/production, you'll probably need to update **PROFILE** to a valid one running on your machine.

## Create the function

**For Staging env** execute `./run.sh staging`

**For Production env** execute `./run.sh production`
