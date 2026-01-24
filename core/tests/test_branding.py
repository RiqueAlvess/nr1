"""Testes para sistema de Branding White Label."""
from django.test import TestCase, RequestFactory, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User

from core.models import Branding


class BrandingModelTest(TestCase):
    """Testes do model Branding."""

    def test_singleton_pattern(self):
        """Testa que so pode existir 1 registro."""
        branding1 = Branding.get_instance()
        branding2 = Branding.get_instance()

        self.assertEqual(branding1.id, branding2.id)
        self.assertEqual(Branding.objects.count(), 1)

    def test_default_values(self):
        """Testa valores padrao."""
        branding = Branding.get_instance()

        self.assertEqual(branding.nome_sistema, "Vivamente360")
        self.assertEqual(branding.nome_empresa, "3S Dev")
        self.assertEqual(branding.cor_primaria, "#1EEB88")
        self.assertEqual(branding.cor_secundaria, "#0F3D52")
        self.assertEqual(branding.cor_accent, "#6EDBC1")
        self.assertTrue(branding.ativo)

    def test_get_logo_url_fallback(self):
        """Testa fallback quando logo nao existe."""
        branding = Branding.get_instance()
        branding.logo = None
        branding.save()

        url = branding.get_logo_url()

        self.assertEqual(url, "/static/public/icone.png")

    def test_get_logo_login_url_fallback(self):
        """Testa fallback quando logo_login nao existe."""
        branding = Branding.get_instance()
        branding.logo_login = None
        branding.save()

        url = branding.get_logo_login_url()

        self.assertEqual(url, "/static/public/icone.png")

    def test_get_favicon_url_fallback(self):
        """Testa fallback quando favicon nao existe."""
        branding = Branding.get_instance()
        branding.favicon = None
        branding.save()

        url = branding.get_favicon_url()

        self.assertEqual(url, "/static/public/icone.png")

    def test_str_representation(self):
        """Testa representacao string do model."""
        branding = Branding.get_instance()

        self.assertEqual(str(branding), f"Branding: {branding.nome_sistema}")

    def test_singleton_id_is_always_one(self):
        """Testa que singleton_id e sempre 1."""
        branding = Branding.get_instance()
        branding.singleton_id = 999  # Tentar mudar
        branding.save()

        self.assertEqual(branding.singleton_id, 1)


class BrandingContextProcessorTest(TestCase):
    """Testes do context processor de branding."""

    def test_context_processor_returns_branding(self):
        """Testa que context processor retorna branding."""
        from core.context_processors import branding_context

        request = RequestFactory().get('/')
        context = branding_context(request)

        self.assertIn('branding', context)
        self.assertIn('SYSTEM_NAME', context)
        self.assertIn('COMPANY_NAME', context)

    def test_context_processor_default_values(self):
        """Testa valores padrao do context processor."""
        from core.context_processors import branding_context

        request = RequestFactory().get('/')
        context = branding_context(request)

        self.assertEqual(context['SYSTEM_NAME'], 'Vivamente360')
        self.assertEqual(context['COMPANY_NAME'], '3S Dev')

    def test_context_processor_with_inactive_branding(self):
        """Testa que usa valores padrao quando branding esta inativo."""
        from core.context_processors import branding_context
        from django.core.cache import cache

        # Limpar cache
        cache.clear()

        # Criar branding inativo
        branding = Branding.get_instance()
        branding.nome_sistema = "Custom Name"
        branding.nome_empresa = "Custom Company"
        branding.ativo = False
        branding.save()

        request = RequestFactory().get('/')
        context = branding_context(request)

        # Deve usar valores padrao quando inativo
        self.assertEqual(context['SYSTEM_NAME'], 'Vivamente360')
        self.assertEqual(context['COMPANY_NAME'], '3S Dev')


class BrandingAdminTest(TestCase):
    """Testes do admin de Branding."""

    def setUp(self):
        """Cria superuser para testes."""
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='admin12345678'
        )
        self.client = Client()

    def test_admin_accessible(self):
        """Testa se admin e acessivel."""
        self.client.login(username='admin', password='admin12345678')
        response = self.client.get('/admin/core/branding/')

        self.assertEqual(response.status_code, 200)

    def test_cannot_add_when_exists(self):
        """Testa que nao pode adicionar segundo registro."""
        # Criar primeiro registro
        Branding.get_instance()

        self.client.login(username='admin', password='admin12345678')
        response = self.client.get('/admin/core/branding/add/')

        # Deve redirecionar ou mostrar 403
        self.assertIn(response.status_code, [302, 403])


class BrandingManagementCommandTest(TestCase):
    """Testes do management command setup_branding."""

    def test_setup_branding_creates_instance(self):
        """Testa que comando cria instancia de branding."""
        from django.core.management import call_command
        from io import StringIO

        out = StringIO()
        call_command('setup_branding', stdout=out)

        self.assertIn('Branding configurado', out.getvalue())
        self.assertEqual(Branding.objects.count(), 1)

    def test_setup_branding_idempotent(self):
        """Testa que comando e idempotente."""
        from django.core.management import call_command
        from io import StringIO

        out = StringIO()

        # Rodar duas vezes
        call_command('setup_branding', stdout=out)
        call_command('setup_branding', stdout=out)

        # Deve ter apenas 1 registro
        self.assertEqual(Branding.objects.count(), 1)
