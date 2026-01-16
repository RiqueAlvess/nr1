from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_principal_view, name='principal'),
    path('unidades/', views.dashboard_unidades_view, name='unidades'),
    path('setores/', views.dashboard_setores_view, name='setores'),
    path('dimensoes/', views.dashboard_dimensoes_view, name='dimensoes'),
    path('graficos/', views.dashboard_graficos_view, name='graficos'),

    # APIs para análises avançadas
    path('api/radar/', views.api_radar_multinivel, name='api_radar'),
    path('api/distribuicao/', views.api_distribuicao_respostas, name='api_distribuicao'),
    path('api/agrupamento/', views.api_scores_agrupamento, name='api_agrupamento'),
    path('api/cargos/', views.api_cargos_disponiveis, name='api_cargos'),
    path('api/evolucao/', views.api_evolucao_temporal, name='api_evolucao'),
    path('api/matriz-nr1/', views.api_matriz_nr1, name='api_matriz_nr1'),

    # DEBUG - TEMPORÁRIO - REMOVER APÓS CORRIGIR
    path('debug-data/', views.debug_dashboard_data, name='debug_data'),
]