"""
Tests for models
"""

from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models


class ModelTests(TestCase):
    """
    Test cases for models
    """

    def test_create_user_with_email_successful(self):
        """
        Test creating a new user with an email is successful
        """

        email = 'test@example.com'
        password = 'Testpass123'
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )

        # assert that the email is the same as the one we created
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """
        Test the email for a new user is normalized
        """

        sample_email = [
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['Test2@Example.com', 'Test2@example.com'],
            ['TEST3@EXAMPLE.COM', 'TEST3@example.com'],
            ['test4@example.COM', 'test4@example.com'],
        ]

        for email, expected in sample_email:  # for each email in sample_email
            user = get_user_model().objects.create_user(email, 'sample123')
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raises_error(self):
        """ Test that creating a uesr whitout an email raisses a ValueError """
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', 'test123')

    def test_create_super_user(self):
        """Test creating super user"""
        user = get_user_model().objects.create_superuser(
            'test@example.com',
            'test123',
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_recipe(self):
        """Test creating a new recipe"""
        user = get_user_model().objects.create_user(
            'test@example.com',
            'test123pass',
        )
        recipe = models.Recipe.objects.create(
            user=user,
            title='Steak and mushroom sauce',
            time_minutes=5,
            price=Decimal('5.50'),
            description='This is a test description',
        )

        self.assertEqual(str(recipe), recipe.title)
