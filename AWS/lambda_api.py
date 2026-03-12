import boto3
import json
import csv
import io

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    
    bucket = 'food-equity-dashboard'
    key = 'final-output/adjusted_final_data.csv'
    
    obj = s3.get_object(Bucket=bucket, Key=key)
    content = obj['Body'].read().decode('utf-8')
    
    reader = csv.DictReader(io.StringIO(content))
    data = [row for row in reader]
    
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Content-Type': 'application/json'
        },
        'body': json.dumps(data)
    }