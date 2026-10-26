FROM public.ecr.aws/lambda/python:3.12

COPY services/monitoring/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

COPY services/shared/ "${LAMBDA_TASK_ROOT}/services/shared/"
COPY services/monitoring/src/ "${LAMBDA_TASK_ROOT}/services/monitoring/src/"

CMD ["services.monitoring.src.handlers.monitoring.handler"]
