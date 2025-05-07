#!/usr/bin/env python
# -*- coding: utf-8 -*-  
from django.shortcuts import render,redirect
from django.http import HttpRequest
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import DetailView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, logout, authenticate
from image_gallery_app.models import Album, AlbumImage
from .forms import SignupForm, LoginForm, FeedbackForm
from django.contrib import messages

from image_gallery_app.models import Album, AlbumImage

def logout_view(request):
    logout(request)
    return redirect('/')

def gallery(request):
    # Fetch albums where is_visible is True, ordered by 'created' in descending order
    albums_list = Album.objects.filter(is_visible=True).order_by('-created')
    
    # Set up pagination: 10 albums per page
    paginator = Paginator(albums_list, 10)
    page = request.GET.get('page')
    
    try:
        albums = paginator.page(page)
    except PageNotAnInteger:
        albums = paginator.page(1)  # If page is not an integer, deliver first page.
    except EmptyPage:
        albums = paginator.page(paginator.num_pages)  # If page is out of range, deliver last page of results.

    # Handle form submission (POST)
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            # Optionally, save the form data to a model or send an email
            # Redirect to the feedback success page after form submission
            return redirect('feedback_success')  # Redirect to the success page

    else:
        form = FeedbackForm()  # Display an empty form on GET request

    # Render the gallery template with albums and form context
    return render(request, 'gallery.html', {
        'albums': albums,
        'form': form
    })
class AlbumDetail(DetailView):
     model = Album
     emplate_name = 'image_gallery_app/album_detail.html'

     def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(AlbumDetail, self).get_context_data(**kwargs)
        # Add in a QuerySet of all the images
        context['images'] = AlbumImage.objects.filter(album=self.object.id)
        context['form'] = FeedbackForm()
        return context
     
     def post(self, request, *args, **kwargs):
        form = FeedbackForm(request.POST)
        if form.is_valid():
            # Optionally save feedback or perform additional actions
            # Redirect to the feedback success page after successful form submission
            return redirect('feedback_success')  # Redirect to the success page

        # If form is invalid, re-render the page with the form and errors
        context = self.get_context_data(**kwargs)
        context['form'] = form
        return self.render_to_response(context)
     
def custom_signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/')  # Redirect to homepage or dashboard
        else:
            print("form invalid******************************************************************************************")
            print("Form errors:", form.errors)
    else:
        form = SignupForm()
    return render(request, 'registration/signup.html', {'form': form})

def custom_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password']
            )
            if user is not None:
                login(request, user)
                return redirect('/')
            else:
                messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()
    return render(request, 'registration/login.html', {'form': form})

def feedback_success(request):
    return render(request, 'feedback/feedback_success.html') 

def handler404(request, exception):
    assert isinstance(request, HttpRequest)
    return render(request, 'handler404.html', None, None, 404)