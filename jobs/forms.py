from django import forms
from jobs.models import Case

class CaseForm(forms.ModelForm):
    class Meta:
        model = Case
        fields = ["name", "description", "is_active"]