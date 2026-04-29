import hmac
import hashlib
from django.conf import settings

def verify_tspay_signature(request, params):
    secret = getattr(settings, 'TSPAY_WEBHOOK_SECRET', None)
    if not secret:
        return False

    signature = request.headers.get("X-Signature", "")
    timestamp = request.headers.get("X-Timestamp", "")

    if not signature or not timestamp:
        return False

    # TSPay usually expects amount without scientific notation if it's large,
    # and exactly as received. float() might change representation.
    # It's safer to use the raw value if it's already a string or format it strictly.
    amount = params.get('amount')
    message = f"{params.get('order_id')}:{amount}:{timestamp}"

    expected_signature = "sha256=" + hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected_signature)