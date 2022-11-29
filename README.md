# pulumi-on-aws-lambda

Minimal Pulumi program that showcases the use of [Pulumi Automation API](https://www.pulumi.com/docs/guides/automation-api/) from within an AWS Lambda function.

Background for this showcase is detailed here: https://justedagain.com/posts/2022/pulumi-on-aws-lambda/


The program provisions the following AWS resources:
- ECR repository for hosting lambda docker container images
- Lambda function accessible via a [function url](https://docs.aws.amazon.com/lambda/latest/dg/lambda-urls.html).
  - Deployed as a docker container image, with Pulumi CLI installed
  - The lambda handler can run a [Pulumi inline program](https://github.com/pulumi/automation-api-examples/tree/main/python/inline_program) which provisions an S3 static site. A unique Pulumi stack is used for provisioning the S3 static site.

## Prerequisites

- [Pulumi](https://www.pulumi.com/docs/get-started/install/)
- [Python 3.7+](https://www.pulumi.com/docs/intro/languages/python/)
- [Docker](https://docs.docker.com/get-docker/)

Note: this project assumes the use of a self-managed backend. To set up such a backend see this [blogpost](https://justedagain.com/posts/2022/pulumi-backend-bootstrap/) and this [Github Project](https://github.com/Mdrbhatti/pulumi-backend-bootstrap).

## Deploy

Ensure that the `PULUMI_BACKEND_URL` and `PULUMI_SECRETS_PROVIDER` environment variables are set before proceeding.

```bash
pulumi stack init pulumi-on-aws-lambda.dev --secrets-provider=$PULUMI_SECRETS_PROVIDER
pulumi config set aws:region eu-central-1

# Deploy pulumi stack
pulumi up --diff

# Once deployment is complete, lambda function URL can be accessed like this
pulumi stack output url
```

Once deployment is complete, a POST request can be sent to the lambda function url for creating a static website. It is safe to invoke this lambda in parallel (as long as the `name` parameter is unique) for creation of multiple static websites hosted on S3.

```bash
# Invoke lambda via function url to create a static website
$ curl --location --request POST $(pulumi stack output url) --header 'Content-Type: application/json' --data-raw '{"operation": "create","name": "hello","index_content": "hello world"}' 
{"status": "created", "website_url": "s3-website-bucket-xxxxx.s3-website.eu-central-1.amazonaws.com"}%                         

# Access static website
$ curl s3-website-bucket-xxxxx.s3-website.eu-central-1.amazonaws.com
hello world%

# Invoke lambda via function url to destroy static website
$ curl --location --request POST $(pulumi stack output url) --header 'Content-Type: application/json' --data-raw '{"operation": "destroy","name": "hello"}' 
{"status": "destroyed"}%                                                                                                         
```
