from django.urls import path
from .views import create_order,notify_on_payment


urlpatterns = [
    path('order/',create_order),
    path('order/notify_on_payment/',notify_on_payment),
]
