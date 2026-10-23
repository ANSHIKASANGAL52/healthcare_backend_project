from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .models import Patient
from .serializers import PatientSerializer
from .permissions import IsOwnerOrReadOnly


@extend_schema(tags=['Patients'])
class PatientViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Patient records.
    - POST /api/patients/ : Add a new patient (sets created_by to current user)
    - GET /api/patients/ : Retrieve all patients created by the authenticated user
    - GET /api/patients/<id>/ : Get details of a specific patient
    - PUT /api/patients/<id>/ : Update patient details
    - DELETE /api/patients/<id>/ : Delete a patient record
    """
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        # List endpoint returns only patients created by the authenticated user
        if self.action == 'list':
            return Patient.objects.filter(created_by=self.request.user)
        # Detail endpoints allow operations on patients created by user (or staff)
        return Patient.objects.all()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {
                "success": True,
                "message": "Patient created successfully.",
                "data": serializer.data
            },
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(
            {
                "success": True,
                "count": len(serializer.data),
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(
            {
                "success": True,
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(
            {
                "success": True,
                "message": "Patient updated successfully.",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {
                "success": True,
                "message": "Patient record deleted successfully."
            },
            status=status.HTTP_200_OK
        )
