from rest_framework import serializers
from .models import Patient


class PatientSerializer(serializers.ModelSerializer):
    """
    Serializer for Patient CRUD operations.
    """
    created_by_name = serializers.CharField(source='created_by.name', read_only=True)
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)

    class Meta:
        model = Patient
        fields = [
            'id',
            'name',
            'age',
            'gender',
            'contact_number',
            'email',
            'address',
            'medical_history',
            'created_by',
            'created_by_name',
            'created_by_email',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_by_name', 'created_by_email', 'created_at', 'updated_at']

    def validate_age(self, value):
        if value < 0 or value > 150:
            raise serializers.ValidationError("Age must be between 0 and 150.")
        return value

    def validate_contact_number(self, value):
        stripped = value.strip()
        if len(stripped) < 7 or len(stripped) > 20:
            raise serializers.ValidationError("Contact number must be between 7 and 20 characters.")
        return stripped
