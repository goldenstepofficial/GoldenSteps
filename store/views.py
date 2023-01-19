from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import AllowAny,IsAuthenticated,IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework import status

from .models import Product,Category,SubCategory,ReviewRating
from .serializers import ProductSerializer,CategorySerializer,SubCategorySerializer


class ProductModelViewSet(viewsets.ModelViewSet):
    queryset           = Product.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly,]
    serializer_class   = ProductSerializer

    def create(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return Response("method \POST\ not allowed",status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return super().create(request, *args, **kwargs)


class CategoryModelViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    permission_classes = [AllowAny]
    serializer_class = CategorySerializer


class SubCategoryModelViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SubCategory.objects.all()
    permission_classes = [AllowAny]
    serializer_class = SubCategorySerializer