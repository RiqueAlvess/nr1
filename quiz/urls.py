from django.urls import path
from . import views

app_name = 'quiz'

urlpatterns = [
    path('gerenciar/', views.gerenciar_links_view, name='gerenciar_links'),
    path('enviar/', views.enviar_links_view, name='enviar_links'),
    path('r/<str:token>/', views.responder_view, name='responder'),
    path('r/<str:token>/submit/', views.submeter_respostas_view, name='submeter'),
]