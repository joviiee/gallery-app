from django.urls import path, re_path
from django.contrib.auth import views
from django.views.generic.base import RedirectView

from django.conf import settings
from django.conf.urls.static import static

import image_gallery_app.forms as form
import image_gallery_app.views as view

from django.conf.urls import include
from django.contrib import admin
admin.autodiscover()

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/login/', view.custom_login, name='login'),
    path('accounts/signup/', view.custom_signup, name='signup'),
    path('logout/', view.logout_view, name='logout'),
    path('blog/', view.blog_view, name='blog'),
    path('blog/<slug:slug>/', view.blog_detail, name='blog_detail'),
    path('create_album/', view.create_album_view, name='create_album'),
    path('favourites/', view.favorites_view, name='favourites'),
    path('favorite/<str:item_type>/<int:item_id>/', view.toggle_favorite, name='toggle_favorite'),
    path('feedback-success/', view.feedback_success, name='feedback_success'),  # Success page URL
    path('toggle-favorite/image/<int:image_id>/', view.toggle_favorite_image, name='toggle_favorite_image'),

    path('', view.gallery, name='gallery'),
    re_path(r'^favicon\.ico$', RedirectView.as_view(url='/static/icons/favicon.ico', permanent=True)),

    # Keep this last!
    path('albums/<slug:slug>/', view.AlbumDetail.as_view(), name='album'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'image_gallery_app.views.handler404'




