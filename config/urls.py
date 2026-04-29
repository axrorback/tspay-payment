from django.contrib import admin
from django.urls import path , include
from django.shortcuts import render

urlpatterns = [
    path('admin/', admin.site.urls),
    path('payment/', include('payment.urls')),
]
def custom_404(request, exception):
    return render(request, 'errors/404.html', status=404)

handler404 = 'config.urls.custom_404'