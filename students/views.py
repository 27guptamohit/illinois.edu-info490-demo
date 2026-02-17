# Paste in: students/views.py
# New addition/changes: export_students_json()

import json

from students.models import Student, Section, Enrollment
from django.shortcuts import get_object_or_404, render
from django.views import View
from django.views.generic import ListView
from django.db.models import Count, Q

class StudentListView(ListView):
    model = Student
    template_name = "students/student_list.html"
    context_object_name = "student_rows_for_looping"   # full list (handled automatically)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        q = self.request.GET.get("q")

        if q:
            search_qs = Student.objects.filter(first_name__icontains=q)
        else:
            search_qs = None
        ctx["q"] = q
        ctx["search_results"] = search_qs

        # =========================
        # MINI AGGREGATIONS (Also check the notes on the top for why we import Q.)
        # =========================
        # A) Overall totals
        #    - Count of all students
        #    - Count of all enrollments
        ctx["total_students"] = Student.objects.count()
        ctx["total_enrollments"] = Enrollment.objects.count()

        # B) Students per Section
        #    Section <--(reverse to Student via related_name='section_related_name')
        #    We get: code, name, and how many students are linked to that section.
        ctx["students_per_section"] = (
            Section.objects
            .values("code", "name")
            .annotate(n_students=Count("section_related_name"))
            .order_by("code")
        )

        # C) Enrollments per Section (plus "active" enrollments)
        #    Section <--(reverse to Enrollment via related_name='enrollments_related_name')
        #    We count all enrollments, and also only the ones where is_active=True.
        ctx["enrollments_per_section"] = (
            Section.objects
            .values("code")
            .annotate(
                n_enrolls=Count("enrollments_related_name"),
                n_active=Count("enrollments_related_name",

                               # Here:
                               # 	•	Q(enrollments_related_name__is_active=True) means “only count enrollments where is_active is true.”
                               # 	•	Without Q, you’d count all enrollments, not just the active ones.
                               filter=Q(enrollments_related_name__is_active=True)),
            )
            .order_by("code")
        )

        # D) Students per Term
        #    'term' lives on Section; each Student belongs to a Section.
        #    Count how many students are in sections for each term.
        ctx["students_per_term"] = (
            Section.objects
            .values("term")
            .annotate(n_students=Count("section_related_name"))
            .order_by("term")
        )


        return ctx

# New class
class SectionListView(ListView):
    model = Section
    template_name = "students/section_list.html"
    context_object_name = "section_rows_for_looping"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        ctx["students_per_section"] = (
            Section.objects
            .annotate(n_students=Count("section_related_name"))
            .values("code", "name", "n_students")
            .order_by("code")
        )
        ctx["students_per_term"] = (
            Section.objects
            .values("term")
            .annotate(n_students=Count("section_related_name"))
            .order_by("term")
        )
        # Example extra (if you want it later):
        ctx["enrollments_per_section"] = (
            Section.objects
            .annotate(
                n_enrolls=Count("enrollments_related_name"),
                n_active=Count("enrollments_related_name",
                               filter=Q(enrollments_related_name__is_active=True)),
            )
            .values("code", "n_enrolls", "n_active")
            .order_by("code")
        )
        return ctx

# New class
class EnrollmentListView(ListView):
    model = Enrollment
    context_object_name = "enrollment_rows_for_looping"

# views.py
class StudentDetail(View):

    def get(self, request, primary_key):
        student = get_object_or_404(Student, pk=primary_key)
        enrollments = student.enrollments_related_name.all()

        return render(
            request,
            'students/student_detail.html',
            {
                'single_student_var_for_looping': student,
                'enrollments_var_for_looping': enrollments,
            },
        )



#===============================================================================================
# Creating charts using matplotlib

from io import BytesIO
from django.http import HttpResponse, JsonResponse

