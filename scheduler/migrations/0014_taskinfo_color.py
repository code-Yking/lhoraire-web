# Generated by Django 3.1.6 on 2021-08-18 09:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scheduler', '0013_auto_20210818_0938'),
    ]

    operations = [
        migrations.AddField(
            model_name='taskinfo',
            name='color',
            field=models.CharField(default=0, max_length=10),
            preserve_default=False,
        ),
    ]
