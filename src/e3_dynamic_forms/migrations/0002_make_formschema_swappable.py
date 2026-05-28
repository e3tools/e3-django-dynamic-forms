from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        migrations.swappable_dependency(settings.DYNAMIC_FORMS_SCHEMA_MODEL),
        ('e3_dynamic_forms', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='formschema',
            options={
                'ordering': ['-created_date'],
                'verbose_name': 'form schema',
                'verbose_name_plural': 'form schemas',
                'swappable': 'DYNAMIC_FORMS_SCHEMA_MODEL',
            },
        ),
        migrations.AlterField(
            model_name='formschema',
            name='created_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='%(class)s_created_schemas',
                to=settings.AUTH_USER_MODEL,
                verbose_name='created by',
            ),
        ),
        migrations.AlterField(
            model_name='formresponse',
            name='schema',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='responses',
                to=settings.DYNAMIC_FORMS_SCHEMA_MODEL,
                verbose_name='schema',
            ),
        ),
    ]
