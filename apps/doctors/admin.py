from django.contrib import admin
from .models import Doctor


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'specialization', 'license_number', 'phone', 'email', 'experience_years', 'created_at')
    list_filter = ('specialization', 'created_at')
    search_fields = ('name', 'license_number', 'email', 'specialization')
    ordering = ('-created_at',)
