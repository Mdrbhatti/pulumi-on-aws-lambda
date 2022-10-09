FROM public.ecr.aws/lambda/python:3.9 AS builder

ARG PULUMI_VERSION=3.42.0

# tar, gzip required by pulumi install script
RUN yum install tar gzip -y && \
    curl -fsSL https://get.pulumi.com/ | bash -s -- --version $PULUMI_VERSION

# https://docs.aws.amazon.com/lambda/latest/dg/python-image.html#python-image-create
WORKDIR ${LAMBDA_TASK_ROOT}

# copy and install requirements first to make use of docker layer caching
COPY requirements.txt .
RUN pip install -r requirements.txt --target .

# copy lambda sources
COPY lambda_function.py .

FROM public.ecr.aws/lambda/python:3.9

ARG PULUMI_BIN_PATH=/pulumi/bin

COPY --from=builder ${LAMBDA_TASK_ROOT} ${LAMBDA_TASK_ROOT}
COPY --from=builder /root/.pulumi/bin/pulumi ${PULUMI_BIN_PATH}/pulumi

# make pulumi binary executable
RUN chmod 755 ${PULUMI_BIN_PATH}/pulumi
# add binary to path and specify PULUMI_HOME to use the only writable directory on Lambda
ENV PATH="${PULUMI_BIN_PATH}:${PATH}" \
    PULUMI_HOME="/tmp" \
    PULUMI_CONFIG_PASSPHRASE=""

CMD ["lambda_function.lambda_handler"]