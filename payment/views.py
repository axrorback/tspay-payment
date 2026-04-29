from django.shortcuts import render, reverse
import time
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Payment, PaymentLog
from django.conf import settings
from .signature import verify_tspay_signature
import json

TSPAY_URL = "https://api.tspay.uz/api/transactions/"
MERCHANT_ID = settings.MERCHANT_ID

def build_redirect_url(request, order_id):
    path = reverse("payment_return")
    return request.build_absolute_uri(f"{path}?order_id={order_id}")


@csrf_exempt
def create_payment(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        data = json.loads(request.body)
    except:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    amount_som = data.get("amount")
    purpose = data.get("purpose")
    reference_id = data.get("reference_id")
    user_id = data.get("user_id")
    callback_url = data.get("callback_url")

    order_id = int(time.time() * 1000)

    payment = Payment.objects.create(
        amount=amount_som,
        purpose=purpose,
        reference_id=reference_id,
        user_id=user_id,
        order_id=order_id,
        callback_url=callback_url
    )

    redirect_url = build_redirect_url(request, order_id)

    res = requests.post(TSPAY_URL, json={
        "merchant_id": MERCHANT_ID,
        "amount": amount_som,
        "order_id": order_id,
        "redirect_url": redirect_url
    })

    if res.status_code == 200:
        resp = res.json()

        payment.cheque_id = resp.get("cheque_id")
        payment.save()

        return JsonResponse({
            "payment_url": resp.get("payment_url"),
            "order_id": order_id
        })

    return JsonResponse(res.json(), status=400)


def payment_return(request):
    order_id = request.GET.get("order_id")
    payment = Payment.objects.filter(order_id=order_id).first()

    return render(request, "payment/return.html", {
        "payment": payment
    })


@csrf_exempt
def tspay_webhook(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    params = body.get("params", {})
    method = body.get("method")

    order_id = params.get("order_id")
    req_amount = int(params.get("amount", 0))

    payment = Payment.objects.filter(order_id=order_id).first()

    if not verify_tspay_signature(request, params):
        return JsonResponse({
            "allow": False,
            "reason": "Invalid signature"
        }, status=401)

    PaymentLog.objects.create(
        payment=payment if payment else None,
        type="webhook",
        data=body
    )

    if method == "checkPerform":
        if not payment:
            return JsonResponse({"allow": False, "reason": "Not found"})

        if payment.amount != req_amount:
            return JsonResponse({"allow": False, "reason": "Amount mismatch"})

        return JsonResponse({"allow": True})

    if method == "createTransaction":
        if not payment:
            return JsonResponse({"success": False})

        return JsonResponse({
            "success": True,
            "transaction_id": str(payment.id)
        })

    if method == "performTransaction":
        if not payment:
            return JsonResponse({"success": False, "reason": "Not found"})

        if payment.status == "success":
            return JsonResponse({"success": True, "message": "Already processed"})

        payment.status = "success"
        payment.cheque_id = params.get("cheque_id")
        payment.transaction_id = params.get("transaction_id")
        payment.save()

        PaymentLog.objects.create(
            payment=payment,
            type="performTransaction",
            data=body
        )

        # if payment.callback_url:
        #     try:
        #         requests.post(payment.callback_url, json={
        #             "status": "success",
        #             "order_id": payment.order_id,
        #             "amount": payment.amount,
        #             "transaction_id": payment.transaction_id,
        #             "user_id": payment.user_id,
        #         }, timeout=5)
        #     except Exception as e:
        #         print("Callback error:", e)
        #
        # return JsonResponse({"success": True})

    return JsonResponse({"error": "Unknown method"}, status=400)