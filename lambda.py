# Function 1: Serialize Image Data  -------------------------------------------------------
import json
import boto3
import base64

s3 = boto3.client('s3')

def lambda_handler(event, context):
    """A function to serialize target data from S3"""

    # Get the s3 address from the Step Function event input
    key = event['s3_key']
    bucket = event['s3_bucket']

    # Download the data from s3 to /tmp/image.png
    s3.download_file(bucket, key, '/tmp/image.png')

    # Read the data from a file
    with open("/tmp/image.png", "rb") as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')

    # Pass the data back to the Step Function
    return {
        'statusCode': 200,
        'body': {
            "image_data": image_data,
            "s3_bucket": bucket,
            "s3_key": key,
            "inferences": []
        }
    }

# Function 2: Classify Image  -------------------------------------------------------
import json
import base64
import boto3

ENDPOINT = 'image-classification-2023-08-08-87-33-76-973'

def lambda_handler(event, context):
    """A function to classify an image using a SageMaker endpoint"""

    # Decode the image data
    image = base64.b64decode(event['image_data'])

    runtime = boto3.client('runtime.sagemaker')

    inferences = runtime.invoke_endpoint(
        EndpointName=ENDPOINT,
        ContentType='image/png',
        Body=image
    )

    # We return the data back to the Step Function
    event["inferences"] = inferences['Body'].read().decode('utf-8')
    return {
        'statusCode': 200,
        'body': json.dumps(event)
    }

# Function 3: Filter Inferences -------------------------------------------------------
import json

THRESHOLD = 0.85

def lambda_handler(event, context):
    """A function to filter inferences based on a confidence threshold"""

    # Grab the inferences from the event
    inferences = json.loads(event['inferences']) if isinstance(event['inferences'], str) else event['inferences']

    # Check if any values in our inferences are above the THRESHOLD
    meets_threshold = max(inferences) > THRESHOLD

    # If our threshold is met, pass our data back out of the Step Function,
    # else, end the Step Function with an error
    if meets_threshold:
        pass
    else:
        raise Exception("THRESHOLD_CONFIDENCE_NOT_MET")

    return {
        'statusCode': 200,
        'body': json.dumps(event)
    }
