from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, Request
from django.conf import settings
from django.contrib.auth import get_user_model
from svix.webhooks import Webhook, WebhookVerificationError
from .schemas import (
    ClerkWebhook,
    ClerkWebhookEvent,
)
from .models import Organization

router = APIRouter(prefix="/auth", tags=["auth"])


async def verify_clerk_webhook(request: Request):
    headers = request.headers
    payload = await request.body()

    try:
        wh = Webhook(settings.CLERK_WEBHOOK_SIGNING_SECRET)
        msg = wh.verify(payload, headers)
        return ClerkWebhook.model_validate(msg)
    except WebhookVerificationError as e:
        print("Webhook verification failed:", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid webhook signature"
        )
    except Exception as e:
        raise e


@router.post("/clerk_webhook/")
def clerk_webhook(event: ClerkWebhook = Depends(verify_clerk_webhook)):
    if event.type in [
        ClerkWebhookEvent.USER_CREATED,
        ClerkWebhookEvent.USER_UPDATED,
        ClerkWebhookEvent.USER_DELETED,
    ]:
        User = get_user_model()
        User.handle_clerk_webhook(event)
    elif event.type in [
        ClerkWebhookEvent.ORGANIZATION_CREATED,
        ClerkWebhookEvent.ORGANIZATION_UPDATED,
        ClerkWebhookEvent.ORGANIZATION_DELETED,
        ClerkWebhookEvent.ORGANIZATION_MEMBERSHIP_CREATED,
        ClerkWebhookEvent.ORGANIZATION_MEMBERSHIP_DELETED,
        ClerkWebhookEvent.ORGANIZATION_MEMBERSHIP_UPDATED,
    ]:
        Organization.handle_clerk_webhook(event)

    return "OK"


def register_routers(app: FastAPI):
    app.include_router(router)
