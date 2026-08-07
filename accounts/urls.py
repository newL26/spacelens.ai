"""
Accounts URL patterns.
"""
from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    # Auth
    path("register/",           views.RegisterView.as_view(),                    name="register"),
    path("login/",              views.LoginView.as_view(),                        name="login"),
    path("logout/",             views.LogoutView.as_view(),                       name="logout"),

    # Profile & Settings
    path("profile/",            views.ProfileView.as_view(),                      name="profile"),
    path("settings/",           views.SettingsView.as_view(),                     name="settings"),

    # Password Reset
    path("password-reset/",           views.CustomPasswordResetView.as_view(),         name="password_reset"),
    path("password-reset/done/",      views.CustomPasswordResetDoneView.as_view(),     name="password_reset_done"),
    path("password-reset/confirm/<uidb64>/<token>/",
                                      views.CustomPasswordResetConfirmView.as_view(),  name="password_reset_confirm"),
    path("password-reset/complete/",  views.CustomPasswordResetCompleteView.as_view(), name="password_reset_complete"),
]
