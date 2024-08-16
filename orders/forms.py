from django import forms
from . models import Order
from accounts.models import UserAddress


class OrderForm(forms.ModelForm):
    order_note = forms.CharField(widget=forms.Textarea, required=False)

    class Meta:
        model = UserAddress
        fields = ['first_name', 'last_name', 'phone_number', 'email', 'address_line_1', 'address_line_2', 'city', 'state', 'country']


class AddressForm(forms.ModelForm):
    class Meta:
        model = UserAddress
        fields = ['first_name', 'last_name', 'phone_number', 'email', 'address_line_1', 'address_line_2', 'city', 'state', 'country']