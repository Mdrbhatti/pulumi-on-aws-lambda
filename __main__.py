import os
import json
import pulumi
import pulumi_aws as aws
import pulumi_awsx as awsx

PULUMI_BACKEND_URL = os.environ.get("PULUMI_BACKEND_URL", "file:///tmp")
PULUMI_SECRETS_PROVIDER = os.environ.get("PULUMI_SECRETS_PROVIDER", "passphrase")

lambda_ecr_repository = aws.ecr.Repository(
    "lambda-ecr-repository",
    image_scanning_configuration=aws.ecr.RepositoryImageScanningConfigurationArgs(
        scan_on_push=False,
    ),
    image_tag_mutability="MUTABLE",
)

lambda_ecr_docker_image = awsx.ecr.Image(
    "lambda-docker-image-ecr",
    repository_url=lambda_ecr_repository.repository_url,
    dockerfile="./pulumi-lambda/Dockerfile",
    path="./pulumi-lambda",
)

lambda_iam_role = aws.iam.Role(
    "lambda-iam-role",
    assume_role_policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "AllowAssumeRole",
                    "Effect": "Allow",
                    "Action": "sts:AssumeRole",
                    "Principal": {"Service": "lambda.amazonaws.com"},
                }
            ],
        }
    ),
    inline_policies=[
        aws.iam.RoleInlinePolicyArgs(
            name="AllowCWLoggingAccess",
            policy=json.dumps(
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Sid": "AllowCloudwatchLogsAccess",
                            "Effect": "Allow",
                            "Resource": "arn:aws:logs:*:*:*",
                            "Action": [
                                "logs:PutLogEvents",
                                "logs:DescribeLogStreams",
                                "logs:CreateLogStream",
                                "logs:CreateLogGroup",
                            ],
                        }
                    ],
                }
            ),
        ),
        aws.iam.RoleInlinePolicyArgs(
            # Note: update this policy if lambda needs more permissions for deploying pulumi program
            name="AllowS3Access",
            policy=json.dumps(
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Sid": "AllowS3Access",
                            "Effect": "Allow",
                            "Action": ["s3:*"],
                            "Resource": "*",
                        }
                    ],
                }
            ),
        ),
    ],
)

lambda_function = aws.lambda_.Function(
    "pulumi-lambda-function",
    package_type="Image",
    image_uri=lambda_ecr_docker_image.image_uri,
    role=lambda_iam_role.arn,
    memory_size=2048,
    # required when installing pulumi plugins in the lambda function
    ephemeral_storage=aws.lambda_.FunctionEphemeralStorageArgs(size=1024),
    timeout=900,  # 15 minutes which is the max timeout
    environment=aws.lambda_.FunctionEnvironmentArgs(
        variables={
            "LOG_LEVEL": "DEBUG",
            "PULUMI_BACKEND_URL": PULUMI_BACKEND_URL,
            "PULUMI_SECRETS_PROVIDER": PULUMI_SECRETS_PROVIDER,
        },
    ),
)

lambda_function_url = aws.lambda_.FunctionUrl(
    "lambda-function-url",
    function_name=lambda_function.name,
    authorization_type="NONE",
    cors=aws.lambda_.FunctionUrlCorsArgs(
        allow_credentials=True,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
        max_age=86400,
    ),
)

pulumi.export("url", lambda_function_url.function_url)
