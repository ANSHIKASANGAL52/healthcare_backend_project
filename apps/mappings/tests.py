from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import CustomUser
from apps.patients.models import Patient
from apps.doctors.models import Doctor
from apps.mappings.models import PatientDoctorMapping


class MappingAPITests(APITestCase):
    def setUp(self):
        self.user1 = CustomUser.objects.create_user(
            email='coordinator1@healthcare.com',
            name='Care Coordinator 1',
            password='Password123!'
        )
        self.user2 = CustomUser.objects.create_user(
            email='coordinator2@healthcare.com',
            name='Care Coordinator 2',
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

        self.patient1 = Patient.objects.create(
            created_by=self.user1,
            name='Patient One (User 1)',
            age=30,
            gender='Female',
            contact_number='1234567890'
        )
        self.patient2 = Patient.objects.create(
            created_by=self.user2,
            name='Patient Two (User 2)',
            age=55,
            gender='Male',
            contact_number='0987654321'
        )

        self.doctor1 = Doctor.objects.create(
            created_by=self.user1,
            name='Dr. Allison Cameron',
            specialization='Immunology',
            license_number='MED-CAMERON',
            phone='+1-555-0201',
            email='cameron@hospital.org',
            experience_years=8
        )
        self.doctor2 = Doctor.objects.create(
            created_by=self.user1,
            name='Dr. Robert Chase',
            specialization='Intensive Care',
            license_number='MED-CHASE',
            phone='+1-555-0202',
            email='chase@hospital.org',
            experience_years=9
        )

        self.list_create_url = reverse('mapping-list-create')

    def test_assign_doctor_to_patient_success(self):
        """Test assigning a doctor to a patient by the patient's owner."""
        payload = {
            'patient_id': self.patient1.id,
            'doctor_id': self.doctor1.id,
            'notes': 'Initial consultation for autoimmune assessment.'
        }
        response = self.client.post(self.list_create_url, payload, format='json', **self.auth_headers1)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['patient']['id'], self.patient1.id)
        self.assertEqual(response.data['data']['doctor']['id'], self.doctor1.id)
        self.assertTrue(PatientDoctorMapping.objects.filter(patient=self.patient1, doctor=self.doctor1).exists())

    def test_assign_doctor_using_patient_doctor_keys(self):
        """Test assigning a doctor using 'patient' and 'doctor' payload keys."""
        payload = {
            'patient': self.patient1.id,
            'doctor': self.doctor2.id,
            'notes': 'Surgical evaluation'
        }
        response = self.client.post(self.list_create_url, payload, format='json', **self.auth_headers1)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PatientDoctorMapping.objects.filter(patient=self.patient1, doctor=self.doctor2).exists())

    def test_assign_doctor_to_unowned_patient_forbidden(self):
        """Security: User 2 cannot assign a doctor to User 1's patient."""
        payload = {
            'patient_id': self.patient1.id,
            'doctor_id': self.doctor1.id,
            'notes': 'Unauthorized assignment'
        }
        response = self.client.post(self.list_create_url, payload, format='json', **self.auth_headers2)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data['success'])
        self.assertFalse(PatientDoctorMapping.objects.filter(patient=self.patient1, doctor=self.doctor1).exists())

    def test_assign_doctor_duplicate_fails(self):
        """Test assigning the same doctor to the same patient again fails with 400."""
        PatientDoctorMapping.objects.create(patient=self.patient1, doctor=self.doctor1)
        payload = {
            'patient_id': self.patient1.id,
            'doctor_id': self.doctor1.id
        }
        response = self.client.post(self.list_create_url, payload, format='json', **self.auth_headers1)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_assign_unauthenticated(self):
        """Test mapping without authentication returns 401."""
        payload = {
            'patient_id': self.patient1.id,
            'doctor_id': self.doctor1.id
        }
        response = self.client.post(self.list_create_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_all_mappings_scoped_to_user_patients(self):
        """Test GET /api/mappings/ returns only mappings for patients owned by the requesting user."""
        PatientDoctorMapping.objects.create(patient=self.patient1, doctor=self.doctor1)
        PatientDoctorMapping.objects.create(patient=self.patient1, doctor=self.doctor2)
        PatientDoctorMapping.objects.create(patient=self.patient2, doctor=self.doctor1)

        # User 1 should only see 2 mappings for patient1
        response1 = self.client.get(self.list_create_url, **self.auth_headers1)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response1.data['count'], 2)
        for m in response1.data['data']:
            self.assertEqual(m['patient']['id'], self.patient1.id)

        # User 2 should only see 1 mapping for patient2
        response2 = self.client.get(self.list_create_url, **self.auth_headers2)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.data['count'], 1)
        self.assertEqual(response2.data['data'][0]['patient']['id'], self.patient2.id)

    def test_get_doctors_assigned_to_specific_patient(self):
        """Test GET /api/mappings/<patient_id>/ returns all doctors assigned to that patient."""
        PatientDoctorMapping.objects.create(patient=self.patient1, doctor=self.doctor1)
        PatientDoctorMapping.objects.create(patient=self.patient1, doctor=self.doctor2)

        patient1_url = reverse('mapping-detail', kwargs={'pk': self.patient1.id})
        response = self.client.get(patient1_url, **self.auth_headers1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        assigned_doctor_ids = [m['doctor']['id'] for m in response.data['data']]
        self.assertIn(self.doctor1.id, assigned_doctor_ids)
        self.assertIn(self.doctor2.id, assigned_doctor_ids)

    def test_get_mappings_for_other_users_patient_forbidden(self):
        """Security: User 2 cannot view doctors assigned to User 1's patient."""
        PatientDoctorMapping.objects.create(patient=self.patient1, doctor=self.doctor1)

        patient1_url = reverse('mapping-detail', kwargs={'pk': self.patient1.id})
        response = self.client.get(patient1_url, **self.auth_headers2)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data['success'])

    def test_get_mappings_nonexistent_patient(self):
        """Test GET /api/mappings/<patient_id>/ returns 404 for non-existent patient."""
        detail_url = reverse('mapping-detail', kwargs={'pk': 99999})
        response = self.client.get(detail_url, **self.auth_headers1)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_mapping_by_patient_owner(self):
        """Test DELETE /api/mappings/<id>/ removes doctor from patient when requested by owner."""
        mapping = PatientDoctorMapping.objects.create(patient=self.patient1, doctor=self.doctor1)
        detail_url = reverse('mapping-detail', kwargs={'pk': mapping.id})
        response = self.client.delete(detail_url, **self.auth_headers1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertFalse(PatientDoctorMapping.objects.filter(id=mapping.id).exists())

    def test_delete_mapping_by_unauthorized_user_forbidden(self):
        """Security: User 2 cannot delete a doctor mapping for User 1's patient."""
        mapping = PatientDoctorMapping.objects.create(patient=self.patient1, doctor=self.doctor1)
        detail_url = reverse('mapping-detail', kwargs={'pk': mapping.id})
        response = self.client.delete(detail_url, **self.auth_headers2)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(PatientDoctorMapping.objects.filter(id=mapping.id).exists())

    def test_delete_nonexistent_mapping(self):
        """Test DELETE /api/mappings/<id>/ returns 404 for invalid ID."""
        detail_url = reverse('mapping-detail', kwargs={'pk': 99999})
        response = self.client.delete(detail_url, **self.auth_headers1)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_staff_can_manage_any_mapping(self):
        """Staff user can assign, view, and delete any mapping."""
        # Staff can assign to user 1's patient
        payload = {
            'patient_id': self.patient1.id,
            'doctor_id': self.doctor1.id
        }
        post_resp = self.client.post(self.list_create_url, payload, format='json', **self.auth_headers_admin)
        self.assertEqual(post_resp.status_code, status.HTTP_201_CREATED)

        mapping_id = post_resp.data['data']['id']

        # Staff can view user 1's patient mappings
        patient1_url = reverse('mapping-detail', kwargs={'pk': self.patient1.id})
        get_resp = self.client.get(patient1_url, **self.auth_headers_admin)
        self.assertEqual(get_resp.status_code, status.HTTP_200_OK)

        # Staff can delete mapping
        detail_url = reverse('mapping-detail', kwargs={'pk': mapping_id})
        del_resp = self.client.delete(detail_url, **self.auth_headers_admin)
        self.assertEqual(del_resp.status_code, status.HTTP_200_OK)
