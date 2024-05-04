from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path('admin/', include('massadmin.urls')),
    path('admin/', admin.site.urls),
    path('phonebank/', include('phonebank.urls'), name='phonebank'),
]
