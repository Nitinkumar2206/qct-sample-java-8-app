# Serverless Photo Application

A serverless application for uploading, storing, and retrieving photos using AWS services. This application provides a simple way to upload photos, store them securely in S3, and retrieve them via pre-signed URLs.

## Architecture

The application uses the following AWS services:

- **API Gateway**: HTTP API with two endpoints:
  - `POST /photos`: Upload photo and metadata
  - `GET /photos/{photoId}`: Download photo via pre-signed URL

- **Lambda Functions**:
  - `UploadPhotoFunction`: Processes photo uploads, stores in S3, and saves metadata to DynamoDB
  - `GetPhotoFunction`: Retrieves photo metadata from DynamoDB and generates pre-signed URLs for S3 objects

- **S3**: Private bucket for secure photo storage

- **DynamoDB**: Photos table with the following schema:
  - `photoId` (Partition Key): Unique identifier for each photo
  - `fileName`: Original file name of the photo
  - `uploadTimestamp`: When the photo was uploaded
  - `s3Key`: S3 object key for the photo

## Architecture Diagram

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│             │     │             │     │             │     │             │
│   Client    │────▶│ API Gateway │────▶│   Lambda    │────▶│     S3      │
│             │     │             │     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                                              │
                                              │
                                              ▼
                                        ┌─────────────┐
                                        │             │
                                        │  DynamoDB   │
                                        │             │
                                        └─────────────┘
```

## Setup Instructions

### Prerequisites

- [AWS CLI](https://aws.amazon.com/cli/) installed and configured
- [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html) installed
- [Python 3.9](https://www.python.org/downloads/) or later

### Deployment

1. Clone this repository:
   ```
   git clone <repository-url>
   cd photo-app
   ```

2. Build the application:
   ```
   sam build
   ```

3. Deploy the application:
   ```
   sam deploy --guided
   ```
   Follow the prompts to deploy the application to your AWS account.

4. After deployment, note the API Gateway endpoint URL from the outputs:
   ```
   PhotosApiEndpoint: https://xxxxxxxxxx.execute-api.region.amazonaws.com/dev
   ```

5. Update the frontend configuration:
   - Open `frontend/index.html`
   - Update the `API_ENDPOINT` variable with your API Gateway endpoint URL

### Local Testing

#### Testing the Frontend

You can test the frontend locally by opening the `frontend/index.html` file in your web browser. Make sure to update the `API_ENDPOINT` variable with your deployed API Gateway endpoint.

#### Testing the Lambda Functions

You can test the Lambda functions locally using the SAM CLI:

```
# Test the upload photo function
sam local invoke UploadPhotoFunction --event events/upload-photo-event.json

# Test the get photo function
sam local invoke GetPhotoFunction --event events/get-photo-event.json
```

### Running Unit Tests

To run the unit tests:

```
cd tests
python -m unittest discover
```

## Security Considerations

- The S3 bucket is configured with private access to prevent unauthorized access to photos
- API Gateway is used to control access to the application
- Lambda functions follow the principle of least privilege with specific IAM permissions
- DynamoDB table is configured with point-in-time recovery for data protection

## Assumptions

- Photos are uploaded as base64-encoded strings in the request body
- Photo IDs are generated as UUIDs
- Pre-signed URLs for photo downloads expire after 1 hour (configurable)
- The application assumes JPEG image format (can be extended to support other formats)

## Future Enhancements

- Add user authentication and authorization
- Implement photo resizing and thumbnail generation
- Add support for photo albums and organization
- Implement image metadata extraction
- Add support for image processing (filters, cropping, etc.)

## License

This project is licensed under the MIT License - see the LICENSE file for details.