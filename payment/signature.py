import hmac
import hashlib
from django.conf import settings

TSPAY_WEBHOOK_SECRET = settings.TSPAY_WEBHOOK_SECRET

def verify_tspay_signature(request, params):
    secret = TSPAY_WEBHOOK_SECRET

    signature = request.headers.get("X-Signature", "")
    timestamp = request.headers.get("X-Timestamp", "")

    message = f"{params.get('order_id')}:{float(params.get('amount'))}:{timestamp}"

    expected_signature = "sha256=" + hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected_signature)