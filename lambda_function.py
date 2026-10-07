import boto3
import json
import hashlib
import os

def lambda_handler(event, context):

        # Initialize the bedrock-runtime boto3 client in us-east-1
        bedrock_runtime = boto3.client("bedrock-runtime", region_name="us-east-1")

        # Get the BUCKET_NAME and TABLE_NAME from Environment variables.
        BUCKET_NAME = os.environ['BUCKET_NAME']
        TABLE_NAME = os.environ['TABLE_NAME']


        # Set MODEL-ID = amazon.nova-pro-v1:0
        MODEL_ID = "amazon.nova-pro-v1:0"

        # Define your user_message as multi-line string
        user_message = f"""
        You are a helpful assistant that generates short stories 
        Generate a short story (around 500 words) based on the title.
        The output need to be a json formatted
        """
   
        # Prepare the request payload       
        try:
            request_payload = {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": user_message}]
                    }
                ],
                "inferenceConfig": {
                    "temperature": 0.7,
                    "topP": 0.9,
                    "maxTokens": 512
                }
            }
        except NameError as e:
            error_response = {
                "statusCode": 500,
                "body": f"NameError: {str(e)}."
            }
            return error_response

        try:
            # Invoke the model
            response = bedrock_runtime.invoke_model(
                modelId=MODEL_ID,
                body=json.dumps(request_payload)
            )
 
        # Parse response_body and print the story from ['output']['message']['content'][0]['text']
            response_body = json.loads(response['body'].read())
            story = response_body['output']['message']['content'][0]['text']
            print(story)

        # Store the title and story in variables

            title = event.get('title', 'Untitled')
            story_content = story
            

        # Create a random 10 character uid
            uid = hashlib.md5(title.encode()).hexdigest()[:10]

        # Put the story in S3 BUCKET_NAME as a text file using the uid as the filename
            s3 = boto3.resource('s3')
            s3.Object(BUCKET_NAME, f"{uid}.txt").put(Body=story_content)

        # 
        dynamodb = boto3.client('dynamodb')
            dynamodb.put_item(
                TableName=TABLE_NAME,
                Item={
                    'title': {'S': title},
                    'uid': {'S': uid},
                    'bucket': {'S': BUCKET_NAME}
                }
            )
        # Return a success response with message
            return {
                'statusCode': 200,
                'body': f"Story saved ro s3 with {uid}.txt"
            }

        except Exception as e:
            return {
                'statusCode': 501,
                'body': json.dumps(f"Error: {str(e)}")
            }
