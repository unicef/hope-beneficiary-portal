from django import forms

from hope_portal.modules.hope.models import Household


class StartForm(forms.Form):
    registration_number = forms.CharField(widget=forms.TextInput(attrs={"class": "input w-full"}))

    def clean_registration_number(self) -> Household:
        try:
            return Household.objects.get(detail_id=self.cleaned_data["registration_number"])
        except Household.DoesNotExist:
            raise forms.ValidationError("Registration number not found") from None
