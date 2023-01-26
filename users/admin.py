from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserChangeForm,CustomUserCreationForm
from .models import User


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form     = CustomUserChangeForm
    model    = User
    list_display = ('email','phone_number','is_staff','is_active','phone_number',)
    list_filter = ('email','is_staff','is_active',)

    fieldsets = (
        (None,{'fields':('email','password')}),
        ('PersonalInfo',{'fields':('name','phone_number','is_phone_verified','is_email_verified','profile_picture')}),
        ('Permissions',{'fields':('is_staff','is_active')}),
    )

    add_fieldsets = (
        (None,{
            'classes':('wide',),
            'fields':('email','password1','password2','is_staff','is_active')
            }
        ),
    )

    search_fields = ('email','name')
    ordering = ('email',)

admin.site.register(User,CustomUserAdmin)
