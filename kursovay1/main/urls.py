from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.index, name='index'),
    path('main/', views.main, name='main'),
    path('invoices/', views.invoices, name='invoices'),
    path('report/', views.report, name='report')
]

