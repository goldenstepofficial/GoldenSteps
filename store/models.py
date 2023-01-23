from uuid import uuid4

from cloudinary.models import CloudinaryField
from django.core.validators import MaxValueValidator
from django.db import models
from django.core.validators import MinValueValidator

from users.models import User


class Category(models.Model):
    name          = models.CharField(max_length=50)
    image         = CloudinaryField('images/',null=True,blank=True)
    desc          = models.CharField(max_length=150,blank=True,null=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"


class SubCategory(models.Model):
    category    = models.ForeignKey(Category,on_delete=models.CASCADE,related_name="sub_categories")
    name        = models.CharField(max_length=50)
    image       = CloudinaryField('images/',blank=True,null=True)
    desc        = models.CharField(max_length=150)
    created_at  = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.name


    class Meta:
        verbose_name          = "SubCategory"
        verbose_name_plural   = "SubCategories"



class Product(models.Model):
    category      = models.ForeignKey(
                                Category,related_name="category_products",
                                blank=True,null=True,
                                on_delete=models.SET_NULL
                            )
    sub_category  = models.ForeignKey(
                                SubCategory,related_name="sub_category_products",
                                blank=True,null=True,on_delete=models.SET_NULL
                            )
    name          = models.CharField(max_length=100)
    image         = CloudinaryField('products/images/')
    variations    = models.JSONField()
    details       = models.JSONField()
    price         = models.IntegerField()
    stock         = models.IntegerField()
    is_available  = models.BooleanField(default=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.name



class ReviewRating(models.Model):
    product = models.ForeignKey(Product,on_delete=models.CASCADE,related_name="product_reviews")
    user    = models.ForeignKey(User, on_delete=models.CASCADE,related_name="user_reviews")
    title   = models.CharField(max_length=100)
    review  = models.TextField(max_length=512)
    rating  = models.FloatField(validators=[MaxValueValidator(5)])
    is_visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.title


class ProductGallery(models.Model):
    product = models.ForeignKey(Product,on_delete=models.CASCADE,related_name="image_gallery")
    image   = CloudinaryField('review/images/')

    def __str__(self):
        return self.product

    class Meta:
        verbose_name = "product gallery"
        verbose_name_plural = "product galleries"



class Cart(models.Model):
    id = models.UUIDField(primary_key=True,default=uuid4)
    created_at = models.DateTimeField(auto_now_add=True)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart,on_delete=models.CASCADE,related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])


    class Meta:
        unique_together = [['cart', 'product']]