from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import os
import stripe

router = APIRouter(prefix="/webhook", tags=["webhook"])

@router.post("/stripe", include_in_schema=False)
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    event = None
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "message": f"Webhook error: {str(e)}"})

    # Handle the event
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_mobile = session["metadata"].get("user_mobile")
        # Upgrade user to Pro in DB
        from app.core.database import AsyncSessionLocal
        from app.models.user import User
        from sqlalchemy import select
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(User).where(User.mobile == user_mobile))
            user = result.scalars().first()
            if user:
                user.subscription = "Pro"
                db.add(user)
                await db.commit()
    # Add more event types as needed
    return JSONResponse(status_code=200, content={"success": True})
