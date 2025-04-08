from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
import json

class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.signup_url = reverse('signup')
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        self.user_details_url = reverse('user_details')
        
        # Create a test user
        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
    
    def test_signup(self):
        """Test user registration"""
        data = {
            'email': 'newuser@example.com',
            'password': 'newpassword123',
            'username': 'newuser'
        }
        response = self.client.post(self.signup_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue('tokens' in response.data)
        self.assertTrue('user' in response.data)
        self.assertEqual(response.data['user']['email'], 'newuser@example.com')
    
    def test_login(self):
        """Test user login"""
        data = {
            'email': 'test@example.com',
            'password': 'testpassword123'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('access' in response.data)
        self.assertTrue('refresh' in response.data)
    
    def test_logout(self):
        """Test user logout"""
        # First login to get token
        login_data = {
            'email': 'test@example.com',
            'password': 'testpassword123'
        }
        login_response = self.client.post(self.login_url, login_data, format='json')
        
        # Set authentication header for subsequent requests
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}")
        
        # Now logout
        logout_data = {
            'refresh': login_response.data['refresh']
        }
        response = self.client.post(self.logout_url, logout_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Successfully logged out')
        
    def test_get_user_details(self):
        """Test getting authenticated user details"""
        # First login to get token
        login_data = {
            'email': 'test@example.com',
            'password': 'testpassword123'
        }
        login_response = self.client.post(self.login_url, login_data, format='json')
        
        # Set authentication header for subsequent requests
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}")
        
        # Get user details
        response = self.client.get(self.user_details_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['username'], 'testuser')
    
    def test_invalid_login(self):
        """Test login with invalid credentials"""
        data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['error'], 'Invalid credentials')
    
    def test_missing_login_fields(self):
        """Test login with missing fields"""
        # Missing password
        data = {
            'email': 'test@example.com'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Missing email
        data = {
            'password': 'testpassword123'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_unauthorized_access(self):
        """Test accessing protected endpoint without authentication"""
        response = self.client.get(self.user_details_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class APIFunctionalityTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create a test user
        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        
        # Get tokens for authentication
        login_data = {
            'email': 'test@example.com',
            'password': 'testpassword123'
        }
        self.login_url = reverse('login')
        login_response = self.client.post(self.login_url, login_data, format='json')
        self.access_token = login_response.data['access']
        
        # Set up URLs for API endpoints
        self.analyze_text_url = reverse('analyze_text')
        self.process_data_url = reverse('process_data')
    
    def test_analyze_text(self):
        """Test the text analysis endpoint"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        
        data = {
            'text': 'This is a sample text for analysis containing a person and a location.'
        }
        response = self.client.post(self.analyze_text_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('sentiment' in response.data)
        self.assertTrue('entities' in response.data)
        self.assertTrue('summary' in response.data)
    
    def test_process_data(self):
        """Test the data processing endpoint"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        
        data = {
            'data_point_1': 'value_1',
            'data_point_2': 'value_2'
        }
        response = self.client.post(self.process_data_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user'], 'testuser')
        self.assertEqual(response.data['message'], 'Data processed successfully')
        self.assertEqual(response.data['received_data']['data_point_1'], 'value_1')
        self.assertEqual(response.data['received_data']['data_point_2'], 'value_2')