############ IMPORTANT
# Count is not one of our models.
# It’s a function (called an aggregate) that Django provides
# to perform SQL COUNT() operations inside queries.
from django.db.models import Count

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------- CHART VIEW ----------
def section_counts_chart(request):
    # Count how many students belong to each section
    # (Student.section has related_name='section_related_name')
    data = (
        Section.objects
        .annotate(student_count=Count("section_related_name"))
        .order_by("code")
    )

    labels = [sec.code for sec in data]
    counts = [sec.student_count for sec in data]

    # fig: the whiteboard, and
    # ax:  the rectangle you actually draw on.
    fig, ax = plt.subplots(figsize=(6, 3), dpi=150)

    # .bar:
    #   •	This is Matplotlib’s method for creating a bar chart.
    # 	•	It draws rectangular bars based on x values (labels) and heights (counts).
    ax.bar(labels, counts, color="#13294B")  # Illinois Blue

    ax.set_title("Students per Section", fontsize=10, color="#13294B")

    ax.set_xlabel("Section", fontsize=8)
    ax.set_ylabel("Students", fontsize=8)

    ax.tick_params(axis="x", rotation=45, labelsize=8)
    ax.tick_params(axis="y", labelsize=8)

    # tight_layout() automatically adjusts the spacing between chart elements like:
    # 	•	the axes labels (x/y),
    # 	•	the title,
    # 	•	and the plot area (bars, ticks, etc.)
    # so that nothing gets cut off when you save or display the figure.

    # Without tight_layout(), Matplotlib often leaves awkward margins
    # or chops text off the edges when saving to an image file.
    fig.tight_layout()

    # BytesIO()
    # 	•	It lets you create a temporary file-like object, but stored in memory, not on disk.
    # 	•	Think of it as a fake file drawer that lives in RAM.
    buf = BytesIO()
    fig.savefig(buf, format="png")

    plt.close(fig)
    buf.seek(0)

    return HttpResponse(buf.getvalue(), content_type="image/png")

#=======================================================
from .forms import FeedbackForm


# Define a view function that handles both GET (show form)
# and POST (process submission) requests
def feedback_view(request):

    # Check the HTTP method.
    # If the user clicked the Submit button, the browser sends a POST request.
    if request.method == "POST":

        # Create a FeedbackForm object and "bind" it to the submitted data.
        # request.POST is a dictionary of the form’s input names and values.
        form = FeedbackForm(request.POST)

        # Validate the form (runs Django’s built-in + custom field checks).
        if form.is_valid():

            # If valid, get the cleaned (validated and converted) data.
            # cleaned_data is a dictionary with safe, normalized values.
            data = form.cleaned_data

            # For demo purposes: printing the feedback to the console.
            # In a real project, you might save it, email it, or redirect.
            print("Name:", data["name"], "Feedback:", data["feedback"])

    # If the request is NOT POST (first visit or refresh), use a blank form.
    else:
        form = FeedbackForm()

    # Render the template with a context dictionary containing the form.
    # Django will send this HTML back to the user’s browser.
    # - On GET: shows an empty form.
    # - On POST (invalid): shows the form again with error messages.
    # - On POST (valid): here, still re-renders (you could redirect instead).
    return render(request, "students/feedback.html", {"form": form})



#===================================================================================================
# Import the StudentForm class that we defined in forms.py
from django.shortcuts import redirect
from .forms import StudentForm

def add_student(request):
    if request.method == "POST":
        form = StudentForm(request.POST)
        if form.is_valid():
            form.save()               # ← automatic DB save
            return redirect("student-list-url")
    else:
        form = StudentForm()
    return render(request, "students/add_student.html", {"form": form})

#===================================================================================================
from django.views.generic import CreateView
from django.urls import reverse_lazy

class StudentCreateView(CreateView):
    model = Student
    form_class = StudentForm        # or: fields = ["first_name", ...]
    template_name = "students/add_student.html"
    success_url = reverse_lazy("student-list-url")  # go back to list after save

#===================================================================================================
# New addition/changes: api_students(); api_ping(); api_json()
from django.http import JsonResponse
from django.db.models import Count, Q

# --- Tiny health check (handy when wiring tools) ---
# Difference between returning a JsonResponse vs HttpResponse
def api_ping_jsonresponse_1(request):
    return JsonResponse({"ok": True})


