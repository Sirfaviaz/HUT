from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    
    class Meta:
        model = Product
        fields = ['name_english', 'name_arabic', 'description_english', 'description_arabic', 'price', 'image']
