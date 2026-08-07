"""
Prediction URL patterns.
"""
from django.urls import path
from prediction.views import (
    PredictView,
    PredictionResultView,
    PredictionHistoryView,
    DeletePredictionView,
)

app_name = "prediction"

urlpatterns = [
    path("",                        PredictView.as_view(),            name="predict"),
    path("result/<int:pk>/",        PredictionResultView.as_view(),   name="result"),
    path("history/",                PredictionHistoryView.as_view(),  name="history"),
    path("delete/<int:pk>/",        DeletePredictionView.as_view(),   name="delete"),
]
