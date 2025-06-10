import json
import unittest
from unittest.mock import patch, MagicMock
import os
import sys
from botocore.exceptions import ClientError

# Add the Lambda function directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src/get_photo'))

# Import the Lambda function
import app

class TestGetPhotoFunction(unittest.TestCase):
    """Test cases for the get_photo Lambda function"""

    @patch('app.boto3.client')
    @patch('app.boto3.resource')
    def test_successful_get_photo(self, mock_resource, mock_client):
        """Test successful photo retrieval"""
        # Mock photo ID
        photo_id = "12345678-1234-5678-1234-567812345678"
        
        # Mock S3 client
        mock_s3 = MagicMock()
        mock_s3.generate_presigned_url.return_value = "https://presigned-url.example.com"
        mock_client.return_value = mock_s3
        
        # Mock DynamoDB response
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            'Item': {
                'photoId': photo_id,
                'fileName': 'test-photo.jpg',
                'uploadTimestamp': '2023-01-01T12:00:00',
                's3Key': f"{photo_id}/test-photo.jpg"
            }
        }
        mock_resource.return_value.Table.return_value = mock_table
        
        # Set environment variables
        os.environ['PHOTOS_TABLE'] = 'test-photos-table'
        os.environ['PHOTOS_BUCKET'] = 'test-photos-bucket'
        os.environ['URL_EXPIRATION'] = '3600'
        
        # Create test event
        event = {
            'pathParameters': {
                'photoId': photo_id
            }
        }
        
        # Call the Lambda function
        response = app.lambda_handler(event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 200)
        response_body = json.loads(response['body'])
        self.assertEqual(response_body['photoId'], photo_id)
        self.assertEqual(response_body['fileName'], 'test-photo.jpg')
        self.assertEqual(response_body['uploadTimestamp'], '2023-01-01T12:00:00')
        self.assertEqual(response_body['downloadUrl'], 'https://presigned-url.example.com')
        
        # Verify DynamoDB get_item was called correctly
        mock_table.get_item.assert_called_once_with(
            Key={
                'photoId': photo_id
            }
        )
        
        # Verify S3 generate_presigned_url was called correctly
        mock_s3.generate_presigned_url.assert_called_once_with(
            'get_object',
            Params={
                'Bucket': 'test-photos-bucket',
                'Key': f"{photo_id}/test-photo.jpg"
            },
            ExpiresIn=3600
        )

    @patch('app.boto3.client')
    @patch('app.boto3.resource')
    def test_missing_photo_id(self, mock_resource, mock_client):
        """Test handling of missing photo ID"""
        # Create test event with missing photoId
        event = {
            'pathParameters': {}
        }
        
        # Call the Lambda function
        response = app.lambda_handler(event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 400)
        response_body = json.loads(response['body'])
        self.assertEqual(response_body['error'], 'Missing photoId parameter')
        
        # Verify no AWS calls were made
        mock_resource.return_value.Table.return_value.get_item.assert_not_called()
        mock_client.return_value.generate_presigned_url.assert_not_called()

    @patch('app.boto3.client')
    @patch('app.boto3.resource')
    def test_photo_not_found(self, mock_resource, mock_client):
        """Test handling of photo not found"""
        # Mock photo ID
        photo_id = "nonexistent-photo-id"
        
        # Mock DynamoDB response for non-existent photo
        mock_table = MagicMock()
        mock_table.get_item.return_value = {}  # No Item in response
        mock_resource.return_value.Table.return_value = mock_table
        
        # Set environment variables
        os.environ['PHOTOS_TABLE'] = 'test-photos-table'
        
        # Create test event
        event = {
            'pathParameters': {
                'photoId': photo_id
            }
        }
        
        # Call the Lambda function
        response = app.lambda_handler(event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 404)
        response_body = json.loads(response['body'])
        self.assertEqual(response_body['error'], 'Photo not found')
        
        # Verify DynamoDB get_item was called
        mock_table.get_item.assert_called_once()
        
        # Verify S3 generate_presigned_url was not called
        mock_client.return_value.generate_presigned_url.assert_not_called()

    @patch('app.boto3.client')
    @patch('app.boto3.resource')
    def test_s3_client_error(self, mock_resource, mock_client):
        """Test handling of S3 client error"""
        # Mock photo ID
        photo_id = "12345678-1234-5678-1234-567812345678"
        
        # Mock S3 client to raise a ClientError
        mock_s3 = MagicMock()
        mock_s3.generate_presigned_url.side_effect = ClientError(
            {'Error': {'Code': 'NoSuchKey', 'Message': 'The specified key does not exist.'}},
            'GetObject'
        )
        mock_client.return_value = mock_s3
        
        # Mock DynamoDB response
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            'Item': {
                'photoId': photo_id,
                'fileName': 'test-photo.jpg',
                'uploadTimestamp': '2023-01-01T12:00:00',
                's3Key': f"{photo_id}/test-photo.jpg"
            }
        }
        mock_resource.return_value.Table.return_value = mock_table
        
        # Set environment variables
        os.environ['PHOTOS_TABLE'] = 'test-photos-table'
        os.environ['PHOTOS_BUCKET'] = 'test-photos-bucket'
        
        # Create test event
        event = {
            'pathParameters': {
                'photoId': photo_id
            }
        }
        
        # Call the Lambda function
        response = app.lambda_handler(event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 500)
        response_body = json.loads(response['body'])
        self.assertEqual(response_body['error'], 'Failed to generate download URL')

if __name__ == '__main__':
    unittest.main()