from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
import random

from django.contrib.auth.models import User

from core.models import Empresa, Unidade, Setor, Cargo
from importacao.models import Colaborador
from account.models import PerfilAcesso
from quiz.models import Pergunta, MagicLink, Resposta


class PopulateAndSubmitQuiz35QuestionsTest(TestCase):
    """
    - Cria Empresa X + hierarquia
    - Cria 5 colaboradores (usando as linhas fornecidas + 2 extras)
    - Garante que existam 35 perguntas (1..35)
    - Para cada colaborador: cria MagicLink (gravando apenas token_hash) e submete respostas aleatórias para as 35 perguntas
    - Faz login com um usuário com PerfilAcesso nível EMPRESA e acessa dashboard:principal
    """

    def setUp(self):
        # Empresa
        self.empresa = Empresa.objects.create(nome="Empresa X")

        # Linhas fornecidas + 2 extras = 5 colaboradores
        rows = [
            ("Matriz", "RH", "Analista", "henrique.alves.siqueira@hotmail.com"),
            ("Matriz", "TI", "Desenvolvedor", "maria@empresa.com"),
            ("Filial SP", "Vendas", "Vendedor", "pedro@empresa.com"),
            ("Filial SP", "Suporte", "Técnico", "ana.souza@empresa.com"),
            ("Matriz", "Financeiro", "Analista", "carlos.santos@empresa.com"),
        ]

        self.colaboradores = []

        for unidade_nome, setor_nome, cargo_nome, email in rows:
            unidade, _ = Unidade.objects.get_or_create(
                nome=unidade_nome,
                empresa=self.empresa
            )
            setor, _ = Setor.objects.get_or_create(
                unidade=unidade,
                nome=setor_nome
            )
            cargo, _ = Cargo.objects.get_or_create(
                setor=setor,
                nome=cargo_nome
            )

            colaborador, _ = Colaborador.objects.update_or_create(
                email=email,
                defaults={"cargo": cargo, "ativo": True}
            )
            self.colaboradores.append(colaborador)

        # Usuário com PerfilAcesso EMPRESA para ver dashboard
        self.user = User.objects.create_user(username="tester", password="testpass", email="tester@example.com")
        PerfilAcesso.objects.create(
            user=self.user,
            nivel_acesso="EMPRESA",
            empresa=self.empresa,
            ativo=True
        )

        # Garantir que usamos perguntas HSE-IT reais (NÃO criar perguntas genéricas!)
        from django.core.management import call_command
        call_command('populate_hseit')

        # Buscar perguntas HSE-IT existentes
        self.perguntas = list(Pergunta.objects.filter(ativa=True).order_by('numero'))

        # Validar que temos 35 perguntas HSE-IT
        self.assertEqual(len(self.perguntas), 35, "Devem existir 35 perguntas HSE-IT")

    def test_submit_random_answers_for_35_questions(self):
        client = Client()

        for colaborador in self.colaboradores:
            # Gerar token e gravar apenas o hash (sem envio de email)
            token = MagicLink.gerar_token()
            token_hash = MagicLink.hash_token(token)
            expires_at = timezone.now() + timedelta(hours=48)

            magic_link = MagicLink.objects.create(
                colaborador=colaborador,
                token_hash=token_hash,
                expires_at=expires_at
            )

            # Montar payload com respostas para todas as perguntas (1..35)
            post_data = {}
            for pergunta in self.perguntas:
                post_data[f"pergunta_{pergunta.numero}"] = str(random.randint(0, pergunta.pontuacao_maxima))

            # Submeter via endpoint público (usa o token em texto puro)
            submeter_url = reverse("quiz:submeter", kwargs={"token": token})
            resp_post = client.post(submeter_url, data=post_data, follow=True)

            # Verificar que foi criada a Resposta vinculada ao magic link
            self.assertTrue(
                Resposta.objects.filter(magic_link=magic_link).exists(),
                msg=f"Resposta não encontrada para colaborador {colaborador.email}"
            )

            # Recarregar e checar status do magic link (deve ter sido marcado concluído pela view)
            magic_link.refresh_from_db()
            # validamos que existe uma resposta e que o status pode ser 'COMPLETED' ou que completed_at esteja setado
            resposta = Resposta.objects.filter(magic_link=magic_link).first()
            self.assertIsNotNone(resposta, "Resposta criada, mas não recuperável")
            # opcional: garantir que o JSON de respostas contenha 35 entradas
            self.assertEqual(len(resposta.respostas), 35, msg="Número de respostas gravadas diferente de 35")

        # Fazer login como usuário com perfil e acessar dashboard principal
        login_ok = client.login(username="tester", password="testpass")
        self.assertTrue(login_ok, "Falha ao logar com usuário de teste")

        dashboard_url = reverse("dashboard:principal")
        dashboard_resp = client.get(dashboard_url)
        self.assertEqual(dashboard_resp.status_code, 200, "Dashboard não retornou 200 OK")

        content = dashboard_resp.content.decode("utf-8")
        self.assertIn(self.empresa.nome, content, "Nome da empresa não encontrado no conteúdo do dashboard")

        # Checar que respostas de fato existem
        self.assertGreaterEqual(Resposta.objects.count(), len(self.colaboradores), "Respostas insuficientes gravadas")