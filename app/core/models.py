"""
Database models
"""

import uuid
import os

from django.conf import settings
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)


def recipe_image_file_path(instance, filename):
    """Generate file path for new recipe image"""
    # uuid4 generates a random UUID
    ext = os.path.splitext(filename)[1]
    filename = f'{uuid.uuid4()}{ext}'

    # return the path as a string
    return os.path.join('uploads', 'recipe', filename)


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


#  models.modl is the base class for all models in django
class Recipe(models.Model):
    """Recipe object"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    time_minutes = models.IntegerField()
    price = models.DecimalField(decimal_places=2, max_digits=5)
    link = models.CharField(max_length=255, blank=True)
    tags = models.ManyToManyField('Tag', blank=True)
    ingredients = models.ManyToManyField('Ingredient', blank=True)
    image = models.ImageField(null=True, upload_to=recipe_image_file_path)

    def __str__(self):
        """Return the string representation of the model"""
        return self.title


class Tag(models.Model):
    """Tag to be used for a recipe"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=255)

    # this is how to make a model return a string
    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Ingredient to be used in a recipe"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
