from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = "Create or update an admin user with a known password"

    def add_arguments(self, parser):
        parser.add_argument("email", nargs="?", default="admin@example.com")
        parser.add_argument("password", nargs="?", default="admin123")

    def handle(self, *args, **options):
        User = get_user_model()
        email = options["email"]
        password = options["password"]

        user, created = User.objects.get_or_create(email=email, defaults={
            "name": "Admin",
            "is_author": True,
            "is_staff": True,
            "is_superuser": True,
            "is_active": True,
        })
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save()
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created admin user {email}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Updated admin user {email}"))
