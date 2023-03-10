from django.db import models
from users.models import User
from store.models import Product,Variation
import uuid

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
    product_price   = models.IntegerField()
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.product.name