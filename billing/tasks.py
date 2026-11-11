from celery import shared_task

from billing.services import handle_stripe_webhook_payload


@shared_task
def process_stripe_webhook_task(payload: dict):
    handle_stripe_webhook_payload(payload)
