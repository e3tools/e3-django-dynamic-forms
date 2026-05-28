from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        migrations.swappable_dependency(settings.DYNAMIC_FORMS_SCHEMA_MODEL),
        migrations.swappable_dependency(settings.DYNAMIC_FORMS_RESPONSE_MODEL),
        ('e3_dynamic_forms', '0002_make_formschema_swappable'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='formresponse',
            options={
                'ordering': ['-created_date'],
                'verbose_name': 'form response',
                'verbose_name_plural': 'form responses',
                'swappable': 'DYNAMIC_FORMS_RESPONSE_MODEL',
            },
        ),
        migrations.AlterField(
            model_name='formresponse',
            name='schema',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='%(class)s_responses',
                to=settings.DYNAMIC_FORMS_SCHEMA_MODEL,
                verbose_name='schema',
            ),
        ),
        migrations.AlterField(
            model_name='formresponse',
            name='created_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='%(class)s_form_responses',
                to=settings.AUTH_USER_MODEL,
                verbose_name='created by',
            ),
        ),
        migrations.AlterField(
            model_name='attachment',
            name='response',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='%(class)s_attachments',
                to=settings.DYNAMIC_FORMS_RESPONSE_MODEL,
                verbose_name='response',
            ),
        ),
    ]
