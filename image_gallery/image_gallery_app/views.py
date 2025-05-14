#!/usr/bin/env python
# -*- coding: utf-8 -*-  
import os
import zipfile
import uuid
from io import BytesIO
from django.shortcuts import render,redirect,get_object_or_404
from django.http import HttpRequest, JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import DetailView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, logout, authenticate,get_user
from image_gallery_app.models import Album, AlbumImage ,AlbumRating, FavoriteImage
from .forms import SignupForm, LoginForm, FeedbackForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.text import slugify
from django.core.files.base import ContentFile
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.mixins import LoginRequiredMixin


from PIL import Image

from .forms import AlbumForm

from image_gallery_app.models import Album, AlbumImage, Blog, Favorite


def logout_view(request):
    logout(request)
    return redirect('/')

def gallery(request):
    # Fetch albums where is_visible is True, ordered by 'created' in descending order
    albums_list = Album.objects.filter(is_visible=True).order_by('-created')
    print(f"Found {albums_list.count()} visible albums")  # Debug line
    user_favorites = []

    if request.user.is_authenticated:
        album_type = ContentType.objects.get_for_model(Album)
        user_favorites = Favorite.objects.filter(
            user=request.user,
            content_type=album_type
        ).values_list('object_id', flat=True)

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
            form.save() 
            # Optionally, save the form data to a model or send an email
            # Redirect to the feedback success page after form submission
            return redirect('feedback_success')  # Redirect to the success page

    else:
        form = FeedbackForm()  # Display an empty form on GET request

    # Render the gallery template with albums and form context
    return render(request, 'gallery.html', {
        'albums': albums,
        'form': form,
        'user_favorites': user_favorites
    })


class AlbumDetail(LoginRequiredMixin, DetailView):
    model = Album
    template_name = 'image_gallery_app/album_detail.html'
    context_object_name = 'album'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        album = self.get_object()

        # Images
        context['images'] = AlbumImage.objects.filter(album=album)

        # Feedback Form
        context['form'] = FeedbackForm()

        # User Rating
        user = self.request.user
        user_rating = None
        if user.is_authenticated:
            user_rating = AlbumRating.objects.filter(user=user, album=album).first()
            favorite_image_ids = FavoriteImage.objects.filter(
                user=self.request.user,
                image__in=album.albumimage_set.all()
            ).values_list('image_id', flat=True)
            context['favorite_image_ids'] = set(favorite_image_ids)
        context['user_rating'] = user_rating

        # Average Rating
        context['average_rating'] = album.average_rating()
        context["rating_range"] = [5, 4, 3, 2, 1]

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if 'rating' in request.POST:
            # Star rating form submitted
            rating = int(request.POST.get('rating'))
            AlbumRating.objects.update_or_create(
                user=request.user,
                album=self.object,
                defaults={'rating': rating}
            )
            return redirect(self.request.path_info)  # refresh page
        if 'favorite_image' in request.POST:
            image_id = request.POST.get('favorite_image')
            try:
                image = AlbumImage.objects.get(id=image_id)
                fav, created = FavoriteImage.objects.get_or_create(
                    user=request.user,
                    image=image
                )
                if not created:
                    fav.delete()
                return JsonResponse({'status': 'success'})
            except AlbumImage.DoesNotExist:
                return JsonResponse({'status': 'error'}, status=404)

        else:
            # Feedback form submitted
            form = FeedbackForm(request.POST)
            if form.is_valid():
                form.save() 
                # Save or process the feedback as needed
                return redirect('feedback_success')
            
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



