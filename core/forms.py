from django import forms
from .models import Dataset

class UploadForm(forms.ModelForm):
    class Meta:
        model = Dataset
        fields = ['file']