def api_ping_jsonresponse_2(request):
    # You must manually serialize and set headers

    # json.dumps() converts python object to JSON string
    # json.loads() converts json string to python object
    payload = json.dumps({"ok": True})

    # content_type = it describes what MIME type or type of data are we sending to the HTML page
    # MIME type stands for Multipurpose Internet Mail Extensions
    # 	•	Browsers use MIME types to decide how to display or execute content.
    # 	•	API clients use them to decide how to parse the data.
    # 	•	If you send the wrong MIME type, the browser may:
    # 	    •	Try to render JSON as HTML (ugly text dump),
    #    	•	Refuse to execute JS for security reasons,
    # 	    •	Or mis-handle file downloads.
    # MIME types are just like labels on your packages.
    # Analogically, the label tells the receiver what's inside the package (a liquid, glass, paper, solid object)
    # So when your Django server sends a response, it includes an HTTP header like this:
    # Content-type: text/html
    return JsonResponse(payload, content_type="application/json")


def api_ping_httpresponse_1(request):

    status_message = "ok"
    return HttpResponse(status_message, content_type="text/plain")

#===================================================================================================
# Main api:
def api_students(request):
    """
    GET /api/students/?q=alice
    Optional ?q= filters by first_name OR last_name OR nickname.
    """
    # First storing the user request in q
    q = (request.GET.get("q") or "").strip()

    # Now, separately loading the Student table data in qs
    qs = Student.objects.all().values("student_id", "first_name", "last_name", "nickname", "email", "section__code")

    # If q is not empty, then filter the data in qs and only show what's requested in 'q' by the user.
    if q:
        qs = Student.objects.filter(
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(nickname__icontains=q)
        ).values("student_id", "first_name", "last_name", "nickname", "email", "section__code")

    data = list(qs.order_by("last_name", "first_name"))
    return JsonResponse({"count": len(data), "results": data})

# --- Simple list of students (minimal fields) ---
def api_students(request):
    """
    GET /api/students/?q=alice
    Optional ?q= filters by first_name OR last_name OR nickname.
    """
    q = (request.GET.get("q") or "").strip()
    qs = Student.objects.all().values("student_id", "first_name", "last_name", "nickname", "email", "section__code")

    if q:
        qs = Student.objects.filter(
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(nickname__icontains=q)
        ).values("student_id", "first_name", "last_name", "nickname", "email", "section__code")

    data = list(qs.order_by("last_name", "first_name"))
    return JsonResponse({"count": len(data), "results": data})


# --- Students per section (good for bar charts) ---
def api_students_per_section(request):
    """
    GET /api/sections/students/
    Returns labels + counts arrays for quick charting.
    """
    rows = (
        Section.objects
        .annotate(n_students=Count("section_related_name"))
        .values("code", "n_students")
        .order_by("code")
    )

    labels = [r["code"] for r in rows]
    counts = [r["n_students"] for r in rows]
    return JsonResponse({"labels": labels, "counts": counts})


# --- Enrollments per section (all vs active) ---
def api_enrollments_per_section(request):
    """
    GET /api/sections/enrollments/
    """
    rows = (
        Section.objects
        .annotate(
            n_all=Count("enrollments_related_name"),
            n_active=Count("enrollments_related_name", filter=Q(enrollments_related_name__is_active=True)),
        )
        .values("code", "n_all", "n_active")
        .order_by("code")
    )
    return JsonResponse({"results": list(rows)})


#===================================================================================================
# New addition/changes: StudentsAPI(View)
# Class Based Views

class StudentsAPI(View):

    def get(self, request):
        q = (request.GET.get("q") or "").strip()
        qs = Student.objects.all()
        if q:
            qs = qs.filter(
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q) |
                Q(nickname__icontains=q)
            )
        data = list(qs.values("student_id","first_name",
                              "last_name","nickname",
                              "email","section__code")

                      .order_by("last_name","first_name"))

        return JsonResponse({"count": len(data), "results": data})

#===================================================================================================
# New addition/changes: Charting via own project's API projected data

