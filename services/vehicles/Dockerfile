FROM public.ecr.aws/lambda/python:3.12

COPY services/vehicles/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

COPY services/shared/ "${LAMBDA_TASK_ROOT}/services/shared/"
COPY services/vehicles/src/ "${LAMBDA_TASK_ROOT}/services/vehicles/src/"

CMD ["services.vehicles.src.handlers.vehicles.handler"]
