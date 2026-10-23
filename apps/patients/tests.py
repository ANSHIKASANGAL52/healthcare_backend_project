from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import CustomUser
from apps.patients.models import Patient


class PatientAPITests(APITestCase):
    def setUp(self):
        self.user1 = CustomUser.objects.create_user(
            email='user1@healthcare.com',
            name='User One',
            password='Password123!'
        )
        self.user2 = CustomUser.objects.create_user(
            email='user2@healthcare.com',
            name='User Two',
            password='Password123!'
        )
        self.admin_user = CustomUser.objects.create_superuser(
            email='admin@healthcare.com',
            name='Admin User',
            password='AdminPassword123!'
        )

        token1 = RefreshToken.for_user(self.user1)
        self.auth_headers1 = {'HTTP_AUTHORIZATION': f'Bearer {token1.access_token}'}

        token2 = RefreshToken.for_user(self.user2)
        self.auth_headers2 = {'HTTP_AUTHORIZATION': f'Bearer {token2.access_token}'}

        token_admin = RefreshToken.for_user(self.admin_user)
        self.auth_headers_admin = {'HTTP_AUTHORIZATION': f'Bearer {token_admin.access_token}'}

        self.list_create_url = reverse('patient-list')

        self.patient_payload = {
            'name': 'John Doe',
            'age': 35,
            'gender': 'Male',
            'contact_number': '+1-555-0199',
            'email': 'john.doe@example.com',
            'address': '123 Main Street',
            'medical_history': 'Seasonal allergies'
        }

    def test_create_patient_authenticated(self):
        """Test adding a new patient when authenticated."""
        response = self.client.post(
            self.list_create_url,
            self.patient_payload,
            format='json',
            **self.auth_headers1
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['name'], 'John Doe')
        self.assertEqual(response.data['data']['created_by'], self.user1.id)

    def test_create_patient_unauthenticated(self):
        """Test adding a patient without auth fails with 401."""
        response = self.client.post(self.list_create_url, self.patient_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_patient_invalid_data(self):
        """Test patient validation fails on invalid age."""
        invalid_payload = self.patient_payload.copy()
        invalid_payload['age'] = 999
        response = self.client.post(
            self.list_create_url,
            invalid_payload,
            format='json',
            **self.auth_headers1
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_patients_scoped_to_authenticated_user(self):
        """Test GET /api/patients/ retrieves only patients created by the authenticated user."""
        # Create 2 patients for user1
        Patient.objects.create(created_by=self.user1, name='User1 Patient A', age=20, gender='Female', contact_number='12345678')
        Patient.objects.create(created_by=self.user1, name='User1 Patient B', age=30, gender='Male', contact_number='87654321')

        # Create 1 patient for user2
        Patient.objects.create(created_by=self.user2, name='User2 Patient C', age=40, gender='Other', contact_number='99999999')

        # Request with user1 credentials
        response = self.client.get(self.list_create_url, **self.auth_headers1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        patient_names = [p['name'] for p in response.data['data']]
        self.assertIn('User1 Patient A', patient_names)
        self.assertIn('User1 Patient B', patient_names)
        self.assertNotIn('User2 Patient C', patient_names)

        # Request with user2 credentials
        response_user2 = self.client.get(self.list_create_url, **self.auth_headers2)
        self.assertEqual(response_user2.status_code, status.HTTP_200_OK)
        self.assertEqual(response_user2.data['count'], 1)
        self.assertEqual(response_user2.data['data'][0]['name'], 'User2 Patient C')

    def test_get_patient_details(self):
        """Test GET /api/patients/<id>/ returns patient details to the owner."""
        patient = Patient.objects.create(
            created_by=self.user1,
            name='Alice Johnson',
            age=28,
            gender='Female',
            contact_number='123456789'
        )
        detail_url = reverse('patient-detail', kwargs={'pk': patient.id})
        response = self.client.get(detail_url, **self.auth_headers1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['name'], 'Alice Johnson')
        self.assertEqual(response.data['data']['id'], patient.id)

    def test_user_cannot_read_other_users_patient(self):
        """Security/IDOR test: User 2 cannot access User 1's patient details."""
        patient_user1 = Patient.objects.create(
            created_by=self.user1,
            name='Private Patient',
            age=32,
            gender='Female',
            contact_number='5551234567'
        )
        detail_url = reverse('patient-detail', kwargs={'pk': patient_user1.id})
        # User 2 attempts to read User 1's patient
        response = self.client.get(detail_url, **self.auth_headers2)
        self.assertIn(response.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN])

    def test_user_cannot_update_other_users_patient(self):
        """Security/IDOR test: User 2 cannot update User 1's patient record."""
        patient_user1 = Patient.objects.create(
            created_by=self.user1,
            name='Original Name',
            age=40,
            gender='Male',
            contact_number='5559876543'
        )
        detail_url = reverse('patient-detail', kwargs={'pk': patient_user1.id})
        update_data = {
            'name': 'Hacked Name',
            'age': 41,
            'gender': 'Male',
            'contact_number': '5559876543'
        }
        # User 2 attempts to update User 1's patient
        response = self.client.put(detail_url, update_data, format='json', **self.auth_headers2)
        self.assertIn(response.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN])
        patient_user1.refresh_from_db()
        self.assertEqual(patient_user1.name, 'Original Name')

    def test_user_cannot_delete_other_users_patient(self):
        """Security/IDOR test: User 2 cannot delete User 1's patient record."""
        patient_user1 = Patient.objects.create(
            created_by=self.user1,
            name='Protected Patient',
            age=45,
            gender='Female',
            contact_number='5551122334'
        )
        detail_url = reverse('patient-detail', kwargs={'pk': patient_user1.id})
        # User 2 attempts to delete User 1's patient
        response = self.client.delete(detail_url, **self.auth_headers2)
        self.assertIn(response.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN])
        self.assertTrue(Patient.objects.filter(id=patient_user1.id).exists())

    def test_staff_can_access_any_patient(self):
        """Staff user can access and manage any patient."""
        patient_user1 = Patient.objects.create(
            created_by=self.user1,
            name='Patient Under Care',
            age=60,
            gender='Male',
            contact_number='5554433221'
        )
        detail_url = reverse('patient-detail', kwargs={'pk': patient_user1.id})
        response = self.client.get(detail_url, **self.auth_headers_admin)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['name'], 'Patient Under Care')

    def test_update_patient(self):
        """Test PUT /api/patients/<id>/ updates patient details for owner."""
        patient = Patient.objects.create(
            created_by=self.user1,
            name='Bob Brown',
            age=45,
            gender='Male',
            contact_number='1122334455'
        )
        detail_url = reverse('patient-detail', kwargs={'pk': patient.id})
        update_data = {
            'name': 'Bob Brown Jr.',
            'age': 46,
            'gender': 'Male',
            'contact_number': '1122334499',
            'medical_history': 'Hypertension diagnosed'
        }
        response = self.client.put(detail_url, update_data, format='json', **self.auth_headers1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        patient.refresh_from_db()
        self.assertEqual(patient.name, 'Bob Brown Jr.')
        self.assertEqual(patient.age, 46)

    def test_delete_patient(self):
        """Test DELETE /api/patients/<id>/ deletes the record for owner."""
        patient = Patient.objects.create(
            created_by=self.user1,
            name='Charlie Day',
            age=50,
            gender='Male',
            contact_number='9876543210'
        )
        detail_url = reverse('patient-detail', kwargs={'pk': patient.id})
        response = self.client.delete(detail_url, **self.auth_headers1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Patient.objects.filter(id=patient.id).exists())