import json
import urllib.request
from django.urls import reverse
from django.views.generic import TemplateView

# Optional: You can display the image from enrollments_chart_png() directly on a link.
# But if you want, you can also display it in another html page.
class EnrollmentsChartPage(TemplateView):
    template_name = "students/enrollments_chart.html"

def enrollments_chart_png(request):
    """
    Server-side fetch of our own JSON API (no JS in the browser),
    then build a matplotlib PNG and return it.
    Expected API shape (from our earlier example):
      {
        "rows": [
          {"code": "INFO-390-MG", "n_enrolls": 2, "n_active": 2},
          {"code": "INFO-490-MG", "n_enrolls": 1, "n_active": 1}
        ]
      }
    """
    # --- 1) DATA: fetch rows from your own JSON API -----------------------------
    # Build absolute URL to your API (works in dev too)
    # The below code is just work likes this:

    # We do not write our local machine's url as it is static and not dynamic
    # And we do not want to bother ourselves for changing the url again-and-again
    # api_url = request.build_absolute_uri(reverse("http://127.0.0.1:8000/api/sections/enrollments/"))
    # api_url = request.build_absolute_uri(reverse("http://www.illinois.edu/api/sections/enrollments/"))

    api_url = request.build_absolute_uri(reverse("api-enrollments-per-section"))
    # Output:
    # api_url = http://127.0.0.1:8000/api/sections/enrollments/
    # or
    # api_url = http://www.illinois.edu/api/sections/enrollments/

    # 	•	reverse():
    #    	•	It is equivalent to using {% url 'api-enrollments-per-section' %} in a template.

    # 	•	request.build_absolute_uri():
    #    	•	This method takes a relative path (like /api/sections/enrollments/)
    #        	and builds a full absolute URL including the current domain.

    # Pull JSON from the API
    with urllib.request.urlopen(api_url) as resp:
        payload = json.load(resp)

    # --- 2) PREPARING DATA: save columns into separate lists ------------------

    # 	•	payload is the Python dictionary you got from json.load(resp).
    # 	•	.get("rows", []) safely extracts the value associated with "rows".
    # If "rows" is missing for any reason (bad response, empty API, etc.), it defaults to an empty list ([]).

    # Right now, our data looks like a dictionary having "rows" as a single "key"
    # and all the columns as dictionaries in a list. For eg: { "a": [ {}, {}, {} ] }
    #
    ##   {
    ##   "results": [
    ##     {"code": "INFO-390-MG", "n_enrolls": 2, "n_active": 2},
    ##     {"code": "INFO-490-MG", "n_enrolls": 1, "n_active": 1}
    ##   ]
    ##   }

    # We want to extract it such that we are just left with the nested list
    ##   "results": [
    ##              {"code": "INFO-390-MG", "n_enrolls": 2, "n_active": 2},
    ##              {"code": "INFO-490-MG", "n_enrolls": 1, "n_active": 1}
    ##           ]

    # IMPORTANT:
    # If you ever get a blank visualization but everything works, it might be because of no data being given to your charts
    # It might be because the name of your table might be different.
    # For me, here it is "results"
    rows = payload.get("results", [])

    # This is a list comprehension, a compact way to loop through all rows and extract each section’s code.
    # labels = ["INFO-390-MG", "INFO-490-MG"]
    labels       = [r["code"] for r in rows]
    all_counts   = [r["n_all"] for r in rows]
    active_counts= [r["n_active"]  for r in rows]

    # --- 3) PRESENTATION: turn rows into a PNG with matplotlib ------------------
    # Plot: grouped bars (All vs Active)
    x = range(len(labels))
    width = 0.4

    fig, ax = plt.subplots(figsize=(6.5, 3.2), dpi=150)
    ax.bar([i - width/2 for i in x], all_counts,   width=width, label="All",    color="#13294B")
    ax.bar([i + width/2 for i in x], active_counts, width=width, label="Active", color="#E84A27")

    ax.set_title("Enrollments per Section")
    ax.set_ylabel("Enrollments")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.legend()
    fig.tight_layout()

    buf = BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return HttpResponse(buf.getvalue(), content_type="image/png")




