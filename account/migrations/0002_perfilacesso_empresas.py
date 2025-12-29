from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
        ('account', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='perfilacesso',
            name='empresas',
            field=models.ManyToManyField(
                blank=True,
                help_text='Empresas às quais o usuário tem acesso',
                related_name='perfis_acesso',
                to='core.empresa',
            ),
        ),
        migrations.AlterField(
            model_name='perfilacesso',
            name='empresa',
            field=models.ForeignKey(
                blank=True,
                help_text='[DEPRECATED] Use empresas para múltiplas empresas',
                null=True,
                on_delete=models.deletion.SET_NULL,
                related_name='perfis_acesso_legacy',
                to='core.empresa',
            ),
        ),
    ]
