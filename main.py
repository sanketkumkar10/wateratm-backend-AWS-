from fastapi import FastAPI, Request, HTTPException
import hmac
import hashlib
import time
import os
from dotenv import load_dotenv

load_dotenv()

RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET")
if not RAZORPAY_WEBHOOK_SECRET:
    raise RuntimeError("RAZORPAY_WEBHOOK_SECRET is required in environment variables")

app = FastAPI()

LATEST_PAYMENT = {
    "paid": False,
    "amount": 0,
    "timestamp": 0,
    "used": True,
    "payment_id": None,
}

PAYMENT_EXPIRY_SECONDS = 300


@app.get("/")
def root():
    return {"status": "Backend Running"}


@app.post("/razorpay-webhook")
async def webhook(request: Request):
    print("🔥 WEBHOOK RECEIVED")

    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature")

    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature")

    expected = hmac.new(
        RAZORPAY_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(signature, expected):
        print("❌ Invalid signature")
        raise HTTPException(status_code=400, detail="Invalid signature")

    data = await request.json()

    if data.get("event") == "payment.captured":
        p = data["payload"]["payment"]["entity"]

        LATEST_PAYMENT.update(
            {
                "paid": True,
                "amount": p["amount"] // 100,
                "timestamp": int(time.time()),
                "used": False,
                "payment_id": p["id"],
            }
        )

        print("✅ Payment stored:", p["id"])

    return {"status": "ok"}


@app.get("/payment/latest")
def latest():
    now = int(time.time())

    if LATEST_PAYMENT["paid"] and not LATEST_PAYMENT["used"]:
        if now - LATEST_PAYMENT["timestamp"] > PAYMENT_EXPIRY_SECONDS:
            LATEST_PAYMENT["paid"] = False
            LATEST_PAYMENT["used"] = True

    return LATEST_PAYMENT


@app.post("/payment/use")
def use():
    if LATEST_PAYMENT["used"]:
        return {"status": "already used"}

    LATEST_PAYMENT["used"] = True
    LATEST_PAYMENT["paid"] = False

    return {"status": "used"}
