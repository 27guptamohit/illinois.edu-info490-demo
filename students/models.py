# Paste here: students/models.py
# New changes: Added get_absolute_url method in the Student model.

from django.db import models
from django.urls import reverse


# ---------- Parent table ----------
class Section(models.Model):
    section_id    = models.AutoField(primary_key=True)

    code  = models.CharField(max_length=10, unique=True)   # e.g. "CS101-A"
    name  = models.CharField(max_length=60)                # e.g. "Intro to CS - A"
    term  = models.CharField(max_length=16, blank=True)    # e.g. "Fall 2025"

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} ({self.term or '—'})"


# ---------- Child table ----------
class Student(models.Model):
    student_id         = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=45)
    last_name  = models.CharField(max_length=45)
    nickname   = models.CharField(max_length=45, blank=True, default="")
    email      = models.EmailField(unique=True)
    section = models.ForeignKey(
        Section,
        on_delete=models.PROTECT,   # start safe; try changing this to CASCADE after class
        related_name="section_related_name",          # I changed this name in week 5
    )

    ####################################################################################################################################
    # NEW:
    def get_absolute_url(self):
        return reverse('student-detail-url',     # This is the same url pattern that we are using for student_details.html in student/urls.py
                       kwargs={'primary_key': self.pk}
                       )
    ####################################################################################################################################


    class Meta:
        ordering = ["last_name", "first_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["first_name", "last_name", "section"],
                name="uniq_student_name_in_section",
            )
        ]

    def __str__(self):
        base = f"{self.last_name}, {self.first_name}"
        return f"{base} ({self.nickname})" if self.nickname else base


# ---------- Association table (join table) ----------
class Enrollment(models.Model):
    enroll_id       = models.AutoField(primary_key=True)
    student  = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,   # if a student is removed, remove their enrollments
        related_name="enrollments_related_name"     # I changed this name in week 5
    )


    section  = models.ForeignKey(
        Section,
        on_delete=models.PROTECT,   # protects Sections with enrollments; demo flip to CASCADE to compare
        related_name="enrollments_related_name"     # I changed this name in week 5
    )


    enrolled_on = models.DateField(auto_now_add=True)
    is_active   = models.BooleanField(default=True)

    class Meta:
        ordering = ["-enroll_id", "student__last_name", "student__first_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "section"],
                name="uniq_enrollment_per_student_per_section",
            )
        ]

    def __str__(self):
        return f"Enrollment(student={self.student_id}, section={self.section_id})"
