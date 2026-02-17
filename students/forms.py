# Paste in: students/forms.py
# New class: StudentForm
# Implementation 2 begins here.

from django import forms

class FeedbackForm(forms.Form):
    name = forms.CharField(max_length=50, label="Your Name")
    email = forms.EmailField(label="Email Address")
    feedback = forms.CharField(widget=forms.Textarea, label="Comments")

# New addition/change
from students.models import Student
class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = "__all__"  # auto-create fields from model

    def clean_first_name(self):
        return self.cleaned_data["first_name"].strip()

    def clean_last_name(self):
        return self.cleaned_data["last_name"].strip()