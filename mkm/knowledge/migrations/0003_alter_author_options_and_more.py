# Generated by Django 4.0.3 on 2022-04-19 22:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('knowledge', '0002_alter_author_ciencia_id_alter_author_orcid_id_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='author',
            options={'ordering': ['pk']},
        ),
        migrations.AlterUniqueTogether(
            name='publication',
            unique_together=set(),
        ),
        migrations.AlterField(
            model_name='publication',
            name='ciencia_id',
            field=models.CharField(max_length=100, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='publication',
            name='scopus_id',
            field=models.IntegerField(null=True, unique=True),
        ),
    ]
