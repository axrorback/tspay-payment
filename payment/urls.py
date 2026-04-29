from django.urls import path

from .views import create_payment, payment_return, tspay_webhook

urlpatterns = [
    path('create/', create_payment, name='create_payment'),
    path('return/', payment_return, name='payment_return'),
    path('webhook/', tspay_webhook, name='tspay_webhook'),
]