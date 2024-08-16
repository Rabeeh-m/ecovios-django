from django import forms
from accounts.models import UserAddress

class SelectAddressForm(forms.Form):
    selected_address = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Select Address",
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(SelectAddressForm, self).__init__(*args, **kwargs)
        self.fields['selected_address'].queryset = UserAddress.objects.filter(user=user)
