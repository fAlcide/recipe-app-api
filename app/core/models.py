"""
Dtabase models
"""

from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)


class UserManager(BaseUserManager):
    """Manager for user profiles"""

    # extra fields are for any other fields we pass in
    def create_user(self, email, password=None, **extra_fields):
        """Create a new user"""
        if (not email):
            raise ValueError('Users must have an email address')
        # creates a new model that we can then modify
        user = self.model(email=self.normalize_email(email), **extra_fields)
        # set_password is a helper function that comes with BaseUserManager
        user.set_password(password)
        # using=self._db is for supporting multiple databases
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create a new super user"""
        # create a new user
        user = self.create_user(email, password, **extra_fields)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    """User in the system"""
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    # is the user active
    is_active = models.BooleanField(default=True)
    # is the user a django admin member
    is_staff = models.BooleanField(default=False)

    # this is the object manager for the user model
    objects = UserManager()

    USERNAME_FIELD = 'email'
