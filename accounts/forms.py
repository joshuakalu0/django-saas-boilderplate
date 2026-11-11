from django import forms
from django.contrib.auth import authenticate

from accounts.models import User
from common.utils import slugify_schema_name


class RegistrationForm(forms.Form):
    name = forms.CharField(max_length=255)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput())
    organization_name = forms.CharField(max_length=255)
    organization_slug = forms.CharField(max_length=255, required=False)

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("That email address is already in use.")
        return email

    def clean_organization_slug(self):
        slug = self.cleaned_data.get("organization_slug") or self.cleaned_data.get(
            "organization_name", ""
        )
        try:
            return slugify_schema_name(slug).replace("_", "-")
        except ValueError as exc:
            raise forms.ValidationError(str(exc)) from exc


class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput())

    def clean(self):
        cleaned = super().clean()
        user = authenticate(
            username=cleaned.get("email", "").strip().lower(),
            password=cleaned.get("password", ""),
        )
        if not user:
            raise forms.ValidationError("Invalid email or password.")
        cleaned["user"] = user
        return cleaned


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField()


class PasswordResetConfirmForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput())
    password_confirm = forms.CharField(widget=forms.PasswordInput())

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password") != cleaned.get("password_confirm"):
            raise forms.ValidationError("Passwords do not match.")
        return cleaned


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("name", "avatar")
