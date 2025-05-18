from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Author, Quote, Tag

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class AuthorForm(forms.ModelForm):
    class Meta:
        model = Author
        fields = ['fullname', 'born_date', 'born_location', 'description']

class QuoteForm(forms.ModelForm):
    tags = forms.CharField(help_text="Enter tags separated by commas")

    class Meta:
        model = Quote
        fields = ['quote', 'author', 'tags']

    def clean_tags(self):
        tags = self.cleaned_data['tags'].split(',')
        return [tag.strip() for tag in tags if tag.strip()]