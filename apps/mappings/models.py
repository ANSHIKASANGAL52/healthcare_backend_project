from django.db import models


class PatientDoctorMapping(models.Model):
    """
    Model representing the assignment of a doctor to a patient.
    """
    patient = models.ForeignKey(
        'patients.Patient',
        on_delete=models.CASCADE,
        related_name='doctor_mappings'
    )
    doctor = models.ForeignKey(
        'doctors.Doctor',
        on_delete=models.CASCADE,
        related_name='patient_mappings'
    )
    assigned_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-assigned_date']
        constraints = [
            models.UniqueConstraint(
                fields=['patient', 'doctor'],
                name='unique_patient_doctor_mapping'
            )
        ]

    def __str__(self):
        return f"Patient: {self.patient.name} <-> Doctor: {self.doctor.name}"
