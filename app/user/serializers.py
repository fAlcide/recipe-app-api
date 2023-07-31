"""
Selrializers for the user api
"""

from rest_framework import serializers
from django.contrib.auth import (
    get_user_model,
    authenticate,
)

from django.utils.translation import gettext as _


class UserSerializer(serializers.ModelSerializer):
    """Serializer for users object"""

    class Meta:
        model = get_user_model()
        fields = ('email', 'password', 'name')
        extra_kwargs = {
            'password': {
                'write_only': True,
                'min_length': 5
            }
        }

    def create(self, validated_data):
        """Create a new user with encrypted password and return it"""
        return get_user_model().objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        """Update a user, setting the password correctly and return it"""
        # On récupère le mot de passe
        password = validated_data.pop('password', None)
        # On appelle la méthode update de la classe parente
        user = super().update(instance, validated_data)
        # Si le mot de passe n'est pas vide
        if password:
            # On met à jour le mot de passe
            user.set_password(password)
            # On sauvegarde l'utilisateur
            user.save()

        return user


class AuthTokenSerializer(serializers.Serializer):
    """Serializer for the user auth toker """

    email = serializers.EmailField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False,
    )

    def validate(self, attrs):
        """Validate and authenticate the user"""
        email = attrs.get('email')
        password = attrs.get('password')
        user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password,
        )
        if not user:
            # On lève une exception si l'utilisateur n'est pas trouvé
            msg = _('Unable to authenticate with provided credentials')
            raise serializers.ValidationError(msg, code='authentication')

        attrs['user'] = user

        return attrs
