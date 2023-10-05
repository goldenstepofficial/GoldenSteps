import requests
from datetime import datetime,timedelta
import pytz
import string
import random
import os
import json
import base64
import time

from django.shortcuts import render,HttpResponseRedirect
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated,AllowAny
from rest_framework import status
from rest_framework.response import Response
from dotenv import load_dotenv
from django.shortcuts import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from .utils import (initiate_payment_cashfree,
                    initiate_payment_phonepe, 
                    get_payment_status_phonepe,
                    process_order_on_payment_complete, 
                    get_cashfree_order_status)
from .serializers import OrderSerializer, OrderItemsSerializer
from store.models import Cart, CartItem, Product, Variation
from .models import Order, OrderItems, Coupon

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
    
    coupon_code = request.data.get('coupon_code')
    discount_rate = 0
    if coupon_code is not None:
        try:
            coupon = Coupon.objects.get(coupon_code=coupon_code)
        except:
            return Response({"coupon_code":"invalid coupon code"},status=status.HTTP_400_BAD_REQUEST)

        if not coupon.is_valid(request.user):
            return Response({"coupon_code is expired or already redeemed by you"},status=status.HTTP_400_BAD_REQUEST)

        discount_rate = coupon.discount_rate



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
            
        data['order_total'] = total_price - ( (total_price * discount_rate)//100 )
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
        data['order_total'] = total_price - ( (total_price * discount_rate)//100 )

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
        payment_platform = os.getenv('PAYMENT_PLATFORM')
        if payment_platform == 'cashfree':
            """ logic for initiating payment for order on cashfree """""
            response = initiate_payment_cashfree(order)

            if response.ok:
                resp_data = response.json()
                order.cf_order_id = resp_data.get('cf_order_id')
                order.save()
                return Response(resp_data)
            else:
                print(response.json())
                return Response({"error": "failed to create order","description":response},status=status.HTTP_400_BAD_REQUEST)

        elif payment_platform == 'phonepe':
            """ logic for initiating payment for  order on phonepe """""
            status, data = initiate_payment_phonepe(order)

            if status:
                return Response(data)
            else:
                return Response({"error": "failed to create order","description":data},status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"errro":"something went wrong. please try again"},status=status.HTTP_503_SERVICE_UNAVAILABLE)




@api_view(['POST'])
def notify_on_payment(request):
    payment_platform = os.getenv('PAYMENT_PLATFORM')
    if payment_platform == 'cashfree':
        """ logic for handling payment notification from cashfree """""

        order_id = request.GET.get('order_id')
        if order_id is None:
            return Response({"error": "Order_id is required"},status=status.HTTP_400_BAD_REQUEST)
        
        response = get_cashfree_order_status(order_id).json()
        retry_count = 0
        delay = 1
        
        while retry_count < 5 and response.get("order_status") != "PAID":
            response = get_cashfree_order_status(order_id).json()
            retry_count += 1
            time.sleep(delay)
            delay *= 2

        # if cashfree returns order status as paid then update record accordingly
        if response.get("order_status") == "PAID":
            process_order_on_payment_complete(order_id,response)
            return HttpResponseRedirect('https://goldenstep.in/payment-success')
        else:
            return HttpResponseRedirect('https://goldenstep.in/payment-failed')
            # return Response(response.json())

    elif payment_platform == 'phonepe':
        """ logic for handling payment notification from phonepe"""""
        encoded_response = request.data['response']
        decoded_string = base64.b64decode(encoded_response)
        phonepe_response = json.loads(decoded_string)
        
        print(phonepe_response)
        # if phonepe returns order status as paid then update record accordingly
        if phonepe_response.get("code") == "PAYMENT_SUCCESS":
            order_id = phonepe_response['data'].get('merchantTransactionId')
            response = get_payment_status_phonepe(order_id)
            retry_count = 0
            delay = 1
            while retry_count < 5 and response.get("code") != "PAYMENT_SUCCESS":
                response = get_payment_status_phonepe(order_id)
                retry_count += 1
                time.sleep(delay)
                delay *= 2
                
            if response.get("code") == "PAYMENT_SUCCESS":
                phonepe_response['data']['amount'] = round(phonepe_response['data']['amount']/100,2)
                process_order_on_payment_complete(order_id,phonepe_response)
                return HttpResponseRedirect('https://goldenstep.in/payment-success')
            return HttpResponseRedirect('https://goldenstep.in/payment-failed')
        else:
            return HttpResponseRedirect('https://goldenstep.in/payment-failed')
            # return Response(response.json())
    else:
        return Response({"error": "invalid payment method"},status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET'])
def get_payment_status(request):
    order_id = request.data.get('order_id')
    if order_id is None:
        return Response({"error": "order_id is required"},status=status.HTTP_400_BAD_REQUEST)

    payment_platform = os.getenv('PAYMENT_PLATFORM')
    if payment_platform == 'cashfree':
        """ logic for getting order status from cashfree """""
        response = get_cashfree_order_status(order_id)
        return Response(response.json())

    elif payment_platform == 'phonepe':
        """ logic for getting order status from phonepe """""
        response = get_payment_status_phonepe(order_id)
        response['data']['amount'] = round(response['data']['amount']/100,2)
        return Response(response)

    else:
        return Response({"error": "invalid payment method"},status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_order_status(request):
    order_id = request.data.get('order_id')
    if order_id is None:
        return Response({"error": "order_id is required"},status=status.HTTP_400_BAD_REQUEST)

    try:
        order = Order.objects.get(order_id=order_id)
    except:
        return Response({"error": "invalid order_id"},status=status.HTTP_400_BAD_REQUEST)

    serializer = OrderSerializer(order)

    return Response({"order_status": serializer.data})




@csrf_exempt
@api_view(['POST'])
# @permission_classes([IsAuthenticated])
def validate_coupon(request):
    coupon_code = request.data.get('coupon_code')
    if coupon_code is None:
        return Response({"coupon_code":"this field is required"},status=status.HTTP_400_BAD_REQUEST)

    try:
        coupon = Coupon.objects.get(coupon_code=coupon_code)
    except:
        return Response({"coupon_code":"invalid coupon code"},status=status.HTTP_400_BAD_REQUEST)

        
    if not coupon.is_valid(request.user):
        return Response({"coupon_code is expired or already redeemed by you"},status=status.HTTP_400_BAD_REQUEST)
    resp = {}
    resp["discount_rate"] = coupon.discount_rate
    return Response(resp)

    return Response({"coupon_code":"invalid coupon code"},status=status.HTTP_400_BAD_REQUEST)
