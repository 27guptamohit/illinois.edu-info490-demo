# Changes in: illinois/urls.py
# We are now adding a link for the home page.

from django.contrib import admin
from django.urls import path, include
from illinois.views import redirect_root_view


urlpatterns = [
    path('', redirect_root_view),           # This says that if a webpage with no pattern opens, load the page sent by redirect_root_view()

    path('admin/', admin.site.urls),
    path('', include('students.urls')),     # This says that include all the urls here in the students/urls.py
]
