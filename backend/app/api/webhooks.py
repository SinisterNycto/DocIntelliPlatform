import os
from fastapi import APIRouter, Request, HTTPException, Header
from svix.webhooks import Webhook, WebhookVerificationError
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

CLERK_WEBHOOK_SECRET = os.getenv("CLERK_WEBHOOK_SECRET")

@router.post("/clerk")
async def clerk_webhook(
    request: Request,
    svix_id: str = Header(None, alias="svix-id"),
    svix_timestamp: str = Header(None, alias="svix-timestamp"),
    svix_signature: str = Header(None, alias="svix-signature")
):
    if not CLERK_WEBHOOK_SECRET:
        logger.error("CLERK_WEBHOOK_SECRET is not set")
        raise HTTPException(status_code=500, detail="Server configuration error")

    if not svix_id or not svix_timestamp or not svix_signature:
        raise HTTPException(status_code=400, detail="Missing Svix headers")

    payload = await request.body()
    
    # Initialize Svix Webhook
    wh = Webhook(CLERK_WEBHOOK_SECRET)
    
    try:
        # Verify the webhook signature
        event = wh.verify(
            payload,
            {
                "svix-id": svix_id,
                "svix-timestamp": svix_timestamp,
                "svix-signature": svix_signature
            }
        )
    except WebhookVerificationError as e:
        logger.error(f"Webhook verification failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid webhook signature")
        
    event_type = event.get("type")
    data = event.get("data", {})
    
    if event_type == "user.created":
        user_id = data.get("id")
        email = data.get("email_addresses", [{}])[0].get("email_address", "")
        # TODO: Get MongoDB client from app state and insert user record
        # For now, we log it
        logger.info(f"Clerk User Created: {user_id} - {email}")
        
    elif event_type == "user.deleted":
        user_id = data.get("id")
        logger.info(f"Clerk User Deleted: {user_id}")
        # TODO: Delete user from MongoDB and cascade delete projects
        
    return {"success": True}
