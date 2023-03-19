from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated,AllowAny
from rest_framework import status
from rest_framework.response import Response
from django.shortcuts import HttpResponse

import requests
from datetime import datetime,timedelta
import pytz
import string
import random
import os
from dotenv import load_dotenv
import json

from .serializers import OrderSerializer, OrderItemsSerializer
from store.models import Cart, CartItem, Product, Variation
from .models import Order,OrderItems

load_dotenv()


@api_view(['POST'])
# @permission_classes([IsAuthenticated])
def create_order(request,*args,**kwargs):
    """
        if request data contains cart_id then create order for all items in cart
        else create order for product_id received in request additionally add variations
    """

    def create_order_object(order_data):
        order_data['order_total'] = round(order_data['order_total'],2)
        serializer = OrderSerializer(data=order_data)
        if not serializer.is_valid(raise_exception=True):
            return Response(serializer.errors)
        return serializer.save()

    
    cart_id = request.data.get('cart_id')
    product_id = request.data.get('product_id')

    if cart_id is None and product_id is None:
        return Response({"error": "either 'cart_id' or 'product_id' is required"},status=status.HTTP_400_BAD_REQUEST)

    data = request.data.copy()
    data['ip'] = request.META.get('REMOTE_ADDR')
    # create order for all cart items
    if cart_id:
        try:
            cart = Cart.objects.get(id=cart_id)
        except:
            return Response({"error": "Invalid cart_id"},status=status.HTTP_400_BAD_REQUEST)

        cart_items = CartItem.objects.filter(cart=cart)
        if cart_items.count() == 0:
            return Response({"error": "your cart is empty. try again after adding some items to your cart"},status=status.HTTP_400_BAD_REQUEST)

        total_price = 0
        for item in cart_items:
            total_price += item.product.price * item.quantity
            
        data['order_total'] = total_price + (total_price * 18)//100
        data['cart'] = cart_id
        data['user'] = request.user.id if request.user.is_authenticated else None
        order = create_order_object(data)

    else:
        try:
            product = Product.objects.get(id=product_id)
        except:
            return Response({"error": "Invalid 'product_id"},status=status.HTTP_400_BAD_REQUEST)

        quantity = request.data.get('quantity')
        if quantity is None:
            return Response({"error": "'quantity' is required"},status=status.HTTP_400_BAD_REQUEST)
        
        total_price = product.price * int(quantity)
        data['order_total'] = total_price + (total_price * 18)//100

        variation_list = []

        variations = request.data.get('variations')
        if variations is not None and len(variations) > 0:
            try:
                variations = json.loads(variations)
            except:
                return Response({"error": "Invalid variation format. please send in json format only"},status=status.HTTP_400_BAD_REQUEST)
            for key in variations:
                value = variations[key]
                try:
                    var = Variation.objects.get(product=product_id,variation_key__iexact=key,variation_value__iexact=value)
                    variation_list.append(var)
                except Exception as e:
                    pass

        data['user'] = request.user.id if request.user.is_authenticated else None
        order = create_order_object(data)
        user = request.user if request.user.is_authenticated else None
        order_item = OrderItems.objects.create(order=order,product=product,quantity=quantity,product_price=order.order_total,user=user)
        order_item.variation.set(variation_list)
        order_item.save()
    

    try:
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

        if response.ok:
            resp_data = response.json()
            order.cf_order_id = resp_data.get('cf_order_id')
            order.save()
            return Response(resp_data)
        else:
            return Response({"error": "failed to create order","description":response},status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"errro":"something went wrong. please try again"},status=status.HTTP_503_SERVICE_UNAVAILABLE)




@api_view(['POST','GET'])
def notify_on_payment(request):
    
    def get_order_status(order_id):
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

    order_id = request.GET.get('order_id')
    if order_id is None:
        return Response({"error": "Order_id is required"},status=status.HTTP_400_BAD_REQUEST)
    
    response = get_order_status(order_id).json()

    # if cashfree returns order status as paid then update record accordingly
    if response.get("order_status") == "PAID":
        try:
            order = Order.objects.get(order_id=order_id)
            order.is_paid = True
            order.payment = response
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
        return HttpResponse("<h1>Payment Done</h1>")
        # return Response(response.json())
    else:
        return HttpResponse("<h1>Payment Failed</h1>")
        # return Response(response.json())