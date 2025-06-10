import json
import boto3
import os
from botocore.exceptions import ClientError

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Get environment variables
PHOTOS_TABLE = os.environ.get('PHOTOS_TABLE')
BUCKET_NAME = os.environ.get('PHOTOS_BUCKET')
URL_EXPIRATION = int(os.environ.get('URL_EXPIRATION', '3600'))  # Default 1 hour

def lambda_handler(event, context):
    """
    Lambda function to retrieve photo metadata and generate a pre-signed URL.
    
    This function:
    1. Extracts photoId from the path parameter
    2. Retrieves photo metadata from DynamoDB
    3. Generates a pre-signed URL for the S3 object
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        API Gateway response with photo metadata and pre-signed URL
    """
    try:
        # Extract photoId from path parameters
        if 'pathParameters' not in event or not event['pathParameters'] or 'photoId' not in event['pathParameters']:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Missing photoId parameter'})
            }
            
        photo_id = event['pathParameters']['photoId']
        
        # Get photo metadata from DynamoDB
        table = dynamodb.Table(PHOTOS_TABLE)
        response = table.get_item(
            Key={
                'photoId': photo_id
            }
        )
        
        # Check if photo exists
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Photo not found'})
            }
            
        photo_metadata = response['Item']
        
        # Generate pre-signed URL for S3 object
        try:
            presigned_url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': BUCKET_NAME,
                    'Key': photo_metadata['s3Key']
                },
                ExpiresIn=URL_EXPIRATION
            )
        except ClientError as e:
            print(f"Error generating pre-signed URL: {str(e)}")
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Failed to generate download URL'})
            }
            
        # Return photo metadata and pre-signed URL
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'photoId': photo_metadata['photoId'],
                'fileName': photo_metadata['fileName'],
                'uploadTimestamp': photo_metadata['uploadTimestamp'],
                'downloadUrl': presigned_url
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal server error'})
        }