provider "aws" {
  region     = "us-east-1"
}

variable "environment" {
  type = string
  default = "qa"
  description = "The name of the environnment (qa, production). This controls the name of lambda and the env vars loaded."

  validation {
    condition     = contains(["qa", "production"], var.environment)
    error_message = "The environmnet must be 'qa' or 'production'."
  }
}

variable "vpc_config" {
  type = map
  description = "The name of the environnment (qa, production)"
}

# Upload the zipped app to S3:
resource "aws_s3_object" "uploaded_zip" {
  bucket = "nypl-github-actions-builds-${var.environment}"
  key    = "holdshelf-poller-${var.environment}-dist.zip"
  acl    = "private"
  source = "../../build/build.zip"
  etag = filemd5("../../build/build.zip")
}

# Create the lambda:
resource "aws_lambda_function" "lambda_instance" {
  description   = "A poller to identify items recently placed on a holdshelf and trigger a notification."
  function_name = "HoldshelfPoller-${var.environment}"
  handler       = "main.handle_event"
  memory_size   = 128
  role          = "arn:aws:iam::946183545209:role/lambda-full-access"
  runtime       = "python3.9"
  timeout       = 60

  # Location of the zipped code in S3:
  s3_bucket     = aws_s3_object.uploaded_zip.bucket
  s3_key        = aws_s3_object.uploaded_zip.key

  # Trigger pulling code from S3 when the zip has changed:
  source_code_hash = filebase64sha256("../../build/build.zip")

  vpc_config {
    subnet_ids         = var.vpc_config.subnet_ids
    security_group_ids = var.vpc_config.security_group_ids
  }

  # Load ENV vars from ./config/{environment}.env
  environment {
    variables = {
      ENVIRONMENT = var.environment
    }
  }
}
