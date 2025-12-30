from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, date
import random

from django.conf import settings
from django.contrib.auth.models import User

from core.models import Empresa, Unidade, Setor, Cargo
from importacao.models import Colaborador
from account.models import PerfilAcesso
from quiz.models import Pergunta, MagicLink, Resposta
from core.services.audit_service import AuditService


class Command(BaseCommand):
    help = "Popula DB com empresa demo, 1000 colaboradores com dados demográficos, gera magic links e submete respostas."

    def add_arguments(self, parser):
        parser.add_argument(
            "--empresa",
            type=str,
            default="Empresa Demo",
            help="Nome da empresa a ser criada/atualizada (default: 'Empresa Demo')"
        )
        parser.add_argument(
            "--create-user",
            action="store_true",
            help="Criar usuário 'tester' com perfil EMPRESA (senha: testpass) para visualizar dashboard"
        )
        parser.add_argument(
            "--total",
            type=int,
            default=1000,
            help="Total de colaboradores a criar (default: 1000)"
        )

    def handle(self, *args, **options):
        empresa_nome = options["empresa"]
        create_user = options["create_user"]
        total_colaboradores = options["total"]

        self.stdout.write(self.style.MIGRATE_HEADING(f"Iniciando população para empresa: {empresa_nome}"))
        self.stdout.write(self.style.NOTICE(f"Total de colaboradores a criar: {total_colaboradores}"))

        # 1) Empresa
        empresa, _ = Empresa.objects.get_or_create(nome=empresa_nome)
        self.stdout.write(self.style.SUCCESS(f"Empresa pronta: {empresa.nome} ({empresa.id})"))

        # 2) Estrutura simples e equilibrada
        # Formato: unidade, setor, cargo, email, data_nascimento, sexo
        unidades_nomes = ["Matriz", "Filial SP", "Filial RJ", "Filial MG"]
        setores_nomes = ["RH", "TI", "Vendas", "Financeiro", "Operações"]
        cargos_nomes = ["Analista", "Gerente"]
        sexos = ["M", "F"]

        # Criar hierarquia
        estrutura = []  # Lista de (unidade, setor, cargo)
        for unidade_nome in unidades_nomes:
            unidade, _ = Unidade.objects.get_or_create(empresa=empresa, nome=unidade_nome)
            for setor_nome in setores_nomes:
                setor, _ = Setor.objects.get_or_create(unidade=unidade, nome=setor_nome)
                for cargo_nome in cargos_nomes:
                    cargo, _ = Cargo.objects.get_or_create(setor=setor, nome=cargo_nome)
                    estrutura.append((unidade, setor, cargo))

        self.stdout.write(self.style.SUCCESS(f"Estrutura criada: {len(unidades_nomes)} unidades, {len(setores_nomes)} setores, {len(cargos_nomes)} cargos"))
        self.stdout.write(self.style.NOTICE(f"Total de combinações: {len(estrutura)}"))

        # Calcular distribuição igual
        combinacoes = len(estrutura)
        por_combinacao = total_colaboradores // combinacoes
        restante = total_colaboradores % combinacoes

        self.stdout.write(self.style.NOTICE(f"Colaboradores por combinação: {por_combinacao} (+ {restante} extras distribuídos)"))

        # 3) Criar colaboradores com distribuição igual
        colaboradores = []
        contador = 0

        # Gerar datas de nascimento (faixa: 18-65 anos)
        hoje = date.today()

        for idx, (unidade, setor, cargo) in enumerate(estrutura):
            # Adicionar 1 extra para as primeiras 'restante' combinações
            qtd = por_combinacao + (1 if idx < restante else 0)

            for i in range(qtd):
                contador += 1
                email = f"colaborador{contador:04d}@empresa.com"

                # Alternar sexo para distribuição equilibrada
                sexo = sexos[contador % 2]

                # Gerar data de nascimento aleatória (idade entre 18-65)
                idade = random.randint(18, 65)
                ano_nasc = hoje.year - idade
                mes_nasc = random.randint(1, 12)
                dia_nasc = random.randint(1, 28)  # Simplificado para evitar problemas com dias inválidos
                data_nascimento = date(ano_nasc, mes_nasc, dia_nasc)

                colaborador, created = Colaborador.objects.update_or_create(
                    email=email,
                    defaults={
                        "cargo": cargo,
                        "data_nascimento": data_nascimento,
                        "sexo": sexo,
                        "ativo": True
                    }
                )
                colaboradores.append(colaborador)

                # Log a cada 100
                if contador % 100 == 0:
                    self.stdout.write(self.style.NOTICE(f"Criados {contador} colaboradores..."))

        self.stdout.write(self.style.SUCCESS(f"Total de {len(colaboradores)} colaboradores criados/atualizados"))

        # 4) Usuário tester/profile opcional
        if create_user:
            user, created = User.objects.get_or_create(username="tester", defaults={"email": "tester@example.com"})
            if created:
                user.set_password("testpass")
                user.save()
                self.stdout.write(self.style.SUCCESS("Usuário 'tester' criado com senha 'testpass'"))
            else:
                self.stdout.write(self.style.WARNING("Usuário 'tester' já existe"))

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

        # 5) Garantir que as perguntas HSE-IT existam
        from django.core.management import call_command
        call_command('populate_hseit')

        perguntas = list(Pergunta.objects.filter(ativa=True).order_by('numero'))

        if len(perguntas) < 35:
            self.stdout.write(self.style.ERROR(
                f'ERRO: Apenas {len(perguntas)} perguntas HSE-IT encontradas. '
                'Execute python manage.py populate_hseit primeiro.'
            ))
            return

        self.stdout.write(self.style.SUCCESS(f"{len(perguntas)} perguntas HSE-IT carregadas"))

        # 6) Para cada colaborador: gerar magic link e gravar resposta aleatória
        agora = timezone.now()
        expiration = agora + timedelta(hours=getattr(settings, "MAGIC_LINK_EXPIRATION_HOURS", 48))

        respostas_criadas = 0
        respostas_atualizadas = 0

        for idx, colaborador in enumerate(colaboradores):
            # Obter/criar magic link
            if hasattr(colaborador, "magic_link"):
                magic_link = colaborador.magic_link
            else:
                token = MagicLink.gerar_token()
                token_hash = MagicLink.hash_token(token)
                magic_link = MagicLink.objects.create(
                    colaborador=colaborador,
                    token_hash=token_hash,
                    expires_at=expiration
                )

            # Marcar iniciado se necessário
            if not magic_link.started_at:
                magic_link.started_at = timezone.now()
                magic_link.save()

            # Montar respostas aleatórias para as perguntas
            respostas_dict = {}
            for p in perguntas:
                respostas_dict[str(p.numero)] = random.randint(0, p.pontuacao_maxima)

            # Tempo total: random 300..900 segundos (5..15 min)
            tempo_total = random.randint(300, 900)

            # Se já existir resposta, atualizar; senão, criar
            if hasattr(magic_link, "resposta"):
                resposta = magic_link.resposta
                resposta.respostas = respostas_dict
                resposta.tempo_total_segundos = tempo_total
                resposta.save()
                try:
                    resposta.calcular_scores()
                except Exception:
                    pass
                respostas_atualizadas += 1
            else:
                try:
                    resposta = Resposta.objects.create(
                        magic_link=magic_link,
                        respostas=respostas_dict,
                        tempo_total_segundos=tempo_total
                    )
                    try:
                        resposta.calcular_scores()
                    except Exception:
                        pass
                    respostas_criadas += 1
                except Exception:
                    continue

            # Marcar concluído
            try:
                magic_link.marcar_concluido()
            except Exception:
                magic_link.status = "COMPLETED"
                magic_link.completed_at = timezone.now()
                magic_link.save()

            # Log a cada 100
            if (idx + 1) % 100 == 0:
                self.stdout.write(self.style.NOTICE(f"Processadas {idx + 1} respostas..."))

        self.stdout.write(self.style.SUCCESS(f"Respostas criadas: {respostas_criadas}, atualizadas: {respostas_atualizadas}"))

        # Resumo final
        self.stdout.write(self.style.MIGRATE_LABEL("\n=== RESUMO ==="))
        self.stdout.write(self.style.SUCCESS(f"Empresa: {empresa_nome}"))
        self.stdout.write(self.style.SUCCESS(f"Unidades: {len(unidades_nomes)} ({', '.join(unidades_nomes)})"))
        self.stdout.write(self.style.SUCCESS(f"Setores: {len(setores_nomes)} ({', '.join(setores_nomes)})"))
        self.stdout.write(self.style.SUCCESS(f"Cargos: {len(cargos_nomes)} ({', '.join(cargos_nomes)})"))
        self.stdout.write(self.style.SUCCESS(f"Colaboradores: {len(colaboradores)}"))
        self.stdout.write(self.style.SUCCESS(f"Respostas: {respostas_criadas + respostas_atualizadas}"))
        self.stdout.write(self.style.SUCCESS(f"Distribuição de sexo: ~50% M, ~50% F"))
        self.stdout.write(self.style.SUCCESS(f"Faixa etária: 18-65 anos (aleatório)"))
        self.stdout.write(self.style.MIGRATE_LABEL("===============\n"))

        self.stdout.write(self.style.MIGRATE_LABEL("População concluída. Dados persistidos no banco."))
