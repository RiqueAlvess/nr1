# Generated manually for icon fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='dimensao',
            name='icon_name',
            field=models.CharField(blank=True, default='lightbulb', help_text='Nome do ícone Lucide', max_length=50),
        ),
        migrations.AddField(
            model_name='dimensao',
            name='icon_color',
            field=models.CharField(blank=True, default='blue', help_text='Cor do ícone (classe Tailwind)', max_length=20),
        ),
        migrations.AddField(
            model_name='dimensao',
            name='icon_path',
            field=models.TextField(blank=True, help_text='SVG path do ícone Lucide'),
        ),
    ]
