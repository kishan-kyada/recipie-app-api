from django.test import TestCase
from django.contrib.auth import get_user, get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')

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
        
    def test_retrive_user_unauthorized(self):
        """test that authorization is required for users"""
        res = self.client.post(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        
class PrivateUserApiTests(TestCase):
    """Test api request that require authentication"""
    
    def setUp(self):
        self.user = create_user(email="rest@api.com", password="testpass", name='name')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
    def test_retrieve_profile_success(self):
        """test retrieving profile for logged in user"""
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data,{
            'name': self.user.name,
            'email': self.user.email
        })
        
    def test_post_me_not_allowed(self):
        """test that post is not allowed on the me url."""
        res = self.client.post(ME_URL, {})
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
    def test_update_user_profile(self):
        """test updating the user profile for authenticated user"""
        payload = {'name': 'newname', 'password': 'newpassword123'}
        res = self.client.patch(ME_URL, payload)
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        