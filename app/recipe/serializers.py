"""
Serializers for recipe API
"""

from rest_framework import serializers

from core.models import Recipe


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for recipe objects"""

    class Meta:
        model = Recipe
        fields = [
            'id',
            'title',
            'time_minutes',
            'price',
            'description',
            'link',
        ]
        read_only_fields = ['id']