# ===================================================================================================
# addition/changes: External APIs

# The requests library is a Python package that lets your Django (or any Python) code
# send HTTP requests, just like a web browser, but programmatically.

# requests lets your Python code talk to other websites or APIs.
import requests

class WeatherNow(View):
    """
    Call Open-Meteo (keyless) and return just the bits we need.
    """
    def get(self, request):

        # Step 1: Prepare parameters for the API request
        params = {
            # Champaign, IL
            "latitude": 40.1164,        # Champaign, IL latitude
            "longitude": -88.2434,      # Champaign, IL longitude
            "current_weather": True,    # Ask Open-Meteo for current conditions
        }

        try:
            # Step 2: Make a GET request to the external API
            # requests.get() contacts the Open-Meteo endpoint with the parameters above

            ##### Step 2.1:
            ##### Output: https://api.open-meteo.com/v1/forecast?latitude=40.11&longitude=-88.24&current_weather=true

            ##### Step 2.2:
            ##### timeout=5 ensures Django doesn’t hang forever if the API is slow
            output_raw_all = requests.get("https://api.open-meteo.com/v1/forecast",
                             params=params, timeout=5)

            # Step 3: Raise an error if the HTTP status code indicates a problem (e.g., 404, 500)
            output_raw_all.raise_for_status()

            # Step 4: Convert the response (which is text) into a Python dictionary
            # Return the entire raw JSON as-is for exploration
            # (This can be very large so use carefully in production!)
            output_polished_all = output_raw_all.json()

            # Step 5: Extract just the values of "current_weather" key from the JSON
            # If missing, return an empty dictionary instead of crashing
            ## Expected raw data:
            ##   {
            ##          "key 1":
            ##                  {
            #                      key 1.1: "value 1.1",
            #                      key 1.2: "value 1.2",
            #                   },
            #
            #           "current_weather":                                   <---- This is what we want
            #                   {
            #                      "time": "2025-10-12T22:45",
            #                      "interval": 900,
            #                      "temperature": 22.0,
            #                      "windspeed": 8.4,
            #                      "winddirection": 100,
            #                      "is_day": 1,
            #                      "weathercode": 0
            #                    }
            ##    }
            output_polished_cw_only = output_polished_all.get("current_weather", {})


            # Step 6: Return success response with simplified data
            # The browser (or JS frontend) can consume this JSON directly
            return JsonResponse({"ok": True, "weather": output_polished_cw_only})

        # Step 7: If *any* network or parsing error occurs, handle it gracefully
        except requests.exceptions.RequestException as e:

            # Return a 502 (Bad Gateway) response with an error message
            # This helps us diagnose connectivity or API issues
            return JsonResponse({"ok": False, "error": str(e)}, status=502)


# ===================================================================================================
# addition/changes: HTML Report

# This sample report generates similar aggregations that we did for week 3.

class ReportsView(TemplateView):
    template_name = "students/reports.html"

    def get_context_data(self, **kwargs):

        ctx = super().get_context_data(**kwargs)

        ctx["students_per_section"] = (
            Section.objects
            .values("code", "name")
            .annotate(n_students=Count("section_related_name"))
            .order_by("code")
        )


        ctx["enrolls_per_section"] = (
            Section.objects
            .annotate(
                n_all=Count("enrollments_related_name"),
                n_active=Count("enrollments_related_name",
                               filter=Q(enrollments_related_name__is_active=True)),
            )
            .values("code", "n_all", "n_active")
            .order_by("code")
        )

        return ctx


# ===================================================================================================
# addition/changes: CSV export example

import csv
from datetime import datetime


