from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
import os
import stripe

router = APIRouter(prefix="/subscribe", tags=["subscribe"])

STRIPE_API_KEY = os.getenv("STRIPE_API_KEY")
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID", "Price_12345")  # Set your actual Stripe price ID here
stripe.api_key = STRIPE_API_KEY

@router.post("/pro", response_class=JSONResponse, status_code=status.HTTP_201_CREATED)
async def subscribe_pro(request: Request):
    # Get user from JWT middleware
    mobile = getattr(request.state, "user_mobile", None)
    if not mobile:
        return JSONResponse(status_code=401, content={"success": False, "message": "Unauthorized"})
    # Create Stripe Checkout session
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": STRIPE_PRICE_ID,
                "quantity": 1,
            }],
            mode="subscription",
            success_url=os.getenv("STRIPE_SUCCESS_URL", "http://localhost:8000/success"),
            cancel_url=os.getenv("STRIPE_CANCEL_URL", "http://localhost:8000/cancel"),
            metadata={"user_mobile": mobile}
        )
        return JSONResponse(status_code=201, content={"success": True, "checkout_url": session.url})
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "message": str(e)})
