import json
import urllib.parse
import boto3
from botocore.exceptions import ClientError
import csv
import os
from io import StringIO
from collections import deque

print('Loading function')

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

def look_around(maze, row, col, been):

    # Assuming it is a square maze and setting boundaries
    # Technically checking if we are at the edge is excessive because because we call this function 
    # from the edge only once at the start. The rest of the time being at the edge means we've found 
    # a way out, so we do not look around
    max_dimension = len(maze) - 1
    min_dimension = 0

    # Left, Down, Up, Right
    targets = [(row,  col - 1), (row + 1,  col), (row - 1,  col), (row,  col + 1)]
    
    for r, c in targets:
        if r >= min_dimension and r <= max_dimension and c >= min_dimension and c <= max_dimension:
            if maze[r][c] == "1" and (r, c) not in been:
                yield (r, c)

def find_entrance(maze):
    rows = len(maze)
    cols = len(maze[0])
    
    # Check top row
    for col in range(cols):
        if maze[0][col] == "1":
            return (0, col)
    
    # Check bottom row
    for col in range(cols):
        if maze[rows - 1][col] == "1":
            return (rows - 1, col)
    
    # Check left column
    for row in range(1, rows - 1):  # Exclude corners already checked
        if maze[row][0] == "1":
            return (row, 0)
    
    # Check right column
    for row in range(1, rows - 1):  # Exclude corners already checked
        if maze[row][cols - 1] == "1":
            return (row, cols - 1)
    
    raise Exception('Did not find an entrance into the maze')


def solve_maze(maze):
    start_row, start_col = find_entrance(maze)
    start = (start_row, start_col)
    print(f'Found maze entrance at ({start_row}, {start_col})')

    node_queue = deque([(start_row, start_col, [])])
    been = set()
    steps = 0
    step_limit = 10**9
    
    while len(node_queue):
        steps += 1
        
        if steps == step_limit:
            raise Exception(f'Could not solve in {step_limit} iterations')
        
        row, col, path = node_queue.popleft()
        
        current_loc = (row, col)
    
        if current_loc in been:
            continue
        else:
            been.add(current_loc)
    
        # Check if we are at the edge of the maze (and not back at the start) i.e. found a way out
        if (0 in current_loc or len(maze)-1 in current_loc) and start != current_loc:
            path.append(current_loc)
            print(f"Found a way out. Took {steps} steps. The distance from start to finish is {len(path)}")
            break
    
        for r, c in look_around(maze, row, col, been):
            updated_path = path + [(row, col)]
            node_queue.append((r, c, updated_path))

    for i in range(len(maze)):
        for j in range(len(maze[i])):
            location = (i, j)
            if maze[i][j] == "1" and location in path:
                maze[i][j] = "2"
                
    return maze, steps, len(path)

def lambda_handler(event, context):
    # Environment Variables
    target_bucket = os.environ['TARGET_BUCKET']
    key_prefix = os.getenv('KEY_PREFIX', 'processed')
    table_name = os.environ['TABLE_NAME']
    
    print('Retrieved environment variables')
    
    # Process each record in the event
    for record in event.get('Records', []):
        bucket = record['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(record['s3']['object']['key'], encoding='utf-8')
        print(f'Processing S3 object {bucket}: {key}')
        
        target_key = f'{key_prefix}_{key}'
        
        try:
            # Get object from S3
            response = s3.get_object(Bucket=bucket, Key=key)
            content = response['Body'].read().decode('utf-8')
            print('Received object from S3 and decoded')

            # Process CSV content
            csv_content = StringIO(content)
            csv_reader = csv.reader(csv_content)
            maze = [row for row in csv_reader]
            print('CSV content read successfully')

            # Solve the maze
            solved_maze, iterations, length_of_path = solve_maze(maze)
            print('Maze solved successfully')

            # Convert result back to CSV
            output = StringIO()
            csv.writer(output).writerows(solved_maze)
            processed_content = output.getvalue()
            print('Processed content converted to CSV')

            # Prepare item for DynamoDB
            table = dynamodb.Table(table_name)
            item = {
                "file_name": target_key,
                "stats": {
                    "iterations": iterations,
                    "length_of_path": length_of_path
                }
            }
            print('Prepared item for DynamoDB')

            # Store item in DynamoDB with idempotency check
            try:
                table.put_item(
                    Item=item,
                    ConditionExpression='attribute_not_exists(file_name)'
                )
                print(f"Successfully processed and stored data for {target_key}.")
            except ClientError as e:
                if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                    print(f"Item with file_name {target_key} already exists.")
                    raise
                else:
                    print(f"Failed to write to DynamoDB: {e}")
                    raise

            # Upload processed content to S3
            try:
                s3.put_object(Bucket=target_bucket, Key=target_key, Body=processed_content)
                print('Processed content uploaded to S3 successfully')
            except ClientError as e:
                print(f'Error uploading processed content to S3: {e}')
                raise
            
        except Exception as e:
            print(f'Error processing object {key} from bucket {bucket}: {e}')
    
    return {
        'statusCode': 200,
        'body': json.dumps('Event processed successfully')
    }
