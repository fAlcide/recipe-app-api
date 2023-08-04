"""
Test for recipe api
"""

from decimal import Decimal
import tempfile
import os

from PIL import Image

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import (
    Recipe,
    Tag,
    Ingredient,
)

from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
)

RECIPES_URL = reverse('recipe:recipe-list')


def details_url(recipe_id):
    """Create and return a recipe detail url"""
    # reverse function will create the url for us
    # /api/recipe/recipes/id
    return reverse('recipe:recipe-detail', args=[recipe_id])


def sample_tag(user, name='Main course'):
    """Create and return a sample tag"""
    return Tag.objects.create(user=user, name=name)


def sample_recipe(user, **params):
    """Create and return a sample recipe"""
    defaults = {
        'title': 'Sample recipe',
        'time_minutes': 10,
        'price': 5.00
    }
    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


def image_upload_url(recipe_id):
    """Create and return URL for recipe image upload"""
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


# /api/recipe/recipes
def create_recipe(user, **params):
    """Create and retunr a sample recipe"""
    defaults = {
        'title': 'Sample recipe',
        'time_minutes': 10,
        'price': Decimal('5.00'),
        'description': 'Sample description',
        'link': 'https://sample.com',
    }
    # update method takes a dictionary and updates the object
    defaults.update(params)

    recipe = Recipe.objects.create(user=user, **defaults)

    return recipe


