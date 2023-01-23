from django.contrib import admin

from .models import Category,SubCategory,Product,ProductGallery,ReviewRating,Cart,CartItem


admin.site.register(Category)
admin.site.register(SubCategory)
admin.site.register(Product)
admin.site.register(ProductGallery)
admin.site.register(ReviewRating)
admin.site.register(Cart)
admin.site.register(CartItem)