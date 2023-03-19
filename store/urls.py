from django.urls import path
# from rest_framework import routers
from rest_framework_nested import routers

from . import views

router = routers.DefaultRouter()
router.register(r'products', views.ProductModelViewSet)
router.register(r'categories', views.CategoryModelViewSet)
router.register(r'sub_categories', views.SubCategoryModelViewSet)
router.register(r'carts', views.CartModelViewSet,basename='carts')
router.register(r'wishlist', views.WishListModelViewSet,basename='wishlist')

cart_router = routers.NestedDefaultRouter(router,"carts",lookup="cart")
cart_router.register('items', views.CartItemModelViewSet,basename="cart-items")

products_router = routers.NestedDefaultRouter(router,"products",lookup="product")
products_router.register('reviews', views.ProductRevieViewSet,basename="product-reviews")

urlpatterns = [
            path('assign_cart/<str:cart_id>/',views.assign_cart,name="assign_cart"),
        ]

urlpatterns += router.urls + cart_router.urls + products_router.urls