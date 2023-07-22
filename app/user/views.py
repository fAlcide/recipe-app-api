"""
Viexs for the user api
"""
from rest_framework import generics, authentication, permissions
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings

from user.serializers import (
    UserSerializer,
    AuthTokenSerializer,
)


# Create your views here.
class CreateUserView(generics.CreateAPIView):
    """Create a new user in the system"""
    serializer_class = UserSerializer


class CreateTokenView(ObtainAuthToken):
    """Create a new auth token for user"""
    # On définit le serializer
    serializer_class = AuthTokenSerializer
    # On définit le renderer pour pouvoir voir la vue dans le navigateur
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES


class ManageUserView(generics.RetrieveUpdateAPIView):
    """Manage the authenticated user"""
    serializer_class = UserSerializer
    # On définit l'authentification
    authentication_classes = [authentication.TokenAuthentication]
    # On définit les permissions
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Retrieve and return authentication user"""
        return self.request.user
