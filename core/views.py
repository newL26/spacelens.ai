"""
Core views — public-facing pages (no authentication required).
"""
from django.views.generic import TemplateView


class LandingPageView(TemplateView):
    template_name = "core/landing.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stats"] = {
            "models_run": "12,400+",
            "images_analysed": "98,000+",
            "accuracy": "94.7%",
            "land_classes": 10,
        }
        context["features"] = [
            {
                "icon": "bi-cpu",
                "title": "Deep Learning Classifier",
                "desc": "TensorFlow/Keras model trained on EuroSAT benchmark data classifies land-use with up to 94.7 % accuracy.",
            },
            {
                "icon": "bi-stars",
                "title": "IBM Granite Explanation",
                "desc": "IBM watsonx.ai Granite LLM turns raw probabilities into rich, human-readable environmental intelligence reports.",
            },
            {
                "icon": "bi-bar-chart-line",
                "title": "Probability Distribution",
                "desc": "Interactive chart shows the full probability spread across all 10 land-cover classes for complete transparency.",
            },
            {
                "icon": "bi-file-earmark-pdf",
                "title": "Downloadable Reports",
                "desc": "Generate a professional PDF report containing the image, prediction, Granite explanation and timestamp.",
            },
            {
                "icon": "bi-shield-check",
                "title": "Secure & Private",
                "desc": "All uploads are tied to authenticated user accounts. Images are stored privately and never shared.",
            },
            {
                "icon": "bi-clock-history",
                "title": "Prediction History",
                "desc": "Full searchable log of every prediction with pagination, delete and re-download controls.",
            },
        ]
        context["land_classes"] = [
            {"name": "Annual Crop",          "icon": "bi-tree",            "color": "#22c55e"},
            {"name": "Forest",               "icon": "bi-tree-fill",       "color": "#16a34a"},
            {"name": "Herbaceous Veg.",      "icon": "bi-flower1",         "color": "#84cc16"},
            {"name": "Highway",              "icon": "bi-signpost-2",      "color": "#94a3b8"},
            {"name": "Industrial",           "icon": "bi-building",        "color": "#f59e0b"},
            {"name": "Pasture",              "icon": "bi-align-bottom",    "color": "#a3e635"},
            {"name": "Permanent Crop",       "icon": "bi-flower2",         "color": "#10b981"},
            {"name": "Residential",          "icon": "bi-houses",          "color": "#6366f1"},
            {"name": "River",                "icon": "bi-water",           "color": "#38bdf8"},
            {"name": "Sea / Lake",           "icon": "bi-tsunami",         "color": "#0ea5e9"},
        ]
        return context
