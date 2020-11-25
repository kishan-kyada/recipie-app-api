from django.test import TestCase
from django.contrib.auth import get_user, get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')

def create_user(**params):
    return get_user_model().objects.create_user(**params)

class PublicUserApiTests(TestCase):
    """Test the user api public"""
    
    def setUp(self):
        self.client = APIClient()
        
    def test_create_user_valid_success(self):
        """test create user with valid payload is successfull"""
        payload = {
            'email':'rest@api.com',
            'password':'testpass',
            'name':'Test name'
        }
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**res.data)
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)
        
    def test_user_exist(self):
        """test creating user that already exist fails"""
        payload = {'email': 'rest@api.com', 'password': 'testpass'}
        create_user(**payload)
        res =self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_password_too_short(self):
        """test that password must be more than 5 charcters"""
        payload = {'email':'rest@api.com', 'password': 'pw', 'name': 'Test'}
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exist = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exist)
        
    def test_create_token_for_user(self):
        """test that the token is created for user"""
        payload = {'email':'rest@api.com', 'password':"testpass"}
        create_user(**payload)
        res = self.client.post(TOKEN_URL, payload)
        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
    def test_create_token_invalid_credentials(self):
        """test that token is not created if invalid credentials are given"""
        create_user(email = 'rest@api.com', password="testpass")
        payload = {'email':'rest@api.com', 'password':"wrong"}
        res = self.client.post(TOKEN_URL, payload)
        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_create_token_no_user(self):
        """test that token is not created if user doesn't exist"""
        payload = {'email':'rest@api.com', 'password':"testpass"}
        res = self.client.post(TOKEN_URL, payload)
        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_create_token_missing_field(self):
        """test that email and passwor are required"""
        res = self.client.post(TOKEN_URL, {'email':'one', 'passowrd':''})
        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)