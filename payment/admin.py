from django.contrib import admin
from .models import Payment , PaymentLog

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('amount', 'status', 'created_at')

@admin.register(PaymentLog)
class PaymentLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'payment', 'type', 'created_at')