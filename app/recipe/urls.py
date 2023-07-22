"""
URL mappings for hte recipe app"""

from django.urls import path, include

from rest_framework.routers import DefaultRouter

from recipe import views

# create endpoints for the viewset
router = DefaultRouter()
router.register('recipes', views.RecipeViewSet)

app_name = 'recipe'

urlpatterns = [
    path('', include(router.urls)),
]
