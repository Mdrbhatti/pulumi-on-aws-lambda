import json
import os
import logging
import pulumi
from pulumi import automation as auto
from pulumi_aws import s3


AWS_REGION = os.environ["AWS_REGION"]
PULUMI_BACKEND_URL = os.environ["PULUMI_BACKEND_URL"]
PULUMI_SECRETS_PROVIDER = os.environ["PULUMI_SECRETS_PROVIDER"]
PULUMI_HOME = os.environ["PULUMI_HOME"]
# Note: make sure the plugins are the same version
# as defined in requirements.txt
PULUMI_STACK_PLUGINS = {"aws": "v5.20.0"}

LOG_LEVEL = os.environ.get("LOG_LEVEL", "DEBUG")
LOGGER = logging.getLogger()
LOGGER.setLevel(LOG_LEVEL)


def log_update_summary(result):
    LOGGER.info(
        f"update summary: \n{json.dumps(result.summary.resource_changes, indent=4)}"
    )


class PulumiInlineProgram:
    def __init__(self, name, index_content=None):
        self.project_name = "pulumi-lambda-static-site"
        self.backend_url = PULUMI_BACKEND_URL
        self.secrets_provider = PULUMI_SECRETS_PROVIDER
        self.pulumi_work_dir = PULUMI_HOME
        self.runtime = "python"
        self.index_content = index_content

        self.stack_name = f"{self.project_name}.{name}"

        self.local_workspace_options = auto.LocalWorkspaceOptions(
            project_settings=auto.ProjectSettings(
                name=self.project_name,
                runtime=self.runtime,
                backend=auto.ProjectBackend(url=self.backend_url),
            ),
            secrets_provider=self.secrets_provider,
            stack_settings={
                self.stack_name: auto.StackSettings(
                    secrets_provider=self.secrets_provider
                )
            },
        )

        self.stack = auto.create_or_select_stack(
            stack_name=self.stack_name,
            work_dir=self.pulumi_work_dir,
            project_name=self.project_name,
            program=self.__pulumi_program,
            opts=self.local_workspace_options,
        )

        self.stack.set_config("aws:region", auto.ConfigValue(AWS_REGION))

        # install plugins required by the pulumi program
        for plugin, version in PULUMI_STACK_PLUGINS.items():
            self.stack.workspace.install_plugin(plugin, version)

    def run(self, operation):
        if operation == "create":
            result = self.stack.up(on_output=LOGGER.info)
            log_update_summary(result)
            response = {
                "status": "created",
                "website_url": result.outputs["website_url"].value,
            }
        elif operation == "destroy":
            result = self.stack.destroy(on_output=LOGGER.info)
            log_update_summary(result)

            self.stack.workspace.remove_stack(self.stack_name)
            LOGGER.info("successfully removed stack")

            response = {"status": "destroyed"}
        else:
            response = {
                "status": "failed",
                "message": f"invalid operation `{operation}`. choose either `create` or `destroy`",
            }

        return json.dumps(response)

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
        LOGGER.debug(f"environment: {os.environ}")
        LOGGER.debug(f"event: {event}")

        body = json.loads(event["body"])

        program = PulumiInlineProgram(
            name=body["name"].lower(),
            # index content not available during destroy operation
            index_content=body.get("index_content", None),
        )

        return program.run(body["operation"])
    except BaseException as ex:
        LOGGER.exception("failed Execution: %s", ex)
        raise ex


if __name__ == "__main__":
    # for local testing
    p = PulumiInlineProgram("dev", "hello world\n")
    p.run("create")
