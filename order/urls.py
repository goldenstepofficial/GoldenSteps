from django.urls import path
from .views import create_order, notify_on_payment, get_payment_status, get_order_status, validate_coupon



urlpatterns = [
    path('order/',create_order),
    path('order/notify_on_payment/',notify_on_payment),

    path('order/payment_status/',get_payment_status),
    path('order/order_status/',get_order_status),
    path('order/validate_coupon/', validate_coupon)

]
