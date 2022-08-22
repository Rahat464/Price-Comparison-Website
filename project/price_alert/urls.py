from django.urls import path
from . import views

urlpatterns = [
    path('', views.pricealert, name="price_alert"),
]
