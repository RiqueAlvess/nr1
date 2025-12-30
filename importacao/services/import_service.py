import csv
import io
import logging
from datetime import datetime
from django.db import transaction
from typing import List, Dict, Any, Optional
from core.models import Empresa, Unidade, Setor, Cargo
from importacao.models import Colaborador, ProcessoImportacao
from core.services.audit_service import AuditService

logger = logging.getLogger('nr1')


class ImportService:
    """Serviço de importação de dados organizacionais"""
    
    @staticmethod
    def normalizar_texto(texto: str) -> str:
        """Normaliza texto removendo espaços e padronizando"""
        return ' '.join(texto.strip().split())
    
    @staticmethod
    def validar_email(email: str) -> bool:
        """Validação básica de email"""
        return '@' in email and '.' in email.split('@')[1]

    @staticmethod
    def processar_data_nascimento(data_str: str) -> Optional[datetime]:
        """
        Processa string de data de nascimento e retorna objeto date

        Formatos aceitos:
        - DD/MM/YYYY
        - DD-MM-YYYY
        - YYYY-MM-DD

        Args:
            data_str: String com a data de nascimento

        Returns:
            date object ou None se inválido
        """
        if not data_str or not data_str.strip():
            return None

        data_str = data_str.strip()

        # Tentar diferentes formatos
        formatos = [
            '%d/%m/%Y',  # DD/MM/YYYY
            '%d-%m-%Y',  # DD-MM-YYYY
            '%Y-%m-%d',  # YYYY-MM-DD
            '%d/%m/%y',  # DD/MM/YY
            '%d-%m-%y',  # DD-MM-YY
        ]

        for formato in formatos:
            try:
                data = datetime.strptime(data_str, formato).date()
                # Validar idade razoável (entre 14 e 100 anos)
                from datetime import date
                hoje = date.today()
                idade = hoje.year - data.year - ((hoje.month, hoje.day) < (data.month, data.day))
                if 14 <= idade <= 100:
                    return data
            except ValueError:
                continue

        logger.warning(f"Formato de data não reconhecido: {data_str}")
        return None

    @staticmethod
    def processar_sexo(sexo_str: str) -> str:
        """
        Processa string de sexo e retorna código padronizado

        Valores aceitos:
        - M/Masculino/Masc/Homem -> 'M'
        - F/Feminino/Fem/Mulher -> 'F'
        - O/Outro -> 'O'
        - Qualquer outro valor -> 'N' (Não informado)

        Args:
            sexo_str: String com o sexo

        Returns:
            Código do sexo: 'M', 'F', 'O' ou 'N'
        """
        if not sexo_str or not sexo_str.strip():
            return 'N'

        sexo_normalizado = sexo_str.strip().upper()

        # Masculino
        if sexo_normalizado in ['M', 'MASCULINO', 'MASC', 'HOMEM', 'H']:
            return 'M'

        # Feminino
        if sexo_normalizado in ['F', 'FEMININO', 'FEM', 'MULHER']:
            return 'F'

        # Outro
        if sexo_normalizado in ['O', 'OUTRO', 'OUTROS']:
            return 'O'

        # Não informado
        return 'N'
    
    @staticmethod
    def processar_csv(
        arquivo,
        usuario,
        empresa_nome: str
    ) -> ProcessoImportacao:
        """
        Processa arquivo CSV de importação

        Formato esperado (campos obrigatórios):
        unidade,setor,cargo,email

        Campos opcionais:
        data_nascimento,sexo

        Args:
            arquivo: Arquivo CSV enviado
            usuario: Usuário que iniciou a importação
            empresa_nome: Nome da empresa

        Returns:
            ProcessoImportacao: Registro do processo
        """
        
        # Criar registro do processo
        processo = ProcessoImportacao.objects.create(
            usuario=usuario,
            arquivo_nome=arquivo.name,
            status='PROCESSING'
        )
        
        # Auditoria
        AuditService.log(
            action='IMPORT_START',
            description=f'Importação iniciada: {arquivo.name}',
            user=usuario,
            metadata={'processo_id': str(processo.id)}
        )
        
        try:
            # Ler arquivo
            decoded_file = arquivo.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)
            
            linhas = list(reader)
            processo.total_linhas = len(linhas)
            processo.save()
            
            erros = []
            processadas = 0
            
            with transaction.atomic():
                # Criar ou obter empresa
                empresa, _ = Empresa.objects.get_or_create(
                    nome=ImportService.normalizar_texto(empresa_nome)
                )
                
                for idx, linha in enumerate(linhas, start=1):
                    try:
                        # Validar campos obrigatórios
                        if not all(k in linha for k in ['unidade', 'setor', 'cargo', 'email']):
                            erros.append({
                                'linha': idx,
                                'erro': 'Campos obrigatórios faltando'
                            })
                            continue
                        
                        # Normalizar dados
                        unidade_nome = ImportService.normalizar_texto(linha['unidade'])
                        setor_nome = ImportService.normalizar_texto(linha['setor'])
                        cargo_nome = ImportService.normalizar_texto(linha['cargo'])
                        email = linha['email'].strip().lower()
                        
                        # Validar email
                        if not ImportService.validar_email(email):
                            erros.append({
                                'linha': idx,
                                'erro': f'Email inválido: {email}'
                            })
                            continue
                        
                        # Criar hierarquia completa
                        unidade, _ = Unidade.objects.get_or_create(
                            empresa=empresa,
                            nome=unidade_nome
                        )
                        
                        setor, _ = Setor.objects.get_or_create(
                            unidade=unidade,
                            nome=setor_nome
                        )
                        
                        # Cargo agora vinculado ao setor
                        cargo, _ = Cargo.objects.get_or_create(
                            setor=setor,
                            nome=cargo_nome
                        )

                        # Processar campos opcionais
                        data_nascimento = None
                        if 'data_nascimento' in linha and linha['data_nascimento']:
                            data_nascimento = ImportService.processar_data_nascimento(
                                linha['data_nascimento']
                            )

                        sexo = 'N'  # Padrão: Não informado
                        if 'sexo' in linha and linha['sexo']:
                            sexo = ImportService.processar_sexo(linha['sexo'])

                        # Criar ou atualizar colaborador
                        defaults = {
                            'cargo': cargo,
                            'ativo': True,
                            'sexo': sexo,
                        }

                        # Adicionar data_nascimento apenas se foi fornecida
                        if data_nascimento:
                            defaults['data_nascimento'] = data_nascimento

                        colaborador, created = Colaborador.objects.update_or_create(
                            email=email,
                            defaults=defaults
                        )

                        processadas += 1
                        
                    except Exception as e:
                        erros.append({
                            'linha': idx,
                            'erro': str(e)
                        })
                        logger.error(f"Erro na linha {idx}: {str(e)}")
                
                # Atualizar processo
                processo.linhas_processadas = processadas
                processo.linhas_erro = len(erros)
                processo.erros = erros
                processo.status = 'COMPLETED'
                processo.metadata = {
                    'empresa_id': str(empresa.id),
                    'empresa_nome': empresa.nome
                }
                processo.save()
                
                # Auditoria
                AuditService.log(
                    action='IMPORT_SUCCESS',
                    description=f'Importação concluída: {processadas} colaboradores processados',
                    user=usuario,
                    metadata={
                        'processo_id': str(processo.id),
                        'total': processo.total_linhas,
                        'processadas': processadas,
                        'erros': len(erros)
                    }
                )
                
                return processo
                
        except Exception as e:
            processo.status = 'FAILED'
            processo.erros = [{'erro': str(e)}]
            processo.save()
            
            # Auditoria
            AuditService.log(
                action='IMPORT_ERROR',
                description=f'Erro na importação: {str(e)}',
                user=usuario,
                metadata={'processo_id': str(processo.id)}
            )
            
            logger.error(f"Erro no processo de importação: {str(e)}")
            raise