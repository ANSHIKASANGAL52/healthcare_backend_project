from rest_framework.views import APIView
from rest_framework import status, permissions
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .models import PatientDoctorMapping
from .serializers import PatientDoctorMappingSerializer
from apps.patients.models import Patient


class MappingListCreateView(APIView):
    """
    API view to list all mappings or assign a doctor to a patient.
    - GET /api/mappings/ : Retrieve all patient-doctor mappings
    - POST /api/mappings/ : Assign a doctor to a patient
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PatientDoctorMappingSerializer

    @extend_schema(
        summary="Retrieve all patient-doctor mappings",
        responses={200: PatientDoctorMappingSerializer(many=True)}
    )
    def get(self, request):
        mappings = PatientDoctorMapping.objects.all().select_related('patient', 'doctor')
        serializer = self.serializer_class(mappings, many=True)
        return Response(
            {
                "success": True,
                "count": len(serializer.data),
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )

    @extend_schema(
        summary="Assign a doctor to a patient",
        request=PatientDoctorMappingSerializer,
        responses={
            201: PatientDoctorMappingSerializer,
            400: OpenApiResponse(description="Validation error")
        }
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            mapping = serializer.save()
            return Response(
                {
                    "success": True,
                    "message": "Doctor assigned to patient successfully.",
                    "data": self.serializer_class(mapping).data
                },
                status=status.HTTP_201_CREATED
            )
        return Response(
            {
                "success": False,
                "message": "Failed to assign doctor to patient.",
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )


class MappingDetailView(APIView):
    """
    API view for patient-specific mappings and mapping deletion.
    - GET /api/mappings/<patient_id>/ : Get all doctors assigned to a specific patient
    - DELETE /api/mappings/<id>/ : Remove a doctor from a patient (delete mapping)
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Get all doctors assigned to a specific patient",
        description="Retrieves all doctor assignments for the given patient ID.",
        responses={
            200: PatientDoctorMappingSerializer(many=True),
            404: OpenApiResponse(description="Patient not found")
        }
    )
    def get(self, request, pk):
        # First verify if patient exists
        patient = Patient.objects.filter(id=pk).first()
        if not patient:
            # Check if pk refers to a mapping id as fallback
            mapping = PatientDoctorMapping.objects.filter(id=pk).select_related('patient', 'doctor').first()
            if mapping:
                serializer = PatientDoctorMappingSerializer(mapping)
                return Response(
                    {
                        "success": True,
                        "data": serializer.data
                    },
                    status=status.HTTP_200_OK
                )
            return Response(
                {
                    "success": False,
                    "message": f"Patient with ID {pk} does not exist."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        mappings = PatientDoctorMapping.objects.filter(patient=patient).select_related('patient', 'doctor')
        serializer = PatientDoctorMappingSerializer(mappings, many=True)
        return Response(
            {
                "success": True,
                "patient_id": patient.id,
                "patient_name": patient.name,
                "count": len(serializer.data),
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )

    @extend_schema(
        summary="Remove a doctor from a patient",
        description="Deletes the patient-doctor mapping record with the specified ID.",
        responses={
            200: OpenApiResponse(description="Doctor removed from patient successfully"),
            404: OpenApiResponse(description="Mapping not found")
        }
    )
    def delete(self, request, pk):
        mapping = PatientDoctorMapping.objects.filter(id=pk).first()
        if not mapping:
            return Response(
                {
                    "success": False,
                    "message": f"Mapping with ID {pk} does not exist."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        mapping.delete()
        return Response(
            {
                "success": True,
                "message": "Doctor removed from patient successfully."
            },
            status=status.HTTP_200_OK
        )
