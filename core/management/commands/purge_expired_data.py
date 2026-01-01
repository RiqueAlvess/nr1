"""
Management command para purge de dados expirados (LGPD - Retenção de Dados)
Execução: python manage.py purge_expired_data
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
import logging

from importacao.models import Colaborador
from account.models import PasswordResetToken
from core.models import AuditLog
from quiz.models import MagicLink

logger = logging.getLogger('nr1')


class Command(BaseCommand):
    help = 'Remove dados expirados conforme política de retenção LGPD'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula a execução sem deletar dados',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        self.stdout.write(self.style.WARNING(
            f'{"[DRY RUN] " if dry_run else ""}Iniciando purge de dados expirados...'
        ))

        total_deleted = 0

        # 1. Purge de colaboradores com data de expiração atingida
        total_deleted += self.purge_colaboradores(dry_run)

        # 2. Purge de tokens de redefinição de senha expirados (> 90 dias)
        total_deleted += self.purge_password_reset_tokens(dry_run)

        # 3. Purge de magic links expirados (> 1 ano)
        total_deleted += self.purge_magic_links(dry_run)

        # 4. Purge de logs de auditoria antigos (> período de retenção)
        total_deleted += self.purge_audit_logs(dry_run)

        self.stdout.write(self.style.SUCCESS(
            f'{"[DRY RUN] " if dry_run else ""}Purge concluído. Total de registros removidos: {total_deleted}'
        ))

        logger.info(
            f'{"[DRY RUN] " if dry_run else ""}Purge de dados expirados concluído. '
            f'Total removido: {total_deleted}'
        )

    def purge_colaboradores(self, dry_run=False):
        """Remove colaboradores com data de expiração atingida"""
        hoje = timezone.now().date()
        colaboradores_expirados = Colaborador.objects.filter(
            data_expiracao__lt=hoje,
            ativo=False  # Apenas inativos
        )

        count = colaboradores_expirados.count()

        if count > 0:
            self.stdout.write(
                f'  Colaboradores expirados encontrados: {count}'
            )

            if not dry_run:
                colaboradores_expirados.delete()
                logger.info(f'Purge: {count} colaboradores removidos')

        return count

    def purge_password_reset_tokens(self, dry_run=False):
        """Remove tokens de reset de senha expirados há mais de 90 dias"""
        data_limite = timezone.now() - timedelta(days=90)
        tokens_expirados = PasswordResetToken.objects.filter(
            expires_at__lt=data_limite
        )

        count = tokens_expirados.count()

        if count > 0:
            self.stdout.write(
                f'  Tokens de reset expirados encontrados: {count}'
            )

            if not dry_run:
                tokens_expirados.delete()
                logger.info(f'Purge: {count} tokens de reset removidos')

        return count

    def purge_magic_links(self, dry_run=False):
        """Remove magic links expirados há mais de 1 ano"""
        data_limite = timezone.now() - timedelta(days=365)
        magic_links_expirados = MagicLink.objects.filter(
            status='EXPIRED',
            expires_at__lt=data_limite
        )

        count = magic_links_expirados.count()

        if count > 0:
            self.stdout.write(
                f'  Magic links expirados encontrados: {count}'
            )

            if not dry_run:
                magic_links_expirados.delete()
                logger.info(f'Purge: {count} magic links removidos')

        return count

    def purge_audit_logs(self, dry_run=False):
        """Remove logs de auditoria conforme política de retenção"""
        retention_years = getattr(settings, 'DATA_RETENTION_YEARS', 5)
        data_limite = timezone.now() - timedelta(days=retention_years * 365)

        logs_expirados = AuditLog.objects.filter(
            created_at__lt=data_limite
        )

        count = logs_expirados.count()

        if count > 0:
            self.stdout.write(
                f'  Logs de auditoria expirados encontrados: {count} (>{retention_years} anos)'
            )

            if not dry_run:
                logs_expirados.delete()
                logger.info(f'Purge: {count} logs de auditoria removidos')

        return count
