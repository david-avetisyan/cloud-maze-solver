output "bucket_name" {
  value = aws_s3_bucket.main.bucket
}

output "lambda_function_name" {
  value = aws_lambda_function.process_file.function_name
}

output "dynamodb_table_name" {
  value = aws_dynamodb_table.processed_files.name
}

output "api_endpoint" {
  value = "https://${aws_api_gateway_rest_api.api.id}.execute-api.eu-north-1.amazonaws.com/${aws_api_gateway_deployment.deployment.stage_name}"
}

output "api_key" {
  value = aws_api_gateway_api_key.api_key.value
  sensitive = true
}
