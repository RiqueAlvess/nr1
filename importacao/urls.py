from django.urls import path
from . import views

app_name = 'importacao'

urlpatterns = [
    path('', views.importacao_view, name='importacao'),
    path('upload/', views.upload_csv_view, name='upload_csv'),
    path('processo/<uuid:processo_id>/', views.processo_detalhe_view, name='processo_detalhe'),
]