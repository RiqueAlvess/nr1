from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_principal_view, name='principal'),
    path('unidades/', views.dashboard_unidades_view, name='unidades'),
    path('setores/', views.dashboard_setores_view, name='setores'),
    path('dimensoes/', views.dashboard_dimensoes_view, name='dimensoes'),
]