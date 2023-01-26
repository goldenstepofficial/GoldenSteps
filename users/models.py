from django.db import models
from django.contrib.auth.models import AbstractBaseUser,PermissionsMixin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from cloudinary.models import CloudinaryField

from .managers import UserManager


class User(AbstractBaseUser,PermissionsMixin):
    email             = models.EmailField(_('email address'), unique=True,db_index=True)
    name              = models.CharField(_('name'), max_length=50,blank=True,null=True)
    profile_picture   = CloudinaryField('images/user',blank=True,null=True)
    phone_number      = models.CharField(_('phone number'), max_length=15,blank=True,null=True)
    is_phone_verified = models.BooleanField(_('is phone verified'),default=False)
    is_email_verified = models.BooleanField(_('is email verified'),default=False)
    is_staff          = models.BooleanField(_('is_staff'),default=False)
    is_superuser      = models.BooleanField(_('is_superuser'),default=False)
    is_active         = models.BooleanField(_('is_active'),default=True)
    date_joined       = models.DateTimeField(_('date_joined'),default=timezone.now)

    USERNAME_FIELD    = 'email'
    REQUIRED_FIELDS   = []

    objects           = UserManager()

    def __str__(self):
        return self.email