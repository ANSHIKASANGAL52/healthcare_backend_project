from rest_framework import serializers
from .models import PatientDoctorMapping
from apps.patients.models import Patient
from apps.doctors.models import Doctor
from apps.patients.serializers import PatientSerializer
from apps.doctors.serializers import DoctorSerializer


class PatientDoctorMappingSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and viewing Patient-Doctor mappings.
    Accepts both `patient`/`doctor` and `patient_id`/`doctor_id` payloads.
    """
    patient = PatientSerializer(read_only=True)
    doctor = DoctorSerializer(read_only=True)

    patient_id = serializers.PrimaryKeyRelatedField(
        queryset=Patient.objects.all(),
        source='patient',
        write_only=True,
        required=False
    )
    doctor_id = serializers.PrimaryKeyRelatedField(
        queryset=Doctor.objects.all(),
        source='doctor',
        write_only=True,
        required=False
    )

    class Meta:
        model = PatientDoctorMapping
        fields = [
            'id',
            'patient',
            'doctor',
            'patient_id',
            'doctor_id',
            'assigned_date',
            'notes'
        ]
        read_only_fields = ['id', 'assigned_date']

    def to_internal_value(self, data):
        # Support both 'patient' / 'doctor' and 'patient_id' / 'doctor_id'
        data_copy = data.copy() if hasattr(data, 'copy') else dict(data)
        if 'patient' in data_copy and 'patient_id' not in data_copy:
            data_copy['patient_id'] = data_copy['patient']
        if 'doctor' in data_copy and 'doctor_id' not in data_copy:
            data_copy['doctor_id'] = data_copy['doctor']
        return super().to_internal_value(data_copy)

    def validate(self, attrs):
        patient = attrs.get('patient')
        doctor = attrs.get('doctor')

        if not patient:
            raise serializers.ValidationError({"patient": "This field is required."})
        if not doctor:
            raise serializers.ValidationError({"doctor": "This field is required."})

        if PatientDoctorMapping.objects.filter(patient=patient, doctor=doctor).exists():
            raise serializers.ValidationError(
                "This doctor is already assigned to this patient."
            )
        return attrs
