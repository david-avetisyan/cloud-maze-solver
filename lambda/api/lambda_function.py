import json
import boto3
from botocore.exceptions import ClientError
import os
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    http_method = event['httpMethod']
    if http_method == 'GET':
        return get_item(event)
    elif http_method == 'POST':
        return create_item(event)
    elif http_method == 'DELETE':
        return delete_item(event)
    else:
        return {
            'statusCode': 405,
            'body': json.dumps('Method Not Allowed')
        }

def convert_decimal_to_float(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimal_to_float(i) for i in obj]
    else:
        return obj

def get_item(event):
    try:
        # Validate that 'queryStringParameters' is present
        if 'queryStringParameters' not in event or not event['queryStringParameters']:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing query parameters'})
            }

        # Validate that 'file_name' is present in 'queryStringParameters'
        if 'file_name' not in event['queryStringParameters']:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing query parameter: file_name'})
            }

        # Extract file_name from query parameters
        file_name = event['queryStringParameters']['file_name']

        # Validate that file_name is not empty
        if not file_name:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'file_name cannot be empty'})
            }

        # Attempt to get the item from DynamoDB
        try:
            response = table.get_item(Key={'file_name': file_name})
            if 'Item' in response:
                # Convert Decimal to float
                item = convert_decimal_to_float(response['Item'])
                return {
                    'statusCode': 200,
                    'body': json.dumps(item)
                }
            else:
                return {
                    'statusCode': 404,
                    'body': json.dumps({'error': 'Record not found'})
                }
        except ClientError as e:
            # Log the error and return a generic server error response
            print(f"Error retrieving item from DynamoDB: {e.response['Error']['Message']}")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': f"Error retrieving item: {str(e)}"})
            }

    except Exception as e:
        # Log unexpected errors and return a server error response
        print(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f"Unexpected error occurred: {str(e)}"})
        }

def create_item(event):
    try:
        # Validate that 'body' is present in the event and parse JSON
        if 'body' not in event:
            return {
                'statusCode': 400,
                'body': json.dumps('Missing request body')
            }

        try:
            item = json.loads(event['body'])
        except json.JSONDecodeError:
            return {
                'statusCode': 400,
                'body': json.dumps('Invalid JSON format')
            }

        # Ensure 'file_name' is present in the item
        if 'file_name' not in item:
            return {
                'statusCode': 400,
                'body': json.dumps('Missing file_name in request body')
            }

        # Attempt to write to DynamoDB with conditional expression
        try:
            table.put_item(
                Item=item,
                ConditionExpression='attribute_not_exists(file_name)'  # Ensure no overwrite
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                return {
                    'statusCode': 409,  # Conflict status code for duplicate item
                    'body': json.dumps(f"Item with file_name {item['file_name']} already exists.")
                }
            else:
                # Log the error and return a generic server error response
                print(f"Error inserting item into DynamoDB: {e.response['Error']['Message']}")
                return {
                    'statusCode': 500,
                    'body': json.dumps(f"Error inserting item into DynamoDB: {str(e)}")
                }

        # Return success response
        return {
            'statusCode': 201,
            'body': json.dumps('Item created successfully')
        }

    except Exception as e:
        # Log unexpected errors and return a server error response
        print(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Unexpected error occurred: {str(e)}")
        }

def delete_item(event):
    try:
        # Validate that 'queryStringParameters' is present
        if 'queryStringParameters' not in event or not event['queryStringParameters']:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing query parameters'})
            }

        # Validate that 'file_name' is present in 'queryStringParameters'
        if 'file_name' not in event['queryStringParameters']:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing query parameter: file_name'})
            }

        # Extract file_name from query parameters
        file_name = event['queryStringParameters']['file_name']

        # Validate that file_name is not empty
        if not file_name:
            return {
                'statusCode': 400,
                'body': json.dumps('file_name cannot be empty')
            }

        # Attempt to delete the item from DynamoDB
        try:
            response = table.delete_item(Key={'file_name': file_name}, ReturnValues='ALL_OLD')
            # Check if the item was found and deleted
            if 'Attributes' not in response:
                return {
                    'statusCode': 404,
                    'body': json.dumps(f"Item with file_name {file_name} not found.")
                }
            else:
                return {
                    'statusCode': 200,
                    'body': json.dumps('Item deleted successfully')
                }
        except ClientError as e:
            # Log the error and return a generic server error response
            print(f"Error deleting item from DynamoDB: {e.response['Error']['Message']}")
            return {
                'statusCode': 500,
                'body': json.dumps(f"Error deleting item from DynamoDB: {str(e)}")
            }

    except Exception as e:
        # Log unexpected errors and return a server error response
        print(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Unexpected error occurred: {str(e)}")
        }
