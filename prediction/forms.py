"""
Prediction upload form.
"""
from django import forms
from .models import Prediction
from .utils import validate_satellite_image


class PredictionForm(forms.ModelForm):
    image = forms.ImageField(
        label="Satellite Image",
        validators=[validate_satellite_image],
        widget=forms.FileInput(attrs={
            "id": "id_image",
            "accept": ".jpg,.jpeg,.png,.tif,.tiff",
            "class": "d-none",
        }),
        error_messages={
            "required": "Please select a satellite image to analyse.",
            "invalid_image": "The uploaded file is not a valid image.",
        },
    )

    class Meta:
        model = Prediction
        fields = ("image",)
