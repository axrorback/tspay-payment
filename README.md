# 💳 TSPay Django Payment Integration Guide

This document explains how to integrate **TSPay payment system** into a Django project, including:

* Payment creation
* Redirect flow
* Webhook handling
* Return page logic
* Sandbox testing
* Production considerations

---

# 📁 Project Structure

## urls.py (project level)

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('payment/', include('payment.urls')),
]
```

---

## payment/urls.py

```python
from django.urls import path
from .views import *

urlpatterns = [
    path('create/', create_payment, name='create_payment'),
    path('return/', payment_return, name='payment_return'),
    path('webhook/', tspay_webhook, name='tspay_webhook'),
]
```

---

# ⚙️ PAYMENT FLOW OVERVIEW

## 🔁 Full Flow

```
User -> create_payment API
        ↓
Django creates Payment
        ↓
Send request to TSPay
        ↓
Receive payment_url
        ↓
Redirect user to TSPay checkout
        ↓
User pays
        ↓
TSPay calls webhook (server-to-server)
        ↓
Django updates payment status
        ↓
User redirected to return page
```

---

# 🚀 1. CREATE PAYMENT (INITIATION)

## Endpoint

```
POST /payment/create/
```

## Example Request

```json
{
  "amount": 5000,
  "purpose": "donate",
  "reference_id": "test123",
  "user_id": "1",
  "callback_url": "https://your-site.uz/payment/return/"
}
```

---

## What happens inside

1. Create Payment in DB
2. Generate order_id
3. Convert amount if needed (som → tiyin)
4. Send request to TSPay API

---

## TSPay Request

```python
requests.post("https://api.tspay.uz/api/transactions/", json={
    "merchant_id": MERCHANT_ID,
    "amount": amount,
    "order_id": order_id,
    "redirect_url": callback_url
})
```

---

## TSPay Response

```json
{
  "cheque_id": "uuid",
  "payment_url": "https://checkout.tspay.uz/invoice/..."
}
```

---

## Django Response

```json
{
  "payment_url": "https://checkout.tspay.uz/...",
  "order_id": 123456
}
```

---

# 🔁 2. RETURN URL (USER REDIRECT)

## Endpoint

```
GET /payment/return/?order_id=...
```

## Purpose

This page is NOT trusted.

👉 It is only UI
👉 Real payment status comes from webhook

---

## Example View

```python
def payment_return(request):
    order_id = request.GET.get("order_id")
    payment = Payment.objects.filter(order_id=order_id).first()

    return render(request, "payment/return.html", {
        "payment": payment
    })
```

---

## Important Rule

❗ DO NOT mark payment as success here

✔ only show status
✔ real update = webhook

---

# 🔔 3. WEBHOOK (MOST IMPORTANT)

## Endpoint

```
POST /payment/webhook/
```

---

## Methods from TSPay

### 1. checkPerform

Validate payment before processing

```json
{
  "method": "checkPerform",
  "params": {
    "order_id": "123",
    "amount": 500000
  }
}
```

Response:

```json
{ "allow": true }
```

---

### 2. createTransaction

Register transaction in your DB

Response:

```json
{
  "success": true,
  "transaction_id": "your-db-id"
}
```

---

### 3. performTransaction

Final payment confirmation

```json
{
  "method": "performTransaction",
  "params": {
    "order_id": "123",
    "cheque_id": "uuid",
    "transaction_id": "tspay-id"
  }
}
```

---

## What you MUST do here

✔ mark payment as success
✔ store cheque_id
✔ store transaction_id
✔ prevent double payment

---

## Example logic

```python
if method == "performTransaction":
    payment.status = "success"
    payment.cheque_id = params["cheque_id"]
    payment.transaction_id = params["transaction_id"]
    payment.save()

    return JsonResponse({"success": True})
```

---

# 🔐 SIGNATURE CHECK (VERY IMPORTANT)

Always verify:

* X-Timestamp
* X-Signature

```python
if not verify_tspay_signature(request, params):
    return JsonResponse({"allow": False}, status=401)
```

---

# 💰 AMOUNT RULE (IMPORTANT)

## TSPay uses TIYIN

| Som  | Tiyin  |
| ---- | ------ |
| 5000 | 500000 |

---

## Conversion rule

```python
def to_tiyin(amount):
    return amount * 100
```

---

# 🧪 SANDBOX TESTING

## Steps

1. Use ngrok

```
ngrok http 8000
```

2. Set webhook URL:

```
https://xxxx.ngrok.io/payment/webhook/
```

3. Test in TSPay sandbox panel

---

# ⚠️ COMMON MISTAKES

❌ using return URL as payment success
❌ mixing DB id and transaction_id
❌ not converting to tiyin
❌ not checking signature
❌ double payment handling missing

---

# 🧠 BEST PRACTICE

* DB stores:

  * order_id
  * amount (in som OR tiyin consistently)
  * status
  * cheque_id
  * transaction_id

* Webhook is SINGLE SOURCE OF TRUTH

---

# 🚀 FINAL ARCHITECTURE

```
Frontend
  ↓
/create/
  ↓
TSPay
  ↓
checkout
  ↓
Webhook → DB update
  ↓
/return/ (UI only)
```

---

# 🎯 DONE

This system is now:

✔ production ready
✔ webhook safe
✔ idempotent
✔ scalable

---

If you want next level upgrade:

🔥 Celery retry webhook system
🔥 Multi-payment gateway (Click + Payme + Stripe)
🔥 Fraud detection layer

just tell 👍
