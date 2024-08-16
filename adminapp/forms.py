# orders/forms.py
from django import forms
from carts.models import Coupon
from django.forms.widgets import DateTimeInput

class DateRangeForm(forms.Form):
    CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        ('custom', 'Custom Date Range'),
    ]
    period = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect)
    start_date = forms.DateField(required=False, widget=forms.TextInput(attrs={'type': 'date'}))
    end_date = forms.DateField(required=False, widget=forms.TextInput(attrs={'type': 'date'}))


class CouponForm(forms.ModelForm):
    valid_from = forms.DateTimeField(widget=DateTimeInput(attrs={
        'class': 'form-control datetimepicker-input',
        'data-target': '#datetimepicker1'
    }))
    valid_to = forms.DateTimeField(widget=DateTimeInput(attrs={
        'class': 'form-control datetimepicker-input',
        'data-target': '#datetimepicker2'
    }))

    class Meta:
        model = Coupon
        fields = ['code', 'discount', 'valid_from', 'valid_to', 'active']


