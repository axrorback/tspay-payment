from django.test import TestCase, Client
from django.urls import reverse
from .models import Payment, PaymentLog
import json
from unittest.mock import patch
import hmac
import hashlib

class PaymentTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.webhook_secret = "test_secret"
        with self.settings(TSPAY_WEBHOOK_SECRET=self.webhook_secret, MERCHANT_ID="test_merchant"):
            pass

    @patch('requests.post')
    def test_create_payment_success(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "cheque_id": "test_cheque",
            "payment_url": "https://checkout.tspay.uz/invoice/test"
        }

        data = {
            "amount": 5000,
            "purpose": "test donation",
            "reference_id": "ref123",
            "user_id": "user1",
            "callback_url": "https://mysite.com/callback"
        }

        with self.settings(TSPAY_WEBHOOK_SECRET="test_secret", MERCHANT_ID="test_merchant"):
            # Re-import MERCHANT_ID in views if it's cached, but usually settings override works if accessed via settings.MERCHANT_ID
            # However, the view does MERCHANT_ID = getattr(settings, 'MERCHANT_ID', None) at module level.
            # We need to mock it in the view.
            with patch('payment.views.MERCHANT_ID', 'test_merchant'):
                response = self.client.post(
                    reverse('create_payment'),
                    data=json.dumps(data),
                    content_type='application/json'
                )

        self.assertEqual(response.status_code, 200)
        self.assertIn('payment_url', response.json())
        self.assertTrue(Payment.objects.filter(reference_id="ref123").exists())

    def test_create_payment_invalid_data(self):
        data = {
            "amount": -100, # Invalid amount
            "purpose": "test"
        }
        response = self.client.post(
            reverse('create_payment'),
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_webhook_check_perform_success(self):
        payment = Payment.objects.create(
            amount=5000,
            order_id=12345,
            purpose="test",
            reference_id="ref123"
        )

        timestamp = "1700000000"
        params = {"order_id": "12345", "amount": "5000"}
        message = f"12345:5000:{timestamp}"
        signature = "sha256=" + hmac.new(
            self.webhook_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        webhook_data = {
            "method": "checkPerform",
            "params": params
        }

        with self.settings(TSPAY_WEBHOOK_SECRET=self.webhook_secret):
            response = self.client.post(
                reverse('tspay_webhook'),
                data=json.dumps(webhook_data),
                content_type='application/json',
                HTTP_X_SIGNATURE=signature,
                HTTP_X_TIMESTAMP=timestamp
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"allow": True})

    def test_webhook_invalid_signature(self):
        webhook_data = {
            "method": "checkPerform",
            "params": {"order_id": "12345", "amount": "5000"}
        }

        response = self.client.post(
            reverse('tspay_webhook'),
            data=json.dumps(webhook_data),
            content_type='application/json',
            HTTP_X_SIGNATURE="invalid",
            HTTP_X_TIMESTAMP="123"
        )

        self.assertEqual(response.status_code, 401)
