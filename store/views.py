from django.shortcuts import render
from rest_framework import status, viewsets
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.mixins import RetrieveModelMixin,CreateModelMixin,DestroyModelMixin

from .models import Category, Product, ReviewRating, SubCategory,Cart,CartItem, WishList
from .serializers import (  CategorySerializer, ProductSerializer,
                            SubCategorySerializer,CartSerializer,
                            CartItemSerializer,AddCartItemSerializer,UpdateCartItemSerializer,WishListSerializer
                            )
from rest_framework.decorators import api_view, permission_classes


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




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def assign_cart(request,cart_id):
    try:
        cart = Cart.objects.get(id=cart_id)
    except:
        return Response({'error': 'invalid cart_id'},status=status.HTTP_400_BAD_REQUEST)

    cart.user = request.user
    cart.save()
    
    return Response('Cart successfully assigned to current user')



class WishListModelViewSet(viewsets.ModelViewSet):
    permission_classes = [ IsAuthenticated ]
    serializer_class = WishListSerializer
    http_method_names = [ 'get','post','delete' ]

    def get_queryset(self):
        return WishList.objects.filter(user=self.request.user)

    def get_serializer_context(self):
        return {'request': self.request}

    def destroy(self, request, *args, **kwargs):
        product_id = request.data.get('product_id')
        if product_id is None:
            return Response({"product_id":"this field is required"},status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(id=product_id)
        except:
            return Response({"product_id":"Invalid product_id"},status=status.HTTP_400_BAD_REQUEST)
        
        instance = self.get_object()
        instance.items.remove(product)
        # self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)