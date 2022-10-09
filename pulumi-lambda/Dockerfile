FROM public.ecr.aws/lambda/python:3.9

# https://docs.aws.amazon.com/lambda/latest/dg/python-image.html#python-image-create
WORKDIR ${LAMBDA_TASK_ROOT}

COPY requirements.txt .

RUN pip install -r requirements.txt --target .

COPY lambda_function.py .

CMD ["lambda_function.lambda_handler"]
