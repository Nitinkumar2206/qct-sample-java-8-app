import json
import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import uuid
from datetime import datetime

# Add the Lambda function directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src/upload_photo'))

# Import the Lambda function
import app

class TestUploadPhotoFunction(unittest.TestCase):
    """Test cases for the upload_photo Lambda function"""

    @patch('app.boto3.client')
    @patch('app.boto3.resource')
    @patch('app.uuid.uuid4')
    @patch('app.datetime')
    def test_successful_upload(self, mock_datetime, mock_uuid, mock_resource, mock_client):
        """Test successful photo upload"""
        # Mock UUID
        mock_uuid_value = "12345678-1234-5678-1234-567812345678"
        mock_uuid.return_value = mock_uuid_value
        
        # Mock datetime
        mock_timestamp = "2023-01-01T12:00:00"
        mock_datetime.utcnow.return_value.isoformat.return_value = mock_timestamp
        
        # Mock S3 client
        mock_s3 = MagicMock()
        mock_client.return_value = mock_s3
        
        # Mock DynamoDB table
        mock_table = MagicMock()
        mock_resource.return_value.Table.return_value = mock_table
        
        # Set environment variables
        os.environ['PHOTOS_TABLE'] = 'test-photos-table'
        os.environ['PHOTOS_BUCKET'] = 'test-photos-bucket'
        
        # Create test event
        event = {
            'body': json.dumps({
                'photo': 'base64encodedphotodata',
                'fileName': 'test-photo.jpg'
            })
        }
        
        # Call the Lambda function
        response = app.lambda_handler(event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 201)
        response_body = json.loads(response['body'])
        self.assertEqual(response_body['photoId'], mock_uuid_value)
        self.assertEqual(response_body['message'], 'Photo uploaded successfully')
        
        # Verify S3 upload was called correctly
        mock_s3.put_object.assert_called_once_with(
            Bucket='test-photos-bucket',
            Key=f"{mock_uuid_value}/test-photo.jpg",
            Body='base64encodedphotodata',
            ContentType='image/jpeg'
        )
        
        # Verify DynamoDB put_item was called correctly
        mock_table.put_item.assert_called_once_with(
            Item={
                'photoId': mock_uuid_value,
                'fileName': 'test-photo.jpg',
                'uploadTimestamp': mock_timestamp,
                's3Key': f"{mock_uuid_value}/test-photo.jpg"
            }
        )

    @patch('app.boto3.client')
    @patch('app.boto3.resource')
    def test_missing_body(self, mock_resource, mock_client):
        """Test handling of missing request body"""
        # Create test event with missing body
        event = {}
        
        # Call the Lambda function
        response = app.lambda_handler(event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 400)
        response_body = json.loads(response['body'])
        self.assertEqual(response_body['error'], 'Missing request body')
        
        # Verify no AWS calls were made
        mock_client.return_value.put_object.assert_not_called()
        mock_resource.return_value.Table.return_value.put_item.assert_not_called()

    @patch('app.boto3.client')
    @patch('app.boto3.resource')
    def test_missing_required_fields(self, mock_resource, mock_client):
        """Test handling of missing required fields"""
        # Create test event with missing fields
        event = {
            'body': json.dumps({
                'photo': 'base64encodedphotodata'
                # Missing fileName
            })
        }
        
        # Call the Lambda function
        response = app.lambda_handler(event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 400)
        response_body = json.loads(response['body'])
        self.assertEqual(response_body['error'], 'Missing required fields: photo and fileName')
        
        # Verify no AWS calls were made
        mock_client.return_value.put_object.assert_not_called()
        mock_resource.return_value.Table.return_value.put_item.assert_not_called()

    @patch('app.boto3.client')
    @patch('app.boto3.resource')
    def test_exception_handling(self, mock_resource, mock_client):
        """Test handling of exceptions"""
        # Mock S3 client to raise an exception
        mock_s3 = MagicMock()
        mock_s3.put_object.side_effect = Exception("Test exception")
        mock_client.return_value = mock_s3
        
        # Set environment variables
        os.environ['PHOTOS_TABLE'] = 'test-photos-table'
        os.environ['PHOTOS_BUCKET'] = 'test-photos-bucket'
        
        # Create test event
        event = {
            'body': json.dumps({
                'photo': 'base64encodedphotodata',
                'fileName': 'test-photo.jpg'
            })
        }
        
        # Call the Lambda function
        response = app.lambda_handler(event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 500)
        response_body = json.loads(response['body'])
        self.assertEqual(response_body['error'], 'Internal server error')

if __name__ == '__main__':
    unittest.main()