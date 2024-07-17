from __future__ import unicode_literals
from django.db import models
from django.utils import timezone
from django.db import transaction
from simple_history.models import HistoricalRecords
from django.contrib.auth.models import (
    AbstractBaseUser, PermissionsMixin, BaseUserManager
)
from django.conf import settings


class UserManager(BaseUserManager):

    def _create_user(self, email, password, **extra_fields):
        """
        Creates and saves a User with the given email,and password.
        """
        if not email:
            raise ValueError('The given email must be set')
        try:
            with transaction.atomic():
                user = self.model(email=email, **extra_fields)
                user.set_password(password)
                user.save(using=self._db)
                return user
        except:
            raise

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self._create_user(email, password=password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    An abstract base class implementing a fully featured User model with
    admin-compliant permissions.
 
    """
    first_name = models.CharField(max_length=25, blank=True)
    last_name = models.CharField(max_length=25, blank=True)
    email = models.EmailField(max_length=254, unique=True)
    password = models.CharField(max_length=254, blank=True, null=True)
    gender = models.CharField(max_length=6, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    phone_no = models.CharField(max_length=17, blank=True, null=True, help_text='Contact phone number')
    address = models.TextField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to='customer/', blank=True, null=True)
    image_name = models.CharField(max_length=100, blank=True, null=True)
    about_us = models.TextField(blank=True, null=True, help_text='user_description and about_us')
    is_active = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_send_time = models.DateTimeField(blank=True, null=True)
    is_staff = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    history = HistoricalRecords(table_name='user_history')

    def save(self, *args, **kwargs):
        super(User, self).save(*args, **kwargs)

    class Meta:
        db_table = 'auth_user'
        indexes = [
            models.Index(fields=['id', 'first_name', 'last_name', 'email', 'is_active'])
        ]
