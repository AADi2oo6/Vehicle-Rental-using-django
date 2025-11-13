# In rental/migrations/0029_customer_is_subscribed_to_newsletter_and_more.py
from django.db import migrations, models
class Migration(migrations.Migration):

    dependencies = [
        ('rental', '0028_alter_customer_password'),
    ]
    ...
    operations = [
        migrations.AlterField(
            model_name='customer',
            name='password',
            field=models.CharField(default='pbkdf2_sha256$870000$zoViJhJ3pMMijVz3jZNida$Aopc9g/Ohuqr7h5PuDZYMTfYEnGEnIjhzDsB1K+e7fs=', max_length=128),
        ),
    ]