from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    '''custom user manager for managing User objects'''

    def create_user(self,email,password,**extra_fields):
        '''create a and save a new User with given email and password'''

        if not email:
            raise ValueError(_('The Email is Required'))
            
        email = self.normalize_email(email)
        user  = self.model(email=email,**extra_fields)
        user.set_password(password)
        user.save()
        return user

    
    def create_superuser(self,email,password,**extra_fields):
        '''create and save a new superuser with the given email and password'''

        extra_fields.setdefault('is_staff',True)
        extra_fields.setdefault('is_superuser',True)
        extra_fields.setdefault('is_active',True)

        # make sure required fields are set
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('is_staff should be set to True for superusers'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('is_superuser should be set to True for Superusers'))

        return self.create_user(email,password,**extra_fields)
