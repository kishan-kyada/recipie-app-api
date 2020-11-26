from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Ingredient
from recipe.serializers import IngredientSerializer

INGREDIENT_URL = reverse('recipe:ingredient-list')

class PublicIngredientApiTest(TestCase):
    """test the pubicly available ingredient API"""
    
    def setUp(self):
        self.client = APIClient()
        
    def test_login_required(self):
        """test that login is required to access the test point"""
        res = self.client.get(INGREDIENT_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        
class PrivateIngredientApiTest(TestCase):
    """test ingredient can be retrieve by authorized user"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user("rest@api.com", "testpass")
        self.client.force_authenticate(self.user)
        
    def test_retrieve_ingredient_list(self):
        """test retrieving a list of ingredient"""
        Ingredient.objects.create(user=self.user, name='kale')
        Ingredient.objects.create(user=self.user, name='Salt')
        res = self.client.get(INGREDIENT_URL)
        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
        
    def test_ingredient_limited_to_user(self):
        """test that ingredient for the authenticated user are return"""
        user2 = get_user_model().objects.create_user("res4t@api.com", "testpass")
        Ingredient.objects.create(user=user2, name='Vinegar')
        ingredient = Ingredient.objects.create(user=self.user, name='Turmeric')
        res = self.client.get(INGREDIENT_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)
        
    def test_create_ingredient_successfull(self):
        """test create anew ingredient"""
        payload = {'name': 'cabbage'}
        self.client.post(INGREDIENT_URL, payload)
        exists = Ingredient.objects.filter(user=self.user, name = payload['name']).exists()
        self.assertTrue(exists)
        
    def test_create_ingredient_invalid(self):
        """test creating a new ingredient with invalid payload"""
        payload = {'name': ''}
        res = self.client.post(INGREDIENT_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)