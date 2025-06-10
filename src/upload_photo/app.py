import json
import boto3
import os
import uuid
from datetime import datetime

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Get environment variables
PHOTOS_TABLE = os.environ.get('PHOTOS_TABLE')
BUCKET_NAME = os.environ.get('PHOTOS_BUCKET')

def lambda_handler(event, context):
    """
    Lambda function to handle photo uploads.
    
    This function:
    1. Receives photo data from API Gateway
    2. Uploads the photo to S3
    3. Stores metadata in DynamoDB
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        API Gateway response with photo ID and status
    """
    try:
        # Parse the request body
        if 'body' not in event or not event['body']:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Missing request body'})
            }
            
        # If the body is a string (which it often is from API Gateway), parse it
        if isinstance(event['body'], str):
            body = json.loads(event['body'])
        else:
            body = event['body']
        
        # Check if required fields are present
        if 'photo' not in body or 'fileName' not in body:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Missing required fields: photo and fileName'})
            }
        
        # Extract data from request
        photo_data = body['photo']  # Base64 encoded photo data
        file_name = body['fileName']
        
        # Generate a unique photo ID
        photo_id = str(uuid.uuid4())
        
        # Generate S3 key
        s3_key = f"{photo_id}/{file_name}"
        
        # Upload photo to S3
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Body=photo_data,
            ContentType='image/jpeg'  # Assuming JPEG format, adjust as needed
        )
        
        # Get current timestamp
        timestamp = datetime.utcnow().isoformat()
        
        # Store metadata in DynamoDB
        table = dynamodb.Table(PHOTOS_TABLE)
        table.put_item(
            Item={
                'photoId': photo_id,
                'fileName': file_name,
                'uploadTimestamp': timestamp,
                's3Key': s3_key
            }
        )
        
        # Return success response
        return {
            'statusCode': 201,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'photoId': photo_id,
                'message': 'Photo uploaded successfully'
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal server error'})
        }