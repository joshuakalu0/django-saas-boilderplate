from django import forms
from django.utils.text import slugify

from common.constants import MembershipRole
from workspace.models import Project


class InvitationForm(forms.Form):
    email = forms.EmailField()
    role = forms.ChoiceField(choices=MembershipRole.choices)


class MemberRoleForm(forms.Form):
    role = forms.ChoiceField(choices=MembershipRole.choices)


class OwnershipTransferForm(forms.Form):
    user_id = forms.IntegerField()


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ("name", "description")

    def save(self, commit=True, created_by_id=None):
        project = super().save(commit=False)
        project.slug = slugify(project.name)
        if created_by_id is not None:
            project.created_by_id = created_by_id
        if commit:
            project.save()
        return project
