from django import forms

from common.constants import PlanCode


class CheckoutPlanForm(forms.Form):
    plan = forms.ChoiceField(choices=PlanCode.choices)


class ApiKeyCreateForm(forms.Form):
    name = forms.CharField(max_length=255)
