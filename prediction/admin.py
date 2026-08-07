from django.contrib import admin
from .models import Prediction


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "predicted_class", "confidence", "created_at")
    list_filter = ("predicted_class", "created_at")
    search_fields = ("user__username", "predicted_class")
    readonly_fields = ("probabilities", "granite_response", "created_at")
    raw_id_fields = ("user",)
