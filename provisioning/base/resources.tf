provider "aws" {
  region     = "us-east-1"
}

locals {
  log_metric_name = "HoldShelfPollerLogError-${var.environment}"
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

data "aws_sns_topic" "rc_alarms" {
  name = "research-catalog-team-alarms-${var.environment}"
}

resource "aws_cloudwatch_log_metric_filter" "error_metric_filter" {
  name           = local.log_metric_name
  pattern        = "{ $.level = \"error\" }"
  log_group_name = "/aws/lambda/${aws_lambda_function.lambda_instance.function_name}"

  metric_transformation {
    name      = local.log_metric_name
    namespace = "LogMetrics"
    value     = "1"
  }
}

resource "aws_cloudwatch_metric_alarm" "log_errors" {
  alarm_name          = "HoldShelfPollerLogErrorAlarm-${var.environment}"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = local.log_metric_name
  namespace           = "LogMetrics"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Lambda function ${aws_lambda_function.lambda_instance.function_name} has more than 0 error logs in 5 minutes"
  alarm_actions       = [data.aws_sns_topic.rc_alarms.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.lambda_instance.function_name
  }
}

resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "HoldShelfPollerLambdaErrorAlarm-${var.environment}"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Lambda function ${aws_lambda_function.lambda_instance.function_name} has more than 0 errors in 5 minutes"
  alarm_actions       = [data.aws_sns_topic.rc_alarms.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.lambda_instance.function_name
  }
}
