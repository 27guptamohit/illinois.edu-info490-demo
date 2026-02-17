# Register the models in students/admin.py.
# This makes a nicer display in the admin panel.

# ========================================================================

from django.contrib import admin
from .models import Section, Student, Enrollment

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display  = ("section_id", "code", "name", "term")
    search_fields = ("code", "name", "term")
    ordering      = ("section_id",)   # or ("code",)

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display  = ("student_id", "last_name", "first_name", "email", "section")
    search_fields = ("first_name", "last_name", "email", "section__code")
    list_filter   = ("section",)
    ordering      = ("last_name", "first_name")

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display  = ("enroll_id", "student", "section", "is_active", "enrolled_on")
    search_fields = ("student__first_name", "student__last_name", "section__code")
    list_filter   = ("section", "is_active")
    ordering      = ("-enroll_id",)   # newest first