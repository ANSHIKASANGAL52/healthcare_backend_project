from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import CustomUser
from apps.doctors.models import Doctor


class DoctorAPITests(APITestCase):
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

        self.list_create_url = reverse('doctor-list')

        self.doctor_payload = {
            'name': 'Gregory House',
            'specialization': 'Diagnostic Medicine',
            'license_number': 'MED-12345',
            'phone': '+1-555-0100',
            'email': 'house@princetonplainsboro.org',
            'experience_years': 20
        }

    def test_create_doctor_authenticated(self):
        """Test adding a new doctor when authenticated saves created_by."""
        response = self.client.post(
            self.list_create_url,
            self.doctor_payload,
            format='json',
            **self.auth_headers1
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['name'], 'Gregory House')
        self.assertEqual(response.data['data']['license_number'], 'MED-12345')
        self.assertEqual(response.data['data']['created_by'], self.user1.id)
        self.assertTrue(Doctor.objects.filter(license_number='MED-12345').exists())

    def test_create_doctor_unauthenticated(self):
        """Test adding a doctor unauthenticated fails with 401."""
        response = self.client.post(self.list_create_url, self.doctor_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_doctor_duplicate_license(self):
        """Test duplicate doctor license number is rejected."""
        Doctor.objects.create(created_by=self.user1, **self.doctor_payload)
        duplicate_payload = self.doctor_payload.copy()
        duplicate_payload['email'] = 'other.doctor@hospital.org'
        response = self.client.post(
            self.list_create_url,
            duplicate_payload,
            format='json',
            **self.auth_headers1
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_doctors_list(self):
        """Test GET /api/doctors/ returns list of all doctors to any authenticated user."""
        Doctor.objects.create(created_by=self.user1, **self.doctor_payload)
        Doctor.objects.create(
            created_by=self.user2,
            name='James Wilson',
            specialization='Oncology',
            license_number='MED-54321',
            phone='+1-555-0101',
            email='wilson@princetonplainsboro.org',
            experience_years=18
        )
        response = self.client.get(self.list_create_url, **self.auth_headers1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_get_doctor_details(self):
        """Test GET /api/doctors/<id>/ returns doctor details to any authenticated user."""
        doc = Doctor.objects.create(created_by=self.user1, **self.doctor_payload)
        detail_url = reverse('doctor-detail', kwargs={'pk': doc.id})
        response = self.client.get(detail_url, **self.auth_headers2)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['id'], doc.id)
        self.assertEqual(response.data['data']['specialization'], 'Diagnostic Medicine')

    def test_update_doctor_by_creator(self):
        """Test PUT /api/doctors/<id>/ updates doctor details when performed by creator."""
        doc = Doctor.objects.create(created_by=self.user1, **self.doctor_payload)
        detail_url = reverse('doctor-detail', kwargs={'pk': doc.id})
        update_data = self.doctor_payload.copy()
        update_data['experience_years'] = 22
        update_data['phone'] = '+1-555-9999'
        response = self.client.put(detail_url, update_data, format='json', **self.auth_headers1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        doc.refresh_from_db()
        self.assertEqual(doc.experience_years, 22)
        self.assertEqual(doc.phone, '+1-555-9999')

    def test_update_doctor_by_unauthorized_user_forbidden(self):
        """Security: Non-creator user cannot update another user's doctor."""
        doc = Doctor.objects.create(created_by=self.user1, **self.doctor_payload)
        detail_url = reverse('doctor-detail', kwargs={'pk': doc.id})
        update_data = self.doctor_payload.copy()
        update_data['name'] = 'Dr. Malicious Change'
        response = self.client.put(detail_url, update_data, format='json', **self.auth_headers2)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        doc.refresh_from_db()
        self.assertEqual(doc.name, 'Gregory House')

    def test_delete_doctor_by_creator(self):
        """Test DELETE /api/doctors/<id>/ deletes doctor record when performed by creator."""
        doc = Doctor.objects.create(created_by=self.user1, **self.doctor_payload)
        detail_url = reverse('doctor-detail', kwargs={'pk': doc.id})
        response = self.client.delete(detail_url, **self.auth_headers1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Doctor.objects.filter(id=doc.id).exists())

    def test_delete_doctor_by_unauthorized_user_forbidden(self):
        """Security: Non-creator user cannot delete another user's doctor."""
        doc = Doctor.objects.create(created_by=self.user1, **self.doctor_payload)
        detail_url = reverse('doctor-detail', kwargs={'pk': doc.id})
        response = self.client.delete(detail_url, **self.auth_headers2)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Doctor.objects.filter(id=doc.id).exists())

    def test_staff_can_modify_and_delete_any_doctor(self):
        """Staff user can modify and delete any doctor profile."""
        doc = Doctor.objects.create(created_by=self.user1, **self.doctor_payload)
        detail_url = reverse('doctor-detail', kwargs={'pk': doc.id})
        update_data = self.doctor_payload.copy()
        update_data['specialization'] = 'Chief of Medicine'
        response = self.client.put(detail_url, update_data, format='json', **self.auth_headers_admin)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        del_response = self.client.delete(detail_url, **self.auth_headers_admin)
        self.assertEqual(del_response.status_code, status.HTTP_200_OK)
        self.assertFalse(Doctor.objects.filter(id=doc.id).exists())
