# Generated migration for adding demographic fields to Colaborador model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('importacao', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='colaborador',
            name='data_nascimento',
            field=models.DateField(blank=True, help_text='Data de nascimento do colaborador', null=True),
        ),
        migrations.AddField(
            model_name='colaborador',
            name='sexo',
            field=models.CharField(
                choices=[
                    ('M', 'Masculino'),
                    ('F', 'Feminino'),
                    ('O', 'Outro'),
                    ('N', 'Não informado')
                ],
                default='N',
                help_text='Sexo do colaborador',
                max_length=1
            ),
        ),
        migrations.AddIndex(
            model_name='colaborador',
            index=models.Index(fields=['data_nascimento'], name='colaborador_data_nasc_idx'),
        ),
        migrations.AddIndex(
            model_name='colaborador',
            index=models.Index(fields=['sexo'], name='colaborador_sexo_idx'),
        ),
    ]
