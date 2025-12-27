from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random

from django.conf import settings
from django.contrib.auth.models import User

from core.models import Empresa, Unidade, Setor, Cargo
from importacao.models import Colaborador
from account.models import PerfilAcesso
from quiz.models import Dimensao, Pergunta, MagicLink, Resposta
from core.services.audit_service import AuditService


class Command(BaseCommand):
    help = "Popula DB com Empresa X, 5 colaboradores, gera magic links e submete respostas aleatórias (35 perguntas)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--empresa",
            type=str,
            default="Empresa X",
            help="Nome da empresa a ser criada/atualizada (default: 'Empresa X')"
        )
        parser.add_argument(
            "--create-user",
            action="store_true",
            help="Criar usuário 'tester' com perfil EMPRESA (senha: testpass) para visualizar dashboard"
        )

    def handle(self, *args, **options):
        empresa_nome = options["empresa"]
        create_user = options["create_user"]

        self.stdout.write(self.style.MIGRATE_HEADING(f"Iniciando população para empresa: {empresa_nome}"))

        # 1) Empresa
        empresa, _ = Empresa.objects.get_or_create(nome=empresa_nome)
        self.stdout.write(self.style.SUCCESS(f"Empresa pronta: {empresa.nome} ({empresa.id})"))

        # 2) Linhas (suas + 2 extras) -> unidade,setor,cargo,email
        rows = [
            ("Matriz", "RH", "Analista", "henrique.alves.siqueira@hotmail.com"),
            ("Matriz", "TI", "Desenvolvedor", "maria@empresa.com"),
            ("Filial SP", "Vendas", "Vendedor", "pedro@empresa.com"),
            # extras para totalizar 5
            ("Filial SP", "Suporte", "Técnico", "ana.souza@empresa.com"),
            ("Matriz", "Financeiro", "Analista", "carlos.santos@empresa.com"),
        ]

        colaboradores = []
        for unidade_nome, setor_nome, cargo_nome, email in rows:
            unidade, _ = Unidade.objects.get_or_create(empresa=empresa, nome=unidade_nome)
            setor, _ = Setor.objects.get_or_create(unidade=unidade, nome=setor_nome)
            cargo, _ = Cargo.objects.get_or_create(setor=setor, nome=cargo_nome)
            colaborador, created = Colaborador.objects.update_or_create(
                email=email,
                defaults={"cargo": cargo, "ativo": True}
            )
            colaboradores.append(colaborador)
            self.stdout.write(self.style.NOTICE(f"{'Criado' if created else 'Atualizado'} colaborador: {email}"))

        # 3) Usuário tester/profile opcional
        if create_user:
            user, created = User.objects.get_or_create(username="tester", defaults={"email": "tester@example.com"})
            if created:
                user.set_password("testpass")
                user.save()
                self.stdout.write(self.style.SUCCESS("Usuário 'tester' criado com senha 'testpass'"))
            else:
                self.stdout.write(self.style.WARNING("Usuário 'tester' já existe"))

            # criar perfil de acesso EMPRESA ligado à empresa criada
            perfil, pcreated = PerfilAcesso.objects.get_or_create(
                user=user,
                defaults={"nivel_acesso": "EMPRESA", "empresa": empresa, "ativo": True}
            )
            if not pcreated:
                perfil.nivel_acesso = "EMPRESA"
                perfil.empresa = empresa
                perfil.ativo = True
                perfil.save()
            self.stdout.write(self.style.SUCCESS("Perfil de acesso EMPRESA vinculado a 'tester'"))

        # 4) Criar Dimensão e 35 perguntas
        dimensao, _ = Dimensao.objects.get_or_create(
            nome="Geral",
            defaults={"descricao": "Dimensão geral gerada automaticamente", "polaridade": "POSITIVA", "ordem": 1, "ativa": True}
        )
        perguntas = []
        for numero in range(1, 36):  # 1..35
            p, created = Pergunta.objects.get_or_create(
                numero=numero,
                defaults={
                    "dimensao": dimensao,
                    "texto": f"Pergunta automática {numero}",
                    "pontuacao_maxima": 4,
                    "ativa": True
                }
            )
            perguntas.append(p)
        self.stdout.write(self.style.SUCCESS(f"{len(perguntas)} perguntas garantidas (1..35)"))

        # 5) Para cada colaborador: gerar magic link (somente hash no DB) e gravar/atualizar resposta aleatória
        agora = timezone.now()
        expiration = agora + timedelta(hours=getattr(settings, "MAGIC_LINK_EXPIRATION_HOURS", 48))

        for colaborador in colaboradores:
            # obter/criar magic link (evitar duplicar)
            if hasattr(colaborador, "magic_link"):
                magic_link = colaborador.magic_link
                self.stdout.write(self.style.WARNING(f"Colaborador {colaborador.email} já tem magic link ({magic_link.id}), usando existente"))
            else:
                token = MagicLink.gerar_token()
                token_hash = MagicLink.hash_token(token)
                magic_link = MagicLink.objects.create(
                    colaborador=colaborador,
                    token_hash=token_hash,
                    expires_at=expiration
                )
                self.stdout.write(self.style.NOTICE(f"MagicLink criado para {colaborador.email} (id={magic_link.id})"))

            # marcar iniciado se necessário
            if not magic_link.started_at:
                magic_link.started_at = timezone.now()
                magic_link.save()

            # montar respostas aleatórias para 35 perguntas
            respostas_dict = {}
            for p in perguntas:
                respostas_dict[str(p.numero)] = random.randint(0, p.pontuacao_maxima)

            # tempo total: random 300..900 segundos (5..15 min)
            tempo_total = random.randint(300, 900)

            # Se já existir resposta associada ao magic_link, atualizamos; senão, criamos
            if hasattr(magic_link, "resposta"):
                resposta = magic_link.resposta
                resposta.respostas = respostas_dict
                resposta.tempo_total_segundos = tempo_total
                resposta.save()
                try:
                    resposta.calcular_scores()
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Erro ao recalcular scores para resposta existente {resposta.id}: {e}"))
                self.stdout.write(self.style.SUCCESS(f"Resposta existente atualizada para {colaborador.email} (resposta id={resposta.id})"))
            else:
                try:
                    resposta = Resposta.objects.create(
                        magic_link=magic_link,
                        respostas=respostas_dict,
                        tempo_total_segundos=tempo_total
                    )
                except Exception as e:
                    # lidar com condição de corrida / integridade de forma segura
                    self.stdout.write(self.style.ERROR(f"Erro ao criar resposta para magic link {magic_link.id}: {e}"))
                    continue

                try:
                    resposta.calcular_scores()
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Erro ao calcular scores para resposta {resposta.id}: {e}"))

                self.stdout.write(self.style.SUCCESS(f"Resposta criada e scores calculados para {colaborador.email}"))

            # marcar concluído
            try:
                magic_link.marcar_concluido()
            except Exception as e:
                # tentar salvar manualmente status/completed_at se houver erro
                magic_link.status = "COMPLETED"
                magic_link.completed_at = timezone.now()
                magic_link.save()

            # auditoria (opcional)
            try:
                AuditService.log(
                    action="QUIZ_COMPLETED",
                    description=f"Questionário concluído (populado): {str(magic_link.id)[:8]}",
                    metadata={"magic_link_id": str(magic_link.id), "resposta_id": str(resposta.id)},
                )
            except Exception:
                # não bloquear por falha de auditoria
                pass

        self.stdout.write(self.style.MIGRATE_LABEL("População concluída. Dados persistidos no banco real."))
        self.stdout.write(self.style.WARNING("Não foram enviados e-mails. Tokens em texto puro não são exibidos por segurança."))
