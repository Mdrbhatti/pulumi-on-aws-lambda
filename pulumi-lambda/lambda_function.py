import json
import os
import logging
import pulumi
from pulumi import automation as auto
from pulumi_aws import s3

LOG_LEVEL = os.environ.get("LOG_LEVEL", "DEBUG")

PULUMI_AWS_REGION = "eu-central-1"
PULUMI_PROJECT_NAME = "pulumi-lambda-static-site"
# Note: make sure the plugins are the same version
# as defined in requirements.txt
PULUMI_STACK_PLUGINS = {"aws": "v5.16.2"}

LOGGER = logging.getLogger()
LOGGER.setLevel(LOG_LEVEL)


class PulumiInlineProgram:
    def __init__(self):
        self.ws = auto.LocalWorkspace()
        for plugin, version in PULUMI_STACK_PLUGINS.items():
            self.ws.install_plugin(plugin, version)

        self.project_name = "dev"
        self.stack_name = "dev"
        self.index_content = "hello world\n"

        # create a new stack, generating our pulumi program on the fly from the POST body
        self.stack = auto.create_stack(
            stack_name=self.stack_name,
            project_name=PULUMI_PROJECT_NAME,
            program=self.__pulumi_program,
        )
        self.stack.set_config("aws:region", auto.ConfigValue(PULUMI_AWS_REGION))

        self.stack.up(on_output=LOGGER.info)

    def __pulumi_program(self):
        """Pulumi program for creating a static website hosted on S3"""

        # Create a bucket and expose a website index document
        site_bucket = s3.Bucket(
            "s3-website-bucket",
            website=s3.BucketWebsiteArgs(index_document="index.html"),
        )

        # Write our index.html into the site bucket
        s3.BucketObject(
            "index",
            bucket=site_bucket.id,
            content=self.index_content,
            key="index.html",
            content_type="text/html; charset=utf-8",
        )

        # Set the access policy for the bucket so all objects are readable
        s3.BucketPolicy(
            "bucket-policy",
            bucket=site_bucket.id,
            policy={
                "Version": "2012-10-17",
                "Statement": {
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": ["s3:GetObject"],
                    # Policy refers to bucket explicitly
                    "Resource": [
                        pulumi.Output.concat("arn:aws:s3:::", site_bucket.id, "/*")
                    ],
                },
            },
        )

        # Export the website URL
        pulumi.export("website_url", site_bucket.website_endpoint)


def lambda_handler(event, _ctx):
    """Entrypoint for AWS lambda function"""
    try:
        LOGGER.info(f"Environment: {os.environ}")
        LOGGER.info(f"Event: {event}")

        # todo: handle events and provision bucket
        return json.dumps({"message": "not yet implemented"})
    except BaseException as ex:
        LOGGER.exception("Failed Execution: %s", ex)
        raise ex


if __name__ == "__main__":
    program = PulumiInlineProgram()
