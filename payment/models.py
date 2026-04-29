# models.py
import uuid
from django.db import models

class Payment(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("success", "Success"),
        ("failed", "Failed"),
        ("canceled", "Canceled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    amount = models.PositiveIntegerField()
    currency = models.CharField(max_length=10, default="UZS")
    purpose = models.CharField(max_length=50)
    reference_id = models.CharField(max_length=100)
    user_id = models.CharField(max_length=100, null=True, blank=True)
    order_id = models.BigIntegerField(unique=True)
    cheque_id = models.CharField(max_length=255, null=True, blank=True)
    provider = models.CharField(max_length=20, default="tspay")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    callback_url = models.URLField(null=True, blank=True)
    meta = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    transaction_id = models.CharField(max_length=255, null=True, blank=True)
    def __str__(self):
        return f"{self.order_id} | {self.amount} | {self.status}"



class PaymentLog(models.Model):

    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name="logs",null=True,blank=True)
    type = models.CharField(max_length=50)
    data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.payment} | {self.type} | {self.created_at}"