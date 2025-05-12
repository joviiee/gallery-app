#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import uuid
import zipfile
import image_gallery.settings as settings
from datetime import datetime
from zipfile import ZipFile

from django.contrib import admin
from django.core.files.base import ContentFile

from PIL import Image

from image_gallery_app.models import Album, AlbumImage
from image_gallery_app.forms import AlbumForm

@admin.register(Album)
class AlbumModelAdmin(admin.ModelAdmin):
    form = AlbumForm
    # Remove prepopulated_fields since we're auto-generating
    list_display = ('title', 'thumb')
    list_filter = ('created',)

    def save_model(self, request, obj, form, change):
        # Let the model's save() handle slug generation and modified date
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

# In case image should be removed from album.
@admin.register(AlbumImage)
class AlbumImageModelAdmin(admin.ModelAdmin):
    list_display = ('alt', 'album')
    list_filter = ('album', 'created')

from .models import Blog

admin.site.register(Blog)