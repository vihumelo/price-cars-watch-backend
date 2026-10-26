FROM public.ecr.aws/lambda/python:3.12

COPY services/notifications/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

COPY services/shared/ "${LAMBDA_TASK_ROOT}/services/shared/"
COPY services/notifications/src/ "${LAMBDA_TASK_ROOT}/services/notifications/src/"

CMD ["services.notifications.src.handlers.new_listings_email.handler"]
