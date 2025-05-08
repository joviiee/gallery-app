#!/usr/bin/env python
# -*- coding: utf-8 -*- 
from django import forms
from image_gallery_app.models import Album, Feedback
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class AlbumForm(forms.ModelForm):
    zip = forms.FileField(required=False, help_text="Optional .zip file of images to add to this album")
    class Meta:
        model = Album
        exclude = ['slug', 'created', 'modified']

class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['name', 'email', "message"]
        widgets = {
    'message': forms.Textarea(attrs={'class': 'message-box'})
}
        

class AlbumRatingForm(forms.Form):
    rating = forms.ChoiceField(
        choices=[(i, str(i)) for i in range(1, 6)],
        widget=forms.RadioSelect
    )