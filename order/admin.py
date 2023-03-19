from django.contrib import admin
from .models import Order,OrderItems

class OrderItemInline(admin.TabularInline):
    model = OrderItems
    extra = 1

class OrderAdmin(admin.ModelAdmin):
    model = Order
    list_display = ('order_id','user','first_name','email','order_total','status','is_paid','created_at')
    inlines = (OrderItemInline,)


class OrderItemAdmin(admin.ModelAdmin):
    model = OrderItems
    list_display = ('order','user','product','quantity','product_price','ordered','created_at')

admin.site.register(Order,OrderAdmin)
admin.site.register(OrderItems,OrderItemAdmin)