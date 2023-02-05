from rest_framework import serializers
from collections import defaultdict

from .models import Product,Category,SubCategory,Cart,CartItem,Variation



class ProductSerializer(serializers.ModelSerializer):
    variations = serializers.SerializerMethodField()

    def get_variations(self,obj):
        variation_dict = defaultdict(list)
        variations = Variation.objects.filter(product=obj)
        for variation in variations:
            variation_dict[variation.variation_key].append(variation.variation_value)
        return variation_dict
    
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
    products_count = serializers.SerializerMethodField()

    def get_products_count(self,obj):
        return Product.objects.filter(category=obj).count()

    class Meta:
        model = Category
        fields = ('name','image','desc','sub_categories','products_count')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['image'] = self.context['view'].request.build_absolute_uri(instance.image.url)
        return representation


class SimpleProductSerializer(serializers.ModelSerializer):
    # variations = serializers.SerializerMethodField()

    # def get_variations(self,obj):
    #     variation_dict = defaultdict(list)
    #     variations = Variation.objects.filter(product=obj)
    #     for variation in variations:
    #         variation_dict[variation.variation_key].append(variation.variation_value)
    #     return variation_dict
    class Meta:
        model = Product
        fields = ('id','name','price','image','is_available')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['image'] = self.context['request'].build_absolute_uri(instance.image.url)
        return representation


class CartItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer()
    sub_total_price = serializers.SerializerMethodField()
    variations = serializers.SerializerMethodField()

    def get_variations(self,cart_item):
        variation_dict = defaultdict(list)
        variations = cart_item.variation.all()
        for variation in variations:
            variation_dict[variation.variation_key].append(variation.variation_value)
        return variation_dict

    def get_sub_total_price(self,cart_item):
        return cart_item.product.price * cart_item.quantity

    class Meta:
        model = CartItem
        fields = ('id','product','quantity','variations','sub_total_price')


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
    variations  = serializers.JSONField(required=False,write_only=True)

    class Meta:
        model = CartItem
        fields = ['id','product_id','quantity','variations']

    def validate_product_id(self,value):
        if not Product.objects.filter(pk=value).exists():
            raise serializers.ValidationError('No product found for given id')
        return value


    def create(self,validated_data):
        cart_id = self.context['cart_id']
        product_id = self.validated_data['product_id']
        quantity = self.validated_data['quantity']

        variation_list = []
        variations = self.validated_data.get('variations')
        if variations is not None and len(variations) > 0:
            for key in variations:
                value = variations[key]
                try:
                    var = Variation.objects.get(product=product_id,variation_key__iexact=key,variation_value__iexact=value)
                    variation_list.append(var)
                except Exception as e:
                    pass

        cart_items = CartItem.objects.filter(cart=cart_id)

        if cart_items.exists():
            print('yes items exists')
            existing_variation_list = []
            ids = []
            for item in cart_items:
                existing_variation_list.append(list(item.variation.all()))
                ids.append(item.id)

            print(variation_list,existing_variation_list)
            if variation_list in existing_variation_list:
                print('yes variation exists')
                item_index = existing_variation_list.index(variation_list)
                item_id    = ids[item_index]
                cart_item  = CartItem.objects.get(id=item_id)
                cart_item.quantity += quantity
                cart_item.save()
                self.instance = cart_item
            else:
                self.validated_data.pop('variations')
                self.instance = CartItem.objects.create(cart_id=cart_id,**self.validated_data)
                if variation_list is not None:
                    print(variation_list,'   :   ',*variation_list)
                    self.instance.variation.add(*variation_list)
        else:

        # try:
        #     cart_item = CartItem.objects.get(cart_id=cart_id,product_id=product_id)
        #     cart_item.quantity += quantity
        #     cart_item.save()
        #     self.instance = cart_item
        # except CartItem.DoesNotExist:
            # variation_list = validated_data.get('variations')
            self.validated_data.pop('variations')
            self.instance = CartItem.objects.create(cart_id=cart_id,**self.validated_data)
            if variation_list is not None:
                print(variation_list,'   :   ',*variation_list)
                self.instance.variation.add(*variation_list)
        return self.instance




class UpdateCartItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = CartItem
        fields = ['quantity']