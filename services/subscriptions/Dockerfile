FROM public.ecr.aws/lambda/python:3.12

COPY services/subscriptions/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

COPY services/shared/ "${LAMBDA_TASK_ROOT}/services/shared/"
COPY services/subscriptions/src/ "${LAMBDA_TASK_ROOT}/services/subscriptions/src/"

CMD ["services.subscriptions.src.handlers.subscriptions.handler"]
