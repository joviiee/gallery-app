import os
import uuid
import zipfile
from datetime import datetime
from zipfile import ZipFile

from django.contrib import admin
from django.contrib.admin import TabularInline
from django.core.files.base import ContentFile
from django.utils.html import format_html

from PIL import Image

import image_gallery.settings as settings
from image_gallery_app.models import Album, AlbumImage, Blog,AlbumRating, Feedback,Favorite, FavoriteImage
from image_gallery_app.forms import AlbumForm

class AlbumImageInline(admin.TabularInline):
    model = AlbumImage
    extra = 0
    readonly_fields = ('thumb_preview',)
    fields = ('image', 'thumb_preview', 'alt', )
    show_change_link = True

    def thumb_preview(self, obj):
        if obj.thumb:
            return format_html('<img src="{}" width="100" height="100" style="object-fit: cover;" />', obj.thumb.url)
        return "No thumbnail"
    thumb_preview.short_description = 'Preview'

@admin.register(Album)
class AlbumModelAdmin(admin.ModelAdmin):
    form = AlbumForm
    list_display = ('title', 'thumb')
    list_filter = ('created',)
    inlines = [  # <-- This was missing
        AlbumImageInline
    ]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        
        if form.cleaned_data.get('zip'):
            with zipfile.ZipFile(form.cleaned_data['zip']) as zip_file:
                for filename in sorted(zip_file.namelist()):
                    file_name = os.path.basename(filename)
                    if not file_name:
                        continue

                    data = zip_file.read(filename)
                    contentfile = ContentFile(data)

                    img = AlbumImage()
                    img.album = obj
                    img.alt = filename
                    filename = f'{obj.slug}{str(uuid.uuid4())[-13:]}.jpg'
                    img.image.save(filename, contentfile)

                    filepath = f'{settings.MEDIA_ROOT}/albums/{filename}'
                    with Image.open(filepath) as image:
                        img.width, img.height = image.size

                    img.thumb.save(f'thumb-{filename}', contentfile)
                    img.save()


@admin.register(AlbumImage)
class AlbumImageModelAdmin(admin.ModelAdmin):
    list_display = ('alt', 'album')
    list_filter = ('album', 'created')

from .models import Blog
admin.site.register(Blog)

@admin.register(AlbumRating)
class AlbumRatingAdmin(admin.ModelAdmin):
    list_display = ('album', 'user', 'rating')
    list_filter = ('album', 'rating')
    search_fields = ('user__username', 'album__title')

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'submitted_at')
    search_fields = ('name', 'email')
    readonly_fields = ('submitted_at',)

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'content_type', 'object_id')
    list_filter = ('content_type',)
    search_fields = ('user__username',)

@admin.register(FavoriteImage)
class FavoriteImageAdmin(admin.ModelAdmin):
    list_display = ('user', 'image', 'created')
    list_filter = ('created',)
    search_fields = ('user__username',)
    readonly_fields = ('created',)