def export_students_csv(request):
    """
    Generate and download a CSV file of all students.
    Demonstrates Django’s HttpResponse + Python’s csv library.
    """

    # ---------------------------------------------------------------
    # STEP 1: Create a timestamp to make the filename unique
    # ---------------------------------------------------------------
    # datetime.now() gives the current date & time.
    # strftime() formats it safely for filenames:
    #   %Y = 4-digit year, %m = month, %d = day, %H = hour, %M = minute
    # Example output: "2025-10-12_17-35"
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")

    # Use that timestamp inside the downloadable filename
    filename = f"students_{timestamp}.csv"

    # ---------------------------------------------------------------
    # STEP 2: Prepare the HTTP response
    # ---------------------------------------------------------------
    # HttpResponse is Django’s way of sending data back to the browser. (Like I mentioned in week 8-9)
    # The 'content_type' tells the browser what kind of file it is.
    #   text/csv → browser knows it's a spreadsheet-friendly CSV file.
    response = HttpResponse(content_type="text/csv")

    # This header tells the browser: “Don’t just display this — download it!”
    # The word 'attachment' triggers a file download prompt.
    # filename="students_2025-10-12_17-35.csv" sets the default save name.
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    # ---------------------------------------------------------------
    # STEP 3: Initialize a CSV writer
    # ---------------------------------------------------------------
    # The csv.writer() function turns the HTTP response object into a
    # "file-like" object that you can write rows to.
    writer = csv.writer(response)

    # Write the header row first (column names)
    writer.writerow(["student_id", "first_name", "last_name", "email", "section_code"])

    # ---------------------------------------------------------------
    # STEP 4: Get the data from the database
    # ---------------------------------------------------------------
    # values_list() extracts tuples instead of full objects → faster and lighter.
    # select_related("section") joins Section so we can grab section__code.
    # order_by() ensures sorted output.
    rows = (
        Student.objects
        .select_related("section")
        .values_list("student_id", "first_name", "last_name", "email", "section__code")
        .order_by("last_name", "first_name")
    )

    # ---------------------------------------------------------------
    # STEP 5: Write each row to the CSV file
    # ---------------------------------------------------------------
    # Each 'row' is a tuple like (1, "Alice", "Johnson", "alice@example.com", "INFO-390-MG")
    for row in rows:
        writer.writerow(row)

    # ---------------------------------------------------------------
    # STEP 6: Return the response
    # ---------------------------------------------------------------
    # At this point, 'response' holds all CSV data in memory.
    # Django sends it back to the browser, which prompts the user
    # to download the file automatically.
    return response


# ===================================================================================================
# addition/changes: JSON export example

def export_students_json(request):
    """
    Generate and download a JSON file of all students.
    Mirrors the CSV export but returns structured JSON data.
    """

    # ---------------------------------------------------------------
    # STEP 1: Prepare data from the database
    # ---------------------------------------------------------------
    # values() returns dictionaries instead of tuples (perfect for JSON).
    # select_related("section") allows us to fetch section code efficiently.
    data = list(
        Student.objects
        .select_related("section")
        .values(
            "student_id",
            "first_name",
            "last_name",
            "email",
            "section__code"
        )
        .order_by("last_name", "first_name")
    )

    # ---------------------------------------------------------------
    # STEP 2: Build a structured JSON dictionary
    # ---------------------------------------------------------------
    # This wraps metadata + actual data.
    # Makes the file easier to read and parse later if used by APIs.
    json_content = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "record_count": len(data),
        "students": data,
    }

    # ---------------------------------------------------------------
    # STEP 3: Create the HTTP response
    # ---------------------------------------------------------------
    # JsonResponse automatically serializes the Python dictionary into JSON text.
    # It sets content-type = "application/json".
    response = JsonResponse(json_content, json_dumps_params={"indent": 2})

    # ---------------------------------------------------------------
    # STEP 4: Create a timestamp for a unique filename and activate download prompt
    # ---------------------------------------------------------------
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"students_{timestamp}.json"

    # This header tells the browser: “download this instead of just showing it”.
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    # ---------------------------------------------------------------
    # STEP 5: Return the response
    # ---------------------------------------------------------------
    return response


# =======================================================================================
# WEEK 4 : VEGA-LITE CHART DEMO
# Author: MOHIT GUPTA
# NOTE: Personal or Commercial use and sharing not permitted
# =======================================================================================

class VegaLiteAPI(TemplateView):
    template_name = "students/vega-lite-illinois.html"