# Generated by Django 4.0.3 on 2022-06-07 20:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('knowledge', '0017_alter_author_options_alter_keyword_options'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='author',
            options={'ordering': ['name']},
        ),
        migrations.AddField(
            model_name='publication',
            name='from_ciencia',
            field=models.BooleanField(default=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='publication',
            name='from_scopus',
            field=models.BooleanField(default=False),
            preserve_default=False,
        ),
    ]
