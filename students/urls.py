# Paste in: students/urls.py
# New addition/changes: export_students_json()

from django.urls import path
from . import views  # single import: use views.X everywhere
from .views import StudentCreateView, StudentsAPI, EnrollmentsChartPage, enrollments_chart_png, WeatherNow, ReportsView, \
    export_students_csv, export_students_json, VegaLiteAPI

urlpatterns = [
    path("student/", views.StudentListView.as_view(), name="student-list-url"),
    path("section/", views.SectionListView.as_view(), name="section-list-url"),
    path("enrollment/", views.EnrollmentListView.as_view(), name="enrollment-list-url"),

    path("student/<int:primary_key>/", views.StudentDetail.as_view(),
         name="student-detail-url"),

    # Chart image endpoint
    path("charts/sections.png", views.section_counts_chart, name="chart-sections"),

    path("feedback/", views.feedback_view, name="feedback-url"),
    # New addition/change
    # Feedback form Student model
    path("function-add-student/", views.add_student, name="function-add-student-url"),

    path("class-add-student/", StudentCreateView.as_view(), name="class-add-student-url"),

    # Test JSON EndPoints (Week 3)
    path("api/ping-json1/", views.api_ping_jsonresponse_1, name="api-ping-json"),
    path("api/ping-json2/", views.api_ping_jsonresponse_2, name="api-ping-json2"),
    path("api/ping-http1/", views.api_ping_httpresponse_1, name="api-ping-http1"),


    path("api/function-students/", views.api_students, name="api-students"),
    path("api/sections/students/", views.api_students_per_section, name="api-students-per-section"),
    path("api/sections/enrollments/", views.api_enrollments_per_section, name="api-enrollments-per-section"),

    # Class based views: JSON endpoints
    path("api/class-students/", StudentsAPI.as_view(), name="api-students"),

    # Charting from the self-projected JSON/API data
    path("charts/enrollments/", EnrollmentsChartPage.as_view(), name="enrollments-chart-page"),
    path("charts/enrollments.png", enrollments_chart_png, name="enrollments-chart-png"),

    path("api/weather/", WeatherNow.as_view(), name="api-weather"),

    path("reports/", ReportsView.as_view(), name="export-reports-url"),

    path("export/students.csv", export_students_csv, name="export-students-csv"),

    path("export/students.json", export_students_json, name="export-students-json"),

    # -----------------------------------------------------------------------------------
    # New addition/changes: VEGA-LITE CHARTS DEMO
    # -----------------------------------------------------------------------------------
    path("charts/vega-lite/", VegaLiteAPI.as_view(), name="chart-vega-lite"),

]