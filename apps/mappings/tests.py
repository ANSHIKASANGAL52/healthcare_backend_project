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
        self.user = CustomUser.objects.create_user(
            email='coordinator@healthcare.com',
            name='Care Coordinator',
            password='Password123!'
        )
        token = RefreshToken.for_user(self.user)
        self.auth_headers = {'HTTP_AUTHORIZATION': f'Bearer {token.access_token}'}

        self.patient1 = Patient.objects.create(
            created_by=self.user,
            name='Patient One',
            age=30,
            gender='Female',
            contact_number='1234567890'
        )
        self.patient2 = Patient.objects.create(
            created_by=self.user,
            name='Patient Two',
            age=55,
            gender='Male',
            contact_number='0987654321'
        )

        self.doctor1 = Doctor.objects.create(
            name='Dr. Allison Cameron',
            specialization='Immunology',
            license_number='MED-CAMERON',
            phone='+1-555-0201',
            email='cameron@hospital.org',
            experience_years=8
        )
        self.doctor2 = Doctor.objects.create(
            name='Dr. Robert Chase',
            specialization='Intensive Care',
            license_number='MED-CHASE',
            phone='+1-555-0202',
            email='chase@hospital.org',
            experience_years=9
        )

        self.list_create_url = reverse('mapping-list-create')

    def test_assign_doctor_to_patient_success(self):
        """Test assigning a doctor to a patient."""
        payload = {
            'patient_id': self.patient1.id,
            'doctor_id': self.doctor1.id,
            'notes': 'Initial consultation for autoimmune assessment.'
        }
        response = self.client.post(self.list_create_url, payload, format='json', **self.auth_headers)
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
        response = self.client.post(self.list_create_url, payload, format='json', **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PatientDoctorMapping.objects.filter(patient=self.patient1, doctor=self.doctor2).exists())

    def test_assign_doctor_duplicate_fails(self):
        """Test assigning the same doctor to the same patient again fails with 400."""
        PatientDoctorMapping.objects.create(patient=self.patient1, doctor=self.doctor1)
        payload = {
            'patient_id': self.patient1.id,
            'doctor_id': self.doctor1.id
        }
        response = self.client.post(self.list_create_url, payload, format='json', **self.auth_headers)
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

    def test_get_all_mappings(self):
        """Test GET /api/mappings/ returns all patient-doctor mappings."""
        PatientDoctorMapping.objects.create(patient=self.patient1, doctor=self.doctor1)
        PatientDoctorMapping.objects.create(patient=self.patient1, doctor=self.doctor2)
        PatientDoctorMapping.objects.create(patient=self.patient2, doctor=self.doctor1)

        response = self.client.get(self.list_create_url, **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

    def test_get_doctors_assigned_to_specific_patient(self):
        """Test GET /api/mappings/<patient_id>/ returns all doctors assigned to that patient."""
        PatientDoctorMapping.objects.create(patient=self.patient1, doctor=self.doctor1)
        PatientDoctorMapping.objects.create(patient=self.patient1, doctor=self.doctor2)
        PatientDoctorMapping.objects.create(patient=self.patient2, doctor=self.doctor1)

        patient1_url = reverse('mapping-detail', kwargs={'pk': self.patient1.id})
        response = self.client.get(patient1_url, **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        assigned_doctor_ids = [m['doctor']['id'] for m in response.data['data']]
        self.assertIn(self.doctor1.id, assigned_doctor_ids)
        self.assertIn(self.doctor2.id, assigned_doctor_ids)

    def test_get_mappings_nonexistent_patient(self):
        """Test GET /api/mappings/<patient_id>/ returns 404 for non-existent patient."""
        detail_url = reverse('mapping-detail', kwargs={'pk': 99999})
        response = self.client.get(detail_url, **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_mapping(self):
        """Test DELETE /api/mappings/<id>/ removes doctor from patient."""
        mapping = PatientDoctorMapping.objects.create(patient=self.patient1, doctor=self.doctor1)
        detail_url = reverse('mapping-detail', kwargs={'pk': mapping.id})
        response = self.client.delete(detail_url, **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertFalse(PatientDoctorMapping.objects.filter(id=mapping.id).exists())

    def test_delete_nonexistent_mapping(self):
        """Test DELETE /api/mappings/<id>/ returns 404 for invalid ID."""
        detail_url = reverse('mapping-detail', kwargs={'pk': 99999})
        response = self.client.delete(detail_url, **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
