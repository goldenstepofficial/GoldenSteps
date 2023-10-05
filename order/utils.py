import json
import base64
import os
import pytz
import requests
from . import phonepe as phonepe_api

from datetime import datetime, timedelta
from dotenv import load_dotenv

from .serializers import OrderSerializer, OrderItemsSerializer
from store.models import Cart, CartItem, Product, Variation
from .models import Order,OrderItems

load_dotenv()



################### standard modules start ##################

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

################## standard modules end ##################


################## Order related modules start ##################

def process_order_on_payment_complete(order_id, payment_response):
    try:
        order = Order.objects.get(order_id=order_id)
        order.is_paid = True
        order.payment = payment_response
        order.save()

        # move items from cart to orderItems
        if order.cart is not None:
            cart_items = CartItem.objects.filter(cart=order.cart)
            for cart_item in cart_items:
                order_item = OrderItems.objects.create(  
                                            order=order,product=cart_item.product,
                                            quantity=cart_item.quantity,
                                            product_price=cart_item.product.price,
                                            ordered=True
                                            )
                order_item.variation.set(cart_item.variation.all())
                order_item.save()
            cart_items.delete()

        else:
            order_items = OrderItems.objects.filter(order=order)
            for order_item in order_items:
                order_item.ordered = True
                order_item.save()

    except:
        pass







################## Order related modules end ##################


################## Phonepe related modules start ##################

def initialize_phonepe():
    env = 'UAT' 
    phonepe_api.set_environment(env)

    phonepe_api.MERCHANT_ID = os.getenv('PHONEPE_MERCHANT_ID')
    phonepe_api.STORE_ID = os.getenv('PHONEPE_STORE_ID')
    phonepe_api.TERMINAL_ID = os.getenv('PHONEPE_TERMINAL_ID')

    api_keys = {
        '1': os.getenv('PHONEPE_API_KEY')
    }
    phonepe_api.API_KEYS.update(api_keys)


def initiate_payment_phonepe(order):
    initialize_phonepe()
    salt_key_index    = '1'
    amount            = order.order_total
    transaction_id    = str(order.order_id)
    user_id           = str(order.customer_id)
    user_phone_number = str(order.phone_number)
    
    response = phonepe_api.make_charge_request(amount, transaction_id, user_phone_number, salt_key_index)
    response_content = json.loads(response.content)
    
    if response_content['success'] is True:
        data = {}
        data['payment_url'] = response_content['data']['instrumentResponse']['redirectInfo']['url']
        data['transaction_id'] = response_content['data']['merchantTransactionId']
        data['message'] = response_content['message']
        data['success'] = response_content['success']
        return True, data
    return False, response_content


def get_payment_status_phonepe(transaction_id):
    initialize_phonepe()
    salt_key_index    = '1'
    response = phonepe_api.make_status_request(transaction_id, salt_key_index)
    return json.loads(response.content)

#response = phonepe_api.make_cancel_request(new_transaction_id,salt_key_index)
#response = phonepe_api.make_refund_request(new_transaction_id, providerReferenceId, salt_key_index)
#response = phonepe_api.make_status_request(new_transaction_id, salt_key_index)

################## Phonepe related modules end ##################



############## Cashfree related modules start ##############
def initiate_payment_cashfree(order):
    time_zone = pytz.timezone('Asia/Kolkata')
    exp_time = datetime.now(time_zone) + timedelta(minutes=20)
    exp_time = exp_time.strftime('%Y-%m-%dT%H:%M:%S%z')
    exp_time = exp_time[:-2] + ":" + exp_time[-2:]


    payload = {
        "order_id": str(order.order_id),
        "order_amount": order.order_total,
        "order_currency": "INR",
        "customer_details": {
            "customer_id": str(order.customer_id),
            "customer_name": order.first_name + " " + order.last_name,
            "customer_email": order.email,
            "customer_phone": order.phone_number,
        },
        "order_meta": {
            "return_url": "http://localhost:8000/order/notify_on_payment/?order_id={order_id}",
        },
        "order_expiry_time": exp_time,
        "order_note": "Test order",
        "order_tags": {"additionalProp": "string"},
    }
    headers = {
        "accept": "application/json",
        "x-client-id": os.getenv("CLIENT_ID"),
        "x-client-secret": os.getenv("CLIENT_SECRET"),
        "x-api-version": "2022-09-01",
        "content-type": "application/json"
    }

    url = "https://sandbox.cashfree.com/pg/orders"
    response = requests.post(url, json=payload, headers=headers)
    return response



def get_cashfree_order_status(order_id):
    url = f"https://sandbox.cashfree.com/pg/orders/{order_id}"
    headers = {
        "accept": "application/json",
        "x-client-id": os.getenv("CLIENT_ID"),
        "x-client-secret": os.getenv("CLIENT_SECRET"),
        "x-api-version": "2022-09-01",
        "content-type": "application/json"
    }
    response = requests.get(url, headers=headers)
    return response

############## Cashfree related modules start ##############