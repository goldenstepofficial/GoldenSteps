from django.urls import path
# from rest_framework import routers
from rest_framework_nested import routers

from . import views

router = routers.DefaultRouter()
router.register(r'products', views.ProductModelViewSet)
router.register(r'categories', views.CategoryModelViewSet)
router.register(r'sub_categories', views.SubCategoryModelViewSet)
router.register(r'carts', views.CartModelViewSet,basename='carts')

cart_router = routers.NestedDefaultRouter(router,"carts",lookup="cart")
cart_router.register('items', views.CartItemModelViewSet,basename="cart-items")

urlpatterns = [
            path('assign_cart/<str:cart_id>/',views.assign_cart,name="assign_cart"),
        ]

urlpatterns += router.urls + cart_router.urls