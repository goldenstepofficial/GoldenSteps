from django.urls import path
from rest_framework import routers

from .views import ProductModelViewSet,CategoryModelViewSet,SubCategoryModelViewSet

router = routers.DefaultRouter()
router.register(r'products', ProductModelViewSet)
router.register(r'categories', CategoryModelViewSet)
router.register(r'sub_categories', SubCategoryModelViewSet)

urlpatterns = router.urls