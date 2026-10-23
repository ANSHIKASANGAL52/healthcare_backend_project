from django.db import models


class Doctor(models.Model):
    """
    Doctor model representing doctors in the healthcare system.
    """
    name = models.CharField(max_length=255)
    specialization = models.CharField(max_length=150)
    license_number = models.CharField(max_length=50, unique=True, db_index=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField(unique=True, db_index=True)
    experience_years = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Dr. {self.name} ({self.specialization})"
