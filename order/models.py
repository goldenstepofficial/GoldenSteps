from django.db import models
from users.models import User
from store.models import Product,Variation
import uuid
import random
from datetime import datetime, timedelta

from store.models import Cart


# class Payment(models.Model):
#     user              = models.ForeignKey(User,on_delete=models.CASCADE)
#     payment_id        = models.CharField(max_length=128)
#     payment_method    = models.CharField(max_length=128)
#     ammount_paid      = models.CharField(max_length=128)
#     status            = models.CharField(max_length=128)
#     created_at        = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return self.payment_id

class Order(models.Model):
    
    STATUS = (
        ('New','New'),
        ('Accepted','Accepted'),
        ('Completed','Completed'),
        ('Cancelled','Cancelled'),
        ('Conflict','Conflict'),
    )
    
    user            = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="orders", null=True, blank=True)
    payment         = models.JSONField(default=dict,blank=True)
    cart            = models.ForeignKey(Cart, on_delete=models.SET_NULL,null=True,blank=True)
    order_id        = models.UUIDField(default=uuid.uuid1)
    customer_id     = models.UUIDField(default=uuid.uuid4)
    cf_order_id     = models.CharField(max_length=40, null=True, blank=True)
    first_name      = models.CharField(max_length=64)
    last_name       = models.CharField(max_length=64)
    phone_number    = models.CharField(max_length=16)
    email           = models.CharField(max_length=64)
    address_line_1  = models.CharField(max_length=64)
    address_line_2  = models.CharField(max_length=64,blank=True)
    country         = models.CharField(max_length=64)
    state           = models.CharField(max_length=32)
    city            = models.CharField(max_length=32)
    pincode         = models.CharField(max_length=8)
    order_note      = models.CharField(max_length=128,blank=True)
    order_total     = models.FloatField()
    tax             = models.FloatField(default=18)
    status          = models.CharField(max_length=16,choices=STATUS,default='New')
    ip              = models.CharField(max_length=32,blank=True, null=True)
    is_paid         = models.BooleanField(default=False)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.order_id)



class OrderItems(models.Model):
    order           = models.ForeignKey(Order, on_delete=models.CASCADE)
    user            = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    product         = models.ForeignKey(Product, on_delete=models.CASCADE)
    variation       = models.ManyToManyField(Variation, blank=True)
    quantity        = models.IntegerField()
    ordered         = models.BooleanField(default=False)
    product_price   = models.IntegerField()
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.product.name



def get_coupon_code():
    code_chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    code = ''
    for i in range(0, 6):
        slice_start = random.randint(0, len(code_chars) - 1)
        code += code_chars[slice_start: slice_start + 1]
    return code


def default_validity():
    return datetime.now() + timedelta(days=365)


class Coupon(models.Model):
    coupon_code           = models.CharField(max_length=20,default=get_coupon_code)
    discount_rate         = models.IntegerField()
    valid_till            = models.DateTimeField(blank=True, null=True,default=default_validity)
    max_redeem_count      = models.IntegerField(default=100)
    redeemed_by           = models.JSONField(default=dict,blank=True)
    created_at            = models.DateTimeField(auto_now_add=True)

    def is_valid(self,user):
        user_redeem_count = self.redeemed_by.get(str(user.id))
        if user_redeem_count is not None and user_redeem_count['count'] > self.max_redeem_count:
            return False
            
        return self.valid_till.timestamp() > datetime.now().timestamp()
        

    def redeem(self,user,price):
        if self.is_valid(user):
            if self.redeemed_by.get(str(user.id)) is None:
                self.redeemed_by[str(user.id)] = {"count":0}
            self.redeemed_by[str(user.id)]['count'] += 1
            self.save()
            if self.is_discount_in_rate and self.discount <= 50:
                discount = (price * self.discount) / 100
            else:
                discount = self.discount
            return float('{0:.2f}'.format(discount))
        return 0