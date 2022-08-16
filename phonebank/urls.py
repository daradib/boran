from django.urls import path

from phonebank import views

urlpatterns = [
    path('', views.phonebank_view, name='index'),
    path('api/voter/', views.api_view),
    path('api/voter/<slug:id>/', views.api_view),
]
