from rest_framework import serializers
from .models import Doctor


class DoctorSerializer(serializers.ModelSerializer):
    """
    Serializer for Doctor CRUD operations.
    """
    created_by_name = serializers.CharField(source='created_by.name', read_only=True)

    class Meta:
        model = Doctor
        fields = [
            'id',
            'name',
            'specialization',
            'license_number',
            'phone',
            'email',
            'experience_years',
            'created_by',
            'created_by_name',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_by_name', 'created_at', 'updated_at']

    def validate_license_number(self, value):
        stripped = value.strip().upper()
        doctor_id = self.instance.id if self.instance else None
        if Doctor.objects.filter(license_number__iexact=stripped).exclude(id=doctor_id).exists():
            raise serializers.ValidationError("A doctor with this license number already exists.")
        return stripped

    def validate_email(self, value):
        normalized = value.strip().lower()
        doctor_id = self.instance.id if self.instance else None
        if Doctor.objects.filter(email__iexact=normalized).exclude(id=doctor_id).exists():
            raise serializers.ValidationError("A doctor with this email already exists.")
        return normalized

    def validate_experience_years(self, value):
        if value < 0 or value > 80:
            raise serializers.ValidationError("Experience years must be between 0 and 80.")
        return value
