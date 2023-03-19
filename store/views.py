from django.shortcuts import get_object_or_404, render
from rest_framework import status, viewsets
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.mixins import RetrieveModelMixin,CreateModelMixin,DestroyModelMixin

from order.models import OrderItems

from .models import Category, Product, ProductRating, ReviewRating, SubCategory,Cart,CartItem, WishList
from .serializers import (  CategorySerializer, ProductRatingSerializer, ProductSerializer,
                            SubCategorySerializer,CartSerializer,
                            CartItemSerializer,AddCartItemSerializer,UpdateCartItemSerializer,WishListSerializer
                            )
from rest_framework.decorators import api_view, permission_classes
from django_filters.rest_framework import DjangoFilterBackend


class ProductModelViewSet(viewsets.ReadOnlyModelViewSet):
    queryset           = Product.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly,]
    serializer_class   = ProductSerializer
    filter_backends    = [DjangoFilterBackend]
    filterset_fields   = ['category','sub_category','name','price']


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




class ProductRevieViewSet(viewsets.ViewSet):
    queryset            = ProductRating.objects.all()
    permission_classes  = [IsAuthenticatedOrReadOnly]
    http_method_names   = ('get', 'post','delete')

    def retrieve(self, request,pk=None,*args,**kwargs):
        product_id = int(self.kwargs['product_pk'])
        queryset   = self.queryset.filter(product=product_id)
        review     = get_object_or_404(queryset,pk=pk)
        serializer = ProductRatingSerializer(review)
        return Response(serializer.data)


    # @method_decorator(cache_page(60*15))
    def list(self, request,*args,**kwargs):
        product_id = int(self.kwargs['product_pk'])
        queryset   = self.queryset.filter(product=product_id)
        serializer = ProductRatingSerializer(queryset,many=True)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        product_id = int(self.kwargs['product_pk'])

        if self.queryset.filter(product=product_id,buyer=request.user).exists():
            return Response({'error':"you have already rated this Product"},status.HTTP_400_BAD_REQUEST)
        
        order_items = OrderItems.objects.filter(product_id=product_id,ordered=True,user=request.user)

        if not order_items.exists():
            return Response({'error':"you must purchase this Product before rating it"},status.HTTP_400_BAD_REQUEST)

        data = request.data.copy()
        data['product'] = product_id

        serializer = ProductRatingSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(order_item=order_items[0],buyer=request.user)
        return Response({"message":"thank you for rating this Product"})

    def destroy(self,request,pk=None,*args,**kwargs):
        product_id = int(self.kwargs['product_pk'])
        queryset   = self.queryset.filter(product=product_id)
        review = get_object_or_404(queryset,pk=pk,buyer=request.user)
        review.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
