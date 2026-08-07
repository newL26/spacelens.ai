"""
Accounts views — login, register, logout, profile, settings, password reset.
All auth-required views use LoginRequiredMixin.
"""
import logging

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView, View, TemplateView, UpdateView

from .forms import (
    AccountSettingsForm,
    LoginForm,
    ProfileUpdateForm,
    RegistrationForm,
    CustomPasswordResetForm,
    CustomSetPasswordForm,
)
from .models import UserProfile

logger = logging.getLogger(__name__)


# ── Register ───────────────────────────────────────────────────────────────────
class RegisterView(FormView):
    template_name = "accounts/register.html"
    form_class = RegistrationForm
    success_url = reverse_lazy("dashboard:index")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard:index")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(
            self.request,
            f"Welcome to SpaceLens AI, {user.first_name or user.username}! "
            "Your account has been created.",
        )
        logger.info("New user registered: %s", user.username)
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)


# ── Login ──────────────────────────────────────────────────────────────────────
class LoginView(FormView):
    template_name = "accounts/login.html"
    form_class = LoginForm
    success_url = reverse_lazy("dashboard:index")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard:index")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.get_user()
        remember_me = form.cleaned_data.get("remember_me", False)

        login(self.request, user)

        if not remember_me:
            # Session expires when browser closes
            self.request.session.set_expiry(0)

        messages.success(self.request, f"Welcome back, {user.first_name or user.username}!")
        logger.info("User logged in: %s", user.username)

        next_url = self.request.GET.get("next") or self.get_success_url()
        return redirect(next_url)

    def form_invalid(self, form):
        messages.error(self.request, "Invalid username or password. Please try again.")
        return super().form_invalid(form)


# ── Logout ─────────────────────────────────────────────────────────────────────
class LogoutView(View):
    def post(self, request, *args, **kwargs):
        username = request.user.username
        logout(request)
        messages.info(request, "You have been signed out.")
        logger.info("User logged out: %s", username)
        return redirect("core:landing")


# ── Profile ────────────────────────────────────────────────────────────────────
class ProfileView(LoginRequiredMixin, FormView):
    template_name = "accounts/profile.html"
    form_class = ProfileUpdateForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self._get_or_create_profile()
        kwargs["user"] = self.request.user
        return kwargs

    def _get_or_create_profile(self) -> UserProfile:
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        return profile

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["profile"] = self._get_or_create_profile()
        ctx["active_page"] = "profile"
        return ctx

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Your profile has been updated successfully.")
        return redirect("accounts:profile")

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        return self.form_valid(form) if False else super().form_invalid(form)


# ── Settings ───────────────────────────────────────────────────────────────────
class SettingsView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/settings.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["username_form"] = AccountSettingsForm(instance=self.request.user)
        ctx["password_form"] = PasswordChangeForm(user=self.request.user)
        ctx["active_page"] = "settings"
        return ctx

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")

        if action == "username":
            form = AccountSettingsForm(request.POST, instance=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, "Username updated successfully.")
            else:
                messages.error(request, "Could not update username — it may already be taken.")

        elif action == "password":
            form = PasswordChangeForm(user=request.user, data=request.POST)
            if form.is_valid():
                user = form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Password changed successfully.")
            else:
                for field_errors in form.errors.values():
                    for err in field_errors:
                        messages.error(request, err)

        return redirect("accounts:settings")


# ── Password Reset (Django built-in views, custom templates) ──────────────────
class CustomPasswordResetView(PasswordResetView):
    template_name = "accounts/forgot_password.html"
    form_class = CustomPasswordResetForm
    email_template_name = "accounts/email/password_reset_email.txt"
    subject_template_name = "accounts/email/password_reset_subject.txt"
    success_url = reverse_lazy("accounts:password_reset_done")


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    form_class = CustomSetPasswordForm
    success_url = reverse_lazy("accounts:password_reset_complete")


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"
