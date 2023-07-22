"""
Tests for the user api
"""


from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

# On définit l'URL pour créer un utilisateur.
# Elle va mapper la ligne appname = user de user/urls.py
CREATE_USER_URL = reverse('user:create')  # /api/user/create
TOKEN_URl = reverse('user:token')  # /api/user/token
ME_URL = reverse('user:me')  # /api/user/me


def create_user(**params):
    """
    Create and return a new user
    """
    return get_user_model().objects.create_user(**params)


""" On fait la différence entre des requêtes authentifiées
    et non authentifiées
"""


class PublicUserApiTests(TestCase):
    """Test the public features of the user API"""

    def setUp(self):
        self.client = APIClient()  # Création d'un client

    def test_create_valid_user_success(self):
        """Test creating user with valid user is successful"""
        payload = {
            'email': 'test@email.com',
            'password': 'testpass',
            'name': 'Test Name'
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**res.data)
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)

    def test_user_wtih_email_exists(self):
        """Test creating a user that already exists fails"""
        payload = {
            'email': 'test@example.com',
            'password': 'testpass',
            'name': 'Test Name',
        }

        # On crée l'utilisateur
        create_user(**payload)
        # On fait une requête POST avec le client
        res = self.client.post(CREATE_USER_URL, payload)

        # On vérifie que la requête a bien été effectuée
        # et que c'est bien une mauvaise requête
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        """Test creating a user with password too short """
        payload = {
            'email': 'test@example.com',
            'password': '12',
            'name': 'Test Name',
        }

        # On fait une requête POST avec le client
        res = self.client.post(CREATE_USER_URL, payload)

        # On vérifie que la requête a bien été effectuée
        # et que c'est bien une mauvaise requête
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # On vérifie que l'utilisateur n'a pas été créé
        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Test that a token is created for the user"""
        user_details = {
            'name': 'Test Name',
            'email': 'test123@example.com',
            'password': 'test-alcide-pass123',
        }
        create_user(**user_details)

        payload = {
            'email': user_details['email'],
            'password': user_details['password'],
        }
        res = self.client.post(TOKEN_URl, payload)

        # On vérifie que le token est bien dans la réponse
        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def create_token_bad_credentials(self):
        """Test that token is not created if invalid credentials are given"""
        create_user(email="test@exaple.com", password="goodpass")
        payload = {'email': 'test@example.com', 'password': 'badpass'}
        res = self.client.post(TOKEN_URl, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_blank_password(self):
        """Test that token is not created if password is blank"""
        payload = {'email': 'test@example.cpom', 'password': ''}
        res = self.client.post(TOKEN_URl, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        """Test that authentification is required for users"""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    """Test API requests that require authentification"""

    def setUp(self):
        self.user = create_user(
            email="test@example.com",
            password="testpass123",
            name="Test Name",
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """Test retrieving profile for logged in user"""
        res = self.client.get(ME_URL)

        # On vérifie que la requête a bien été effectuée
        print(res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'email': self.user.email,
            'name': self.user.name,
        })

    def test_post_me_not_allowed(self):
        """Test that POST is not allowed on the me url"""
        res = self.client.post(ME_URL, {})

        # On vérifie que la requête a bien été effectuée
        # et que c'est bien une mauvaise requête
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_use_profile(self):
        """Test updating the user profile for authenticated user"""
        payload = {'name': 'New Name', 'password': 'newpass123'}

        res = self.client.patch(ME_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
