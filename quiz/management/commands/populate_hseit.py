from django.core.management.base import BaseCommand
from quiz.models import Dimensao, Pergunta


class Command(BaseCommand):
    help = 'Popula as dimensões e perguntas do questionário HSE-IT'
    
    def handle(self, *args, **kwargs):
        self.stdout.write('Populando dimensões e perguntas HSE-IT...')
        
        # Criar dimensões
        dimensoes = {
            'Demandas': Dimensao.objects.get_or_create(
                nome='Demandas',
                defaults={
                    'descricao': 'Carga de trabalho, ritmo e horários',
                    'polaridade': 'NEGATIVA',
                    'ordem': 1
                }
            )[0],
            'Controle': Dimensao.objects.get_or_create(
                nome='Controle',
                defaults={
                    'descricao': 'Autonomia e influência sobre o trabalho',
                    'polaridade': 'POSITIVA',
                    'ordem': 2
                }
            )[0],
            'Apoio Gerencial': Dimensao.objects.get_or_create(
                nome='Apoio Gerencial',
                defaults={
                    'descricao': 'Suporte e incentivo dos supervisores',
                    'polaridade': 'POSITIVA',
                    'ordem': 3
                }
            )[0],
            'Apoio de Colegas': Dimensao.objects.get_or_create(
                nome='Apoio de Colegas',
                defaults={
                    'descricao': 'Suporte e cooperação entre colegas',
                    'polaridade': 'POSITIVA',
                    'ordem': 4
                }
            )[0],
            'Relacionamentos': Dimensao.objects.get_or_create(
                nome='Relacionamentos',
                defaults={
                    'descricao': 'Conflitos e tensões interpessoais',
                    'polaridade': 'NEGATIVA',
                    'ordem': 5
                }
            )[0],
            'Papel': Dimensao.objects.get_or_create(
                nome='Papel',
                defaults={
                    'descricao': 'Clareza sobre responsabilidades e expectativas',
                    'polaridade': 'POSITIVA',
                    'ordem': 6
                }
            )[0],
            'Mudanças': Dimensao.objects.get_or_create(
                nome='Mudanças',
                defaults={
                    'descricao': 'Como as mudanças são geridas e comunicadas',
                    'polaridade': 'POSITIVA',
                    'ordem': 7
                }
            )[0],
        }
        
        # Criar perguntas
        perguntas_data = [
            (1, 'Papel', 'Tenho clareza sobre o que se espera do meu trabalho'),
            (2, 'Controle', 'Posso decidir quando fazer uma pausa'),
            (3, 'Demandas', 'As exigências de trabalho feitas por colegas e supervisores são difíceis de combinar'),
            (4, 'Papel', 'Eu sei como fazer o meu trabalho'),
            (5, 'Relacionamentos', 'Falam ou se comportam comigo de forma dura'),
            (6, 'Demandas', 'Tenho prazos inatingíveis'),
            (7, 'Apoio de Colegas', 'Quando o trabalho se torna difícil, posso contar com ajuda dos colegas'),
            (8, 'Apoio Gerencial', 'Recebo informações e suporte que me ajudam no trabalho que eu faço'),
            (9, 'Demandas', 'Devo trabalhar muito intensamente'),
            (10, 'Controle', 'Consideram a minha opinião sobre a velocidade do meu trabalho'),
            (11, 'Papel', 'Estão claras as minhas tarefas e responsabilidades'),
            (12, 'Demandas', 'Eu não faço algumas tarefas porque tenho muita coisa para fazer'),
            (13, 'Papel', 'Os objetivos e metas do meu setor são claros para mim'),
            (14, 'Relacionamentos', 'Existem conflitos entre os colegas'),
            (15, 'Controle', 'Tenho liberdade de escolha de como fazer meu trabalho'),
            (16, 'Demandas', 'Não tenho possibilidade de fazer pausas suficientes'),
            (17, 'Papel', 'Eu vejo como o meu trabalho se encaixa nos objetivos da empresa'),
            (18, 'Demandas', 'Recebo pressão para trabalhar em outro horário'),
            (19, 'Controle', 'Tenho liberdade de escolha para decidir o que fazer no meu trabalho'),
            (20, 'Demandas', 'Tenho que fazer meu trabalho com muita rapidez'),
            (21, 'Relacionamentos', 'Sinto que sou perseguido no trabalho'),
            (22, 'Demandas', 'As pausas temporárias são impossíveis de cumprir'),
            (23, 'Apoio Gerencial', 'Posso confiar no meu chefe quando eu tiver problemas no trabalho'),
            (24, 'Apoio de Colegas', 'Meus colegas me ajudam e me dão apoio quando eu preciso'),
            (25, 'Controle', 'Minhas sugestões são consideradas sobre como fazer meu trabalho'),
            (26, 'Mudanças', 'Tenho oportunidades para pedir explicações ao chefe sobre as mudanças relacionadas ao meu trabalho'),
            (27, 'Apoio de Colegas', 'No trabalho os meus colegas demonstram o respeito que mereço'),
            (28, 'Mudanças', 'As pessoas são sempre consultadas sobre as mudanças no trabalho'),
            (29, 'Apoio Gerencial', 'Quando algo no trabalho me perturba ou irrita posso falar com meu chefe'),
            (30, 'Controle', 'O meu horário de trabalho pode ser flexível'),
            (31, 'Apoio de Colegas', 'Os colegas estão disponíveis para escutar os meus problemas de trabalho'),
            (32, 'Mudanças', 'Quando há mudanças, faço o meu trabalho com o mesmo carinho'),
            (33, 'Apoio Gerencial', 'Tenho suportado trabalhos emocionalmente exigentes'),
            (34, 'Relacionamentos', 'As relações no trabalho são tensas'),
            (35, 'Apoio Gerencial', 'Meu chefe me incentiva no trabalho'),
        ]
        
        for numero, dimensao_nome, texto in perguntas_data:
            Pergunta.objects.get_or_create(
                numero=numero,
                defaults={
                    'dimensao': dimensoes[dimensao_nome],
                    'texto': texto,
                    'opcoes_texto': '(0) nunca; (1) raramente; (2) às vezes; (3) frequentemente; (4) sempre',
                    'pontuacao_maxima': 4,
                    'ativa': True
                }
            )
        
        self.stdout.write(self.style.SUCCESS(
            f'✓ Dimensões criadas: {len(dimensoes)}'
        ))
        self.stdout.write(self.style.SUCCESS(
            f'✓ Perguntas criadas: {len(perguntas_data)}'
        ))
        self.stdout.write(self.style.SUCCESS('Questionário HSE-IT populado com sucesso!'))