# ngt-demo-david-avetisyan

# NGT Demo Project

## Project Overview

This project demonstrates a serverless architecture using AWS services. The primary components include an AWS Lambda function and Terraform configuration to deploy the necessary infrastructure. The Lambda function processes files uploaded to an S3 bucket and writes the results to a DynamoDB table. Additionally, an API Gateway is set up to interact with the DynamoDB table through a REST API.

## Project Components

### 1. AWS Lambda Function
The Lambda function is written in Python and is responsible for:
- Processing files uploaded to an S3 bucket.
- Solving a maze from the CSV content of the files.
- Storing the processed results in another S3 bucket.
- Writing summary statistics to a DynamoDB table.

### 2. Terraform Configuration
The Terraform configuration files are used to define and deploy the infrastructure:
- **main.tf**: Main configuration file that includes the definition of resources such as S3 buckets, Lambda functions, DynamoDB table, and API Gateway.
- **outputs.tf**: Defines outputs for the configuration.
- **provider.tf**: Configures the AWS provider.

### 3. API Gateway
The API Gateway is set up to provide a REST API interface for CRUD operations on the DynamoDB table. It includes:
- Methods for `POST`, `DELETE`, and `GET` requests.
- Integration with the Lambda function to handle these requests.
- API keys for securing the API endpoints and rate limiting usage plan.


## Getting Started

### Prerequisites
- AWS account with appropriate permissions.
- Terraform installed on your local machine.
- AWS CLI configured with your credentials.

### Deployment Steps

1. **Clone the repository:**
   git clone https://github.com/david-avetisyan/ngt-demo-david-avetisyan.git
   cd your-repo

2. **Initialise terraform and apply:**
    cd terraform
    terraform init
    terraform apply
