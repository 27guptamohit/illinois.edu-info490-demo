import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Section',
            fields=[
                ('section_id', models.AutoField(primary_key=True, serialize=False)),
                ('code', models.CharField(max_length=10, unique=True)),
                ('name', models.CharField(max_length=60)),
                ('term', models.CharField(blank=True, max_length=16)),
            ],
        ),
        migrations.CreateModel(
            name='Student',
            fields=[
                ('student_id', models.AutoField(primary_key=True, serialize=False)),
                ('first_name', models.CharField(max_length=45)),
                ('last_name', models.CharField(max_length=45)),
                ('nickname', models.CharField(blank=True, default='', max_length=45)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('section', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='learners', to='students.section')),
            ],
        ),
        migrations.CreateModel(
            name='Enrollment',
            fields=[
                ('enroll_id', models.AutoField(primary_key=True, serialize=False)),
                ('enrolled_on', models.DateField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True)),
                ('section', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='enrollments', to='students.section')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enrollments', to='students.student')),
            ],
        ),
    ]
