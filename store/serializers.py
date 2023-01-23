from rest_framework import serializers

from .models import Product,Category,SubCategory,Cart,CartItem



class ProductSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Product
        fields = ('id','category','sub_category','name','image','variations','details','price','stock','is_available')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['image'] = self.context['view'].request.build_absolute_uri(instance.image.url)
        return representation



class SubCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = SubCategory
        fields = ('name','image','desc')

    def to_representation(self, instance):
        representation =  super().to_representation(instance)
        representation['image'] = self.context['view'].request.build_absolute_uri(instance.image.url)
        return representation



class CategorySerializer(serializers.ModelSerializer):
    sub_categories = SubCategorySerializer(many=True,read_only=True)
    products_count = serializers.SerializerMethodField

    class Meta:
        model = Category
        fields = ('name','image','desc','sub_categories')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['image'] = self.context['view'].request.build_absolute_uri(instance.image.url)
        return representation


class SimpleProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ('id','name','price','image','is_available')


class CartItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer()
    sub_total_price = serializers.SerializerMethodField()

    def get_sub_total_price(self,cart_item):
        return cart_item.product.price * cart_item.quantity

    class Meta:
        model = CartItem
        fields = ('id','product','quantity','sub_total_price')


class CartSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    items = CartItemSerializer(many=True,read_only=True)
    total_price = serializers.SerializerMethodField()

    def get_total_price(self,cart):
        return sum([ item.product.price * item.quantity for item in cart.items.all()])

    class Meta:
        model = Cart
        fields = ['id','items','total_price']



class AddCartItemSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField()

    def validate_product_id(self,value):
        if not Product.objects.filter(pk=value).exists():
            raise serializers.ValidationError('No product found for given id')
        return value


    def save(self,**kwargs):
        cart_id = self.context['cart_id']
        product_id = self.validated_data['product_id']
        quantity = self.validated_data['quantity']

        try:
            cart_item = CartItem.objects.get(cart_id=cart_id,product_id=product_id)
            cart_item.quantity += quantity
            cart_item.save()
            self.instance = cart_item
        except CartItem.DoesNotExist:
            self.instance = CartItem.objects.create(cart_id=cart_id,**self.validated_data)

        return self.instance

    class Meta:
        model = CartItem
        fields = ['id','product_id','quantity']



class UpdateCartItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = CartItem
        fields = ['quantity']