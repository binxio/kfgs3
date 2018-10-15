# Kinesis, Firehose, Athena

Try to do this workshop without looking in the Help section. If you cannot find the right help searching online, then some steps have a few tips to help you. If you're really stuck, check out the lambda.py or completed.yaml.

1. Read the CloudFormation **template.yaml**
2. Write down the resources to separate stickies (a resource is: FirehoseLogGroup, FirehoseLogStream, etc..)
3. Paste them on a whiteboard/flipover and connect them with a short description
4. Deploy the CloudFormation stack in your AWS account
5. Write some json data to your stream using `python ./generator.py <your-kinesis-stream>`
6. Check the result in S3 (`aws s3 ls`)
7. Crawl the data by triggering the crawler manually in the console (or `aws glue start-crawler --name <glue crawler id>`)
8. Use Athena in the console to query some data. Question: do you see *all* the data sent?
9. Now update CloudFormation/stack to automatically crawl the data every 15 minutes
10. Add the a Lambda Function to the stack which performs a "transformation" of the message before it's being stored to S3 (now we *should* see all the new data)
11. Bonus: if there is some time left, change the CloudFormation so everything is encrypted using KMS
12. Remove all files in the S3 bucket (`aws s3 rm s3://<bucket>/ --recursive`) and then delete your stack

# Help

## Step 4

New to CloudFormation? This is how you validate, deploy (create / update) and delete your stack.

```
aws cloudformation validate-template \
    --template-body file://template.yaml

aws cloudformation deploy \
    --capabilities CAPABILITY_IAM \
    --stack-name <stack_name> \
    --template template.yaml

aws cloudformation delete \
    --stack-name <stack_name>
```

## Step 6

Tired of typing? Use these functions to easily browse through your s3 content.

```python
def s3_cat(s3path):
    bucket, key = s3_split(s3path)
    client = boto3.client("s3")
    result = client.get_object(Bucket=bucket, Key=key)
    text = result["Body"].read().decode()
    print(text)

def s3_list(s3path):
    client = boto3.client("s3")
    bucket, key = s3_split(s3path)
    response = client.list_objects_v2(
        Bucket=bucket,
        Prefix=key
    )
    if 'Contents' in response:
        for item in response['Contents']:
            print("s3://" + bucket + "/" + item['Key'])
    else:
        print("No files found in s3://{}/{}".format(bucket, key))
```

## Step 9

Check out this documentation and find how to add a schedule.

https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-glue-crawler.html

## Step 10

We need a Lambda Function and some permission for the Lambda function to create and write logging.

```yaml
# Lambda for Transform
  FirehoseTransformLambda: 
    Type: AWS::Lambda::Function
    Properties: 
      Handler: "index.lambda_handler"
      Role: !GetAtt FirehoseTransformLambdaRole.Arn
      Code:
        ZipFile: <your lambda python code here>
      Runtime: "python3.6"
      Timeout: 60
  FirehoseTransformLambdaRole:
      Type: AWS::IAM::Role
      Properties:
        AssumeRolePolicyDocument:
          Version: 2012-10-17
          Statement:
            -
              Effect: Allow
              Principal:
                Service:
                  - lambda.amazonaws.com
              Action:
                - sts:AssumeRole
        Path: /
        Policies:
          - PolicyName: "basic-lambda"
            PolicyDocument:
              Version: '2012-10-17'
              Statement:
                - Effect: Allow
                  Action:
                    - logs:CreateLogGroup
                    - logs:CreateLogStream
                    - logs:PutLogEvents
                  Resource:
                    - "arn:aws:logs:*:*:*"
```

Here a Lambda Function to start with. Read the comments in the function to update before adding it to the CloudFormation template.

You can of course transform the data further by removing, or transforming json fields.

```python
import base64
import json

def lambda_handler(event, context):
    output = []

    for record in event['records']:
        payload = base64.b64decode(record['data'])

        # transform payload raw json string to a dict 
        # and back to make it proper json on a single line

        # add a new line (\n) to payload
        
        output_record = {
            'recordId': record['recordId'],
            'result': 'Ok',
            'data': base64.b64encode(payload.encode()).decode("utf-8")
        }
        output.append(output_record)

    return {'records': output}
```

To add the python script in CloudFormation, use this syntax example:

```
ZipFile: |
    import ...
```

Test your Lambda Function locally by adding this to your lambda.py and executing: `python lambda.py`

```python
if __name__ == '__main__':
    context = ''
    event = {
        'records': [
            {
                'recordId': '123',
                'data': base64.b64encode('{ "test": "test" }'.encode())
            }
        ]
    }
    lambda_handler(event,context)
```

It requires a different Firehose configuration to trigger the Lambda Function.

```yaml
      ExtendedS3DestinationConfiguration:
        ProcessingConfiguration:
          Enabled: True
          Processors:
            - Type: Lambda
              Parameters:
                - ParameterName: LambdaArn
                  ParameterValue: !GetAtt FirehoseTransformLambda.Arn
```

And the DeliveryRole needs an additional permission:

```yaml
- Effect: Allow
  Action:
    - lambda:InvokeFunction
    - lambda:GetFunctionConfiguration
  Resource:
    - !GetAtt FirehoseTransformLambda.Arn
```