@login_required
def create_album_view(request):
    if request.method == 'POST':
        form = AlbumForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                album = form.save(commit=False)
                album.save()  # This triggers the slug generation
                
                if zip_file := form.cleaned_data.get('zip'):
                    try:
                        with zipfile.ZipFile(zip_file) as archive:
                            for entry in sorted(archive.namelist()):
                                if entry.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                                    file_data = archive.read(entry)
                                    filename = os.path.basename(entry)
                                    
                                    with BytesIO(file_data) as buffer:
                                        img = AlbumImage(album=album, alt=filename)
                                        img.image.save(filename, ContentFile(file_data))
                                        
                                        image = Image.open(buffer)
                                        img.width, img.height = image.size
                                        
                                        thumb_buffer = BytesIO()
                                        image.thumbnail((300, 300))
                                        image.save(thumb_buffer, format='JPEG', quality=90)
                                        img.thumb.save(f"thumb_{filename}", ContentFile(thumb_buffer.getvalue()))
                                        img.save()
                    except zipfile.BadZipFile:
                        messages.error(request, "Invalid ZIP file")
                        return redirect('create_album')

                return redirect('album', slug=album.slug)
            
            except Exception as e:
                messages.error(request, f"Error creating album: {str(e)}")
                return redirect('create_album')
    else:
        form = AlbumForm()
    return render(request, 'create_album.html', {'form': form})
from .models import Blog

def blog_view(request):
    blogs = Blog.objects.all()

    user_favorites = []
    if request.user.is_authenticated:
        blog_type = ContentType.objects.get_for_model(Blog)
        user_favorites = Favorite.objects.filter(
            user=request.user,
            content_type=blog_type
        ).values_list('object_id', flat=True)  # returns list of favorited blog IDs

    # Handle form submission (POST)
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            form.save() 
            # Optionally, save the form data to a model or send an email
            # Redirect to the feedback success page after form submission
            return redirect('feedback_success')  # Redirect to the success page

    else:
        form = FeedbackForm()  # Display an empty form on GET request
    return render(request, 'blog.html', {'blogs': blogs,"form":form,'user_favorites': user_favorites})


@login_required
def toggle_favorite(request, item_type, item_id):
    # Map string to model
    model_map = {
        'album': Album,
        'blog': Blog,
    }

    model = model_map.get(item_type)
    if not model:
        return redirect('home')

    item = get_object_or_404(model, id=item_id)
    content_type = ContentType.objects.get_for_model(model)

    fav, created = Favorite.objects.get_or_create(
        user=request.user,
        content_type=content_type,
        object_id=item.id
    )

    if not created:
        fav.delete()

    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def favorites_view(request):
    album_content_type = ContentType.objects.get_for_model(Album)

    # Fetch the favorite albums for the logged-in user
    fav_albums = Album.objects.filter(
        id__in=Favorite.objects.filter(user=request.user, content_type=album_content_type).values('object_id')
    )

    # Fetch favorite blogs in a similar way (if applicable)
    fav_blogs = Blog.objects.filter(
        id__in=Favorite.objects.filter(user=request.user, content_type=ContentType.objects.get_for_model(Blog)).values('object_id')
    )

    fav_images = AlbumImage.objects.filter(
        id__in=FavoriteImage.objects.filter(
            user=request.user
        ).values_list('image_id', flat=True)
    ).select_related('album')

    # Handle form submission (POST)
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            form.save() 
            # Optionally, save the form data to a model or send an email
            # Redirect to the feedback success page after form submission
            return redirect('feedback_success')  # Redirect to the success page

    else:
        form = FeedbackForm()  # Display an empty form on GET request

    return render(request, 'favorites.html', {
        'fav_albums': fav_albums,
        'fav_blogs': fav_blogs,
        'fav_images': fav_images,
        "form":form
    })

def blog_detail(request, slug):
    blog = get_object_or_404(Blog, slug=slug)
    # Handle form submission (POST)
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            form.save() 
            # Optionally, save the form data to a model or send an email
            # Redirect to the feedback success page after form submission
            return redirect('feedback_success')  # Redirect to the success page

    else:
        form = FeedbackForm()  # Display an empty form on GET request
    return render(request, 'blog_detail.html', {'blog': blog,"form":form})


@login_required
def toggle_favorite_image(request, image_id):
    image = get_object_or_404(AlbumImage, id=image_id)
    
    # Get or create favorite
    fav, created = FavoriteImage.objects.get_or_create(
        user=request.user,
        image=image
    )
    
    # If it already existed, delete it (toggle)
    if not created:
        fav.delete()
    
    # Redirect back to the album page
    return redirect('album', slug=image.album.slug)