class PublicRecipeApiTests(TestCase):
    """Test unauthenticated recipe API access"""

    # this function is run before every test
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test that authentication is required"""
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """Test unauthenticated recipe API access"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email='user@example.com', password='test123')

        # force_authenticate is a helper function that comes with APIClient
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes"""
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        """Test list of recipes is limited to authenticated user"""
        user2 = create_user(email='user123@example.com', password='test123')
        create_recipe(user=user2)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # we compare api data with serializer data
        self.assertEqual(res.data, serializer.data)

    def test_view_recipe_detail(self):
        """test get recipe deail"""
        recipe = create_recipe(user=self.user)

        url = details_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_basic_recipe(self):
        """Test creating recipe"""
        payload = {
            'title': 'Chocolate_cake',
            'time_minutes': 30,
            'price': Decimal('5.00'),
        }

        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_create_recipe_with_new_tags(self):
        """Test creating a recipe with new tags"""
        payload = {
            'title': 'Chocolate_cake',
            'time_minutes': 30,
            'price': Decimal('5.00'),
            'tags': [{'name': 'Dessert'}, {'name': 'Protein'}],
        }

        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tag(self):
        """Test creating a recipe with existing tag"""
        tag1 = Tag.objects.create(user=self.user, name="Protein")
        payload = {
            "title": "Chocolate cheesecake",
            "tags": [{"name": tag1.name}, {"name": "Malin"}],
            "time_minutes": 30,
            "price": 5.00
        }
        res = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag1, recipe.tags.all())
        for tag in payload["tags"]:
            exists = recipe.tags.filter(
                name=tag["name"],
                user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_partial_update_recipe(self):
        """Test updating a recipe with patch"""
        original_link = 'https://sample.com'
        recipe = create_recipe(
            user=self.user,
            title='Chocolate cheesecake',
            link=original_link
        )

        payload = {'title': 'Chocolate cheesecake'}
        url = details_url(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update_recipe(self):
        """Test updating a recipe with put"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        payload = {
            'title': 'Spaghetti carbonara',
            'time_minutes': 25,
            'price': 5.00
        }
        url = details_url(recipe.id)
        self.client.put(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.time_minutes, payload['time_minutes'])
        self.assertEqual(recipe.price, payload['price'])
        tags = recipe.tags.all()
        self.assertEqual(len(tags), 0)

    def test_delete_recipe(self):
        """Test deleting a recipe"""
        recipe = create_recipe(user=self.user)
        url = details_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_tag_on_update(self):
        """Test creating a tag on update"""
        recipe = create_recipe(user=self.user)
        payload = {
            'title': 'Spaghetti carbonara',
            'time_minutes': 25,
            'price': 5.00,
            'tags': [{'name': 'Pasta'}]
        }
        url = details_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        new_tag = Tag.objects.get(user=self.user, name="Pasta")
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        """Test updating a recipe with existing tag"""
        tag1 = Tag.objects.create(user=self.user, name="Protein")
        tag2 = Tag.objects.create(user=self.user, name="Dessert")

        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag1)
        payload = {
            "tags": [{"name": "Dessert"}],
        }

        url = details_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag2, recipe.tags.all())
        self.assertNotIn(tag1, recipe.tags.all())

    def test_clear_recipe_tags(self):
        """Test clearing recipe tags"""
        tag1 = Tag.objects.create(user=self.user, name="Protein")
        tag2 = Tag.objects.create(user=self.user, name="Dessert")

        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag1)
        payload = {
            "tags": [],
        }

        url = details_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotIn(tag1, recipe.tags.all())
        self.assertNotIn(tag2, recipe.tags.all())

    def test_create_recipe_with_new_ingredients(self):
        """Test creating a Recipe with new ingredients"""

        payload = {
            "title": "Chocolate cheesecake",
            "ingredients": [{"name": "Chocolate"}, {"name": "Cheese"}],
            "time_minutes": 30,
            "price": 5.00
        }

        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipes[0].ingredients.count(), 2)
        for ingredient in payload["ingredients"]:
            exist = recipe.ingredients.filter(
                name=ingredient["name"],
                user=self.user
            ).exists()
            self.assertTrue(exist)

    def test_create_recipe_with_existing_ingredients(self):
        """Test creating a Recipe with existing ingredients"""
        # since we have created a ingredient name chocolate,
        # we check it will not create a new one

        ingredient1 = Ingredient.objects.create(
            user=self.user,
            name="Chocolate"
            )

        payload = {
            "title": "Chocolate cheesecake",
            "ingredients": [{"name": "Chocolate"}, {"name": "Sugar"}],
            "time_minutes": 30,
            "price": 5.00
        }

        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipes[0].ingredients.count(), 2)
        self.assertIn(ingredient1, recipe.ingredients.all())

        for ingredient in payload["ingredients"]:
            exist = recipe.ingredients.filter(
                name=ingredient["name"],
                user=self.user
            ).exists()
            self.assertTrue(exist)

    def test_create_ingredient_on_update(self):
        """Test creating an ingredient on update"""
        recipe = create_recipe(user=self.user)
        payload = {
            'ingredients': [{'name': 'Pasta'}]
        }
        url = details_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        new_ingredient = Ingredient.objects.get(
            user=self.user, name="Pasta")
        self.assertIn(new_ingredient, recipe.ingredients.all())

    def test_update_recipe_assign_ingredients(self):
        """Test updating a recipe with existing ingredients"""
        ingredient1 = Ingredient.objects.create(
            user=self.user,
            name="Chocolate"
            )
        ingredient2 = Ingredient.objects.create(
            user=self.user,
            name="Sugar"
            )

        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient1)
        payload = {
            "ingredients": [{"name": "Sugar"}],
        }

        url = details_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ingredient2, recipe.ingredients.all())
        self.assertNotIn(ingredient1, recipe.ingredients.all())

    def test_clear_recipe_ingredients(self):
        """Test clearing recipe ingredients"""
        ingredient1 = Ingredient.objects.create(
            user=self.user,
            name="Chocolate"
            )
        ingredient2 = Ingredient.objects.create(
            user=self.user,
            name="Sugar"
            )

        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient1)
        payload = {
            "ingredients": [],
        }

        url = details_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotIn(ingredient1, recipe.ingredients.all())
        self.assertNotIn(ingredient2, recipe.ingredients.all())

    def test_filter_by_tags(self):
        """Test filterring recipes by tags"""
        r1 = create_recipe(user=self.user, title="Thai vegetable curry")
        r2 = create_recipe(user=self.user, title="Aubergine with tahini")
        tag1 = Tag.objects.create(user=self.user, name="Vegan")
        tag2 = Tag.objects.create(user=self.user, name="Vegetarian")
        r1.tags.add(tag1)
        r2.tags.add(tag2)
        r3 = create_recipe(user=self.user, title="Fish and chips")

        prarams = {'tags': f'{tag1.id},{tag2.id}'}
        res = self.client.get(RECIPES_URL, prarams)

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)

        # check if the response contains the correct data
        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)

    def test_filter_by_ingredients(self):
        """Test filterring recipes by ingredients"""
        r1 = create_recipe(user=self.user, title="Posh beans on toast")
        r2 = create_recipe(user=self.user, title="Chicken cacciatore")
        ingredient1 = Ingredient.objects.create(
            user=self.user,
            name="Feta cheese"
            )
        ingredient2 = Ingredient.objects.create(
            user=self.user,
            name="Chicken"
            )
        r1.ingredients.add(ingredient1)
        r2.ingredients.add(ingredient2)
        r3 = create_recipe(user=self.user, title="Steak and mushrooms")

        prarams = {'ingredients': f'{ingredient1.id},{ingredient2.id}'}
        res = self.client.get(RECIPES_URL, prarams)

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)

        # check if the response contains the correct data
        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)


class imageUploadTest(TestCase):
    """Test image upload"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'test@example.com',
            'password123'
        )
        self.client.force_authenticate(self.user)
        self.recipe = create_recipe(user=self.user)

    def tearDown(self):
        # delete the image after test
        self.recipe.image.delete()

    def test_upload_image(self):
        """Test uplaoding an image to a recipe"""
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            image = Image.new('RGB', (10, 10))
            image.save(image_file, format='JPEG')
            image_file.seek(0)
            payload = {'image': image_file}
            res = self.client.post(
                url,
                payload,
                format='multipart'
                )
        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        """Test uploadding invalid image"""
        url = image_upload_url(self.recipe.id)
        payload = {'image': 'notimage'}
        res = self.client.post(
            url,
            payload,
            format='multipart'
            )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
