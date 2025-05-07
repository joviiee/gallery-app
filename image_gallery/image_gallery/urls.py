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
    # path('feedback/', view.feedback_view, name='feedback'),
    path('feedback-success/', view.feedback_success, name='feedback_success'),  # Success page URL

    path('', view.gallery, name='gallery'),
    re_path(r'^favicon\.ico$', RedirectView.as_view(url='/static/icons/favicon.ico', permanent=True)),

    # Keep this last!
    path('<slug:slug>/', view.AlbumDetail.as_view(), name='album'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'image_gallery_app.views.handler404'




