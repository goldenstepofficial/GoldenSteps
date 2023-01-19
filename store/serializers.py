from rest_framework import serializers

from .models import Product,Category,SubCategory



class ProductSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Product
        fields = ('category','sub_category','name','image','variations','details','price','stock','is_available')

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

    class Meta:
        model = Category
        fields = ('name','image','desc','sub_categories')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['image'] = self.context['view'].request.build_absolute_uri(instance.image.url)
        return representation
