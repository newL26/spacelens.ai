"""
Accounts forms — registration, login, profile update, password change.
"""
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import (
    UserCreationForm,
    AuthenticationForm,
    PasswordResetForm,
    SetPasswordForm,
)
from .models import UserProfile


# ── Shared widget helper ───────────────────────────────────────────────────────
def _text_widget(placeholder="", input_type="text", extra_classes=""):
    classes = f"sl-form-control {extra_classes}".strip()
    return forms.TextInput(attrs={"placeholder": placeholder, "class": classes, "type": input_type})


def _password_widget(placeholder=""):
    return forms.PasswordInput(
        attrs={"placeholder": placeholder, "class": "sl-form-control", "autocomplete": "current-password"},
        render_value=False,
    )


def _email_widget(placeholder=""):
    return forms.EmailInput(attrs={"placeholder": placeholder, "class": "sl-form-control"})


# ── Registration ───────────────────────────────────────────────────────────────
class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=_text_widget("First name"),
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=_text_widget("Last name"),
    )
    email = forms.EmailField(
        required=True,
        widget=_email_widget("you@example.com"),
    )
    password1 = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"placeholder": "Create a password", "class": "sl-form-control", "autocomplete": "new-password"},
        ),
    )
    password2 = forms.CharField(
        label="Confirm Password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"placeholder": "Repeat password", "class": "sl-form-control", "autocomplete": "new-password"},
        ),
    )

    class Meta:
        model = User
        fields = ("first_name", "last_name", "username", "email", "password1", "password2")
        widgets = {
            "username": _text_widget("Username"),
        }

    def clean_email(self):
        email = self.cleaned_data.get("email", "").lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
        return user


# ── Login ──────────────────────────────────────────────────────────────────────
class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=_text_widget("Username or email"),
    )
    password = forms.CharField(
        strip=False,
        widget=_password_widget("Password"),
    )
    remember_me = forms.BooleanField(required=False, initial=False)


# ── Password Reset ────────────────────────────────────────────────────────────
class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        widget=_email_widget("Registered email address"),
    )


class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label="New Password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"placeholder": "New password", "class": "sl-form-control", "autocomplete": "new-password"},
        ),
    )
    new_password2 = forms.CharField(
        label="Confirm New Password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"placeholder": "Repeat new password", "class": "sl-form-control", "autocomplete": "new-password"},
        ),
    )


# ── Profile Update ────────────────────────────────────────────────────────────
class ProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=_text_widget("First name"),
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=_text_widget("Last name"),
    )
    email = forms.EmailField(
        required=True,
        widget=_email_widget("Email address"),
    )

    class Meta:
        model = UserProfile
        fields = ("avatar", "organisation", "bio", "location", "website")
        widgets = {
            "organisation": _text_widget("Your organisation or institution"),
            "bio": forms.Textarea(
                attrs={
                    "placeholder": "Short bio…",
                    "class": "sl-form-control",
                    "rows": 3,
                }
            ),
            "location": _text_widget("City, Country"),
            "website": _text_widget("https://", input_type="url"),
            "avatar": forms.FileInput(attrs={"class": "sl-form-control", "accept": "image/*"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._user = user
        if user:
            self.fields["first_name"].initial = user.first_name
            self.fields["last_name"].initial = user.last_name
            self.fields["email"].initial = user.email

    def clean_email(self):
        email = self.cleaned_data.get("email", "").lower().strip()
        qs = User.objects.filter(email__iexact=email)
        if self._user:
            qs = qs.exclude(pk=self._user.pk)
        if qs.exists():
            raise forms.ValidationError("This email is already in use by another account.")
        return email

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self._user:
            self._user.first_name = self.cleaned_data.get("first_name", "")
            self._user.last_name = self.cleaned_data.get("last_name", "")
            self._user.email = self.cleaned_data["email"]
            if commit:
                self._user.save()
        if commit:
            profile.save()
        return profile


# ── Account Settings (username / password change) ─────────────────────────────
class AccountSettingsForm(forms.ModelForm):
    """Lets the user change their username."""

    class Meta:
        model = User
        fields = ("username",)
        widgets = {
            "username": _text_widget("Username"),
        }
