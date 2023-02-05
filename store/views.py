from django.shortcuts import render
from rest_framework import status, viewsets
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.mixins import RetrieveModelMixin,CreateModelMixin,DestroyModelMixin

from .models import Category, Product, ReviewRating, SubCategory,Cart,CartItem
from .serializers import (  CategorySerializer, ProductSerializer,
                            SubCategorySerializer,CartSerializer,
                            CartItemSerializer,AddCartItemSerializer,UpdateCartItemSerializer
                            )


class ProductModelViewSet(viewsets.ReadOnlyModelViewSet):
    queryset           = Product.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly,]
    serializer_class   = ProductSerializer


class CategoryModelViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    permission_classes = [AllowAny]
    serializer_class = CategorySerializer


class SubCategoryModelViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SubCategory.objects.all()
    permission_classes = [AllowAny]
    serializer_class = SubCategorySerializer



class CartModelViewSet(viewsets.GenericViewSet,RetrieveModelMixin,CreateModelMixin,DestroyModelMixin):
    queryset = Cart.objects.prefetch_related('items__product').all()
    permission_classes = [AllowAny]
    serializer_class = CartSerializer



class CartItemModelViewSet(viewsets.ModelViewSet):
    http_method_names = ['get','post','patch','delete']

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AddCartItemSerializer
        elif self.request.method == "PATCH":
            return UpdateCartItemSerializer
        return CartItemSerializer


    def get_serializer_context(self):
        return {'cart_id':self.kwargs['cart_pk'],'request':self.request}

    def get_queryset(self):
        return CartItem.objects \
                .filter(cart_id=self.kwargs['cart_pk']) \
                    .select_related('product')