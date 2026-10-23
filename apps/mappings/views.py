from rest_framework.views import APIView
from rest_framework import status, permissions
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .models import PatientDoctorMapping
from .serializers import PatientDoctorMappingSerializer
from apps.patients.models import Patient
from apps.doctors.models import Doctor


class MappingListCreateView(APIView):
    """
    API view to list patient-doctor mappings or assign a doctor to a patient.
    - GET /api/mappings/ : Retrieve patient-doctor mappings (scoped to user's patients)
    - POST /api/mappings/ : Assign a doctor to a patient (requires patient ownership)
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PatientDoctorMappingSerializer

    @extend_schema(
        summary="Retrieve patient-doctor mappings",
        description="Returns mappings for patients created by the authenticated user (or all mappings for staff).",
        responses={200: PatientDoctorMappingSerializer(many=True)}
    )
    def get(self, request):
        if request.user.is_staff:
            mappings = PatientDoctorMapping.objects.all().select_related('patient', 'doctor')
        else:
            mappings = PatientDoctorMapping.objects.filter(
                patient__created_by=request.user
            ).select_related('patient', 'doctor')

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
        description="Assigns a doctor to a patient. Authenticated user must own the patient.",
        request=PatientDoctorMappingSerializer,
        responses={
            201: PatientDoctorMappingSerializer,
            400: OpenApiResponse(description="Validation error or duplicate assignment"),
            403: OpenApiResponse(description="Permission denied - not patient owner"),
            404: OpenApiResponse(description="Patient or Doctor not found")
        }
    )
    def post(self, request):
        # Extract patient ID from payload
        patient_id = request.data.get('patient_id') or request.data.get('patient')
        if not patient_id:
            return Response(
                {
                    "success": False,
                    "message": "Validation error.",
                    "errors": {"patient": ["This field is required."]}
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify patient existence
        patient = Patient.objects.filter(id=patient_id).first()
        if not patient:
            return Response(
                {
                    "success": False,
                    "message": f"Patient with ID {patient_id} does not exist.",
                    "errors": {"patient": [f"Invalid pk \"{patient_id}\" - object does not exist."]}
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Enforce patient ownership authorization
        if patient.created_by != request.user and not request.user.is_staff:
            return Response(
                {
                    "success": False,
                    "message": "You do not have permission to assign doctors to this patient."
                },
                status=status.HTTP_403_FORBIDDEN
            )

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
        description="Retrieves all doctor assignments for the given patient ID. Verifies patient ownership.",
        responses={
            200: PatientDoctorMappingSerializer(many=True),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Patient not found")
        }
    )
    def get(self, request, pk):
        patient = Patient.objects.filter(id=pk).first()
        if not patient:
            # Check if pk refers to a mapping id as fallback
            mapping = PatientDoctorMapping.objects.filter(id=pk).select_related('patient', 'doctor').first()
            if mapping:
                if mapping.patient.created_by != request.user and not request.user.is_staff:
                    return Response(
                        {
                            "success": False,
                            "message": "You do not have permission to view this mapping."
                        },
                        status=status.HTTP_403_FORBIDDEN
                    )
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

        # Enforce patient ownership authorization
        if patient.created_by != request.user and not request.user.is_staff:
            return Response(
                {
                    "success": False,
                    "message": "You do not have permission to view mappings for this patient."
                },
                status=status.HTTP_403_FORBIDDEN
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
        description="Deletes the patient-doctor mapping record with the specified ID. Verifies patient ownership.",
        responses={
            200: OpenApiResponse(description="Doctor removed from patient successfully"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Mapping not found")
        }
    )
    def delete(self, request, pk):
        mapping = PatientDoctorMapping.objects.filter(id=pk).select_related('patient').first()
        if not mapping:
            return Response(
                {
                    "success": False,
                    "message": f"Mapping with ID {pk} does not exist."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # Enforce patient ownership authorization on deletion
        if mapping.patient.created_by != request.user and not request.user.is_staff:
            return Response(
                {
                    "success": False,
                    "message": "You do not have permission to remove a doctor from this patient."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        mapping.delete()
        return Response(
            {
                "success": True,
                "message": "Doctor removed from patient successfully."
            },
            status=status.HTTP_200_OK
        )
