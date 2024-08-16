from django import forms
from . models import ReviewRating,Product
from django.core.exceptions import ValidationError


class ReviewForm(forms.ModelForm):
    class Meta:
        model = ReviewRating
        fields = ['subject', 'review', 'rating']

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['product_name', 'slug', 'description', 'price', 'images','stock', 'is_available', 'category', 'offer_percentage']

    def clean_offer_percentage(self):
        offer_percentage = self.cleaned_data.get('offer_percentage')
        if offer_percentage > 80:
            raise ValidationError("Offer percentage cannot exceed 80%.")
        return offer_percentage