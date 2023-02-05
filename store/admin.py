from django.contrib import admin

from .models import Category,SubCategory,Product,ProductGallery,ReviewRating,Cart,CartItem,Variation

class VariationInline(admin.TabularInline):
    model = Variation
    extra = 1

class ProductAdmin(admin.ModelAdmin):
    list_display = ['id','name','category','sub_category','price','stock','is_available']
    inlines = (VariationInline,)


class CartItemAdmin(admin.ModelAdmin):
    list_display = ['id','product','quantity']


class VariationAdmin(admin.ModelAdmin):
    list_display = ['id','variation_key','variation_value']

admin.site.register(Category)
admin.site.register(SubCategory)
admin.site.register(Product,ProductAdmin)
admin.site.register(ProductGallery)
admin.site.register(ReviewRating)
admin.site.register(Cart)
admin.site.register(CartItem,CartItemAdmin)
admin.site.register(Variation,VariationAdmin)