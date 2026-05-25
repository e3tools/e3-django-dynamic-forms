from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
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
            model_name='formresponse',
            name='schema',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='responses',
                to=getattr(
                    settings,
                    'DYNAMIC_FORMS_SCHEMA_MODEL',
                    'e3_dynamic_forms.FormSchema',
                ),
                verbose_name='schema',
            ),
        ),
    ]
