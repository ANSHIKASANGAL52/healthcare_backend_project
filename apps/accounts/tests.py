from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.accounts.models import CustomUser


class AuthenticationAPITests(APITestCase):
    def setUp(self):
        self.register_url = reverse('auth-register')
        self.login_url = reverse('auth-login')
        self.user_data = {
            'name': 'Dr. Alice Smith',
            'email': 'alice@healthcare.com',
            'password': 'StrongPassword123!'
        }

    def test_register_user_success(self):
        """Test registering a new user with valid details."""
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['user']['email'], 'alice@healthcare.com')
        self.assertEqual(response.data['data']['user']['name'], 'Dr. Alice Smith')
        self.assertIn('tokens', response.data['data'])
        self.assertIn('access', response.data['data']['tokens'])
        self.assertIn('refresh', response.data['data']['tokens'])
        self.assertTrue(CustomUser.objects.filter(email='alice@healthcare.com').exists())

    def test_register_duplicate_email(self):
        """Test registration fails when email is already registered."""
        CustomUser.objects.create_user(
            email='alice@healthcare.com',
            name='Alice',
            password='SomePassword123'
        )
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_register_short_password(self):
        """Test registration fails with a password shorter than 6 characters."""
        data = {
            'name': 'Bob',
            'email': 'bob@healthcare.com',
            'password': '123'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success(self):
        """Test logging in with valid credentials returns JWT tokens."""
        CustomUser.objects.create_user(
            email='alice@healthcare.com',
            name='Alice',
            password='StrongPassword123!'
        )
        login_payload = {
            'email': 'alice@healthcare.com',
            'password': 'StrongPassword123!'
        }
        response = self.client.post(self.login_url, login_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('tokens', response.data['data'])
        self.assertIn('access', response.data['data']['tokens'])
        self.assertIn('refresh', response.data['data']['tokens'])
        self.assertEqual(response.data['data']['user']['email'], 'alice@healthcare.com')

    def test_login_invalid_password(self):
        """Test login fails with incorrect password."""
        CustomUser.objects.create_user(
            email='alice@healthcare.com',
            name='Alice',
            password='StrongPassword123!'
        )
        login_payload = {
            'email': 'alice@healthcare.com',
            'password': 'WrongPassword!'
        }
        response = self.client.post(self.login_url, login_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_login_nonexistent_user(self):
        """Test login fails for an unregistered user."""
        login_payload = {
            'email': 'unknown@healthcare.com',
            'password': 'Password123'
        }
        response = self.client.post(self.login_url, login_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_login_inactive_user(self):
        """Test login fails for deactivated/disabled user."""
        user = CustomUser.objects.create_user(
            email='disabled@healthcare.com',
            name='Disabled User',
            password='Password123!'
        )
        user.is_active = False
        user.save()

        login_payload = {
            'email': 'disabled@healthcare.com',
            'password': 'Password123!'
        }
        response = self.client.post(self.login_url, login_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

