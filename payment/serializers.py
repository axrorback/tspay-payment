from rest_framework import serializers
from .models import Payment

class PaymentCreateSerializer(serializers.Serializer):
    amount = serializers.IntegerField(min_value=1)
    purpose = serializers.CharField(max_length=50)
    reference_id = serializers.CharField(max_length=100)
    user_id = serializers.CharField(max_length=100, required=False, allow_null=True)
    callback_url = serializers.URLField(required=False, allow_null=True)
