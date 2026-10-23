from django.contrib import admin
from .models import PatientDoctorMapping


@admin.register(PatientDoctorMapping)
class PatientDoctorMappingAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'doctor', 'assigned_date')
    list_filter = ('assigned_date',)
    search_fields = ('patient__name', 'doctor__name')
    ordering = ('-assigned_date',)
