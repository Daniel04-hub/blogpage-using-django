from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.auth import get_user_model


ROLE_USERS = [
    ("admin", "admin@example.com", "Admin@12345"),
    ("author", "author1@example.com", "Author@12345"),
    ("author", "author2@example.com", "Author@12345"),
    ("user", "user1@example.com", "User@12345"),
    ("user", "user2@example.com", "User@12345"),
]


class Command(BaseCommand):
    help = "Bootstrap role groups and users with predefined credentials"

    def handle(self, *args, **options):
        User = get_user_model()

        # Create groups
        admin_group, _ = Group.objects.get_or_create(name="Admin")
        author_group, _ = Group.objects.get_or_create(name="Author")
        user_group, _ = Group.objects.get_or_create(name="User")

        # Assign permissions (basic: authors get add/change Post; admin gets all; user none)
        from django.contrib.contenttypes.models import ContentType
        from blog.models import Post, Comment
        post_ct = ContentType.objects.get_for_model(Post)
        comment_ct = ContentType.objects.get_for_model(Comment)

        post_perms = Permission.objects.filter(content_type=post_ct)
        comment_perms = Permission.objects.filter(content_type=comment_ct)

        # Admin: all model permissions
        admin_group.permissions.set(list(post_perms) + list(comment_perms))
        # Author: only add/change/delete own posts logically (Django can't enforce own automatically, so we give add/change/delete; object logic in admin limits it)
        author_group.permissions.set(post_perms)
        # User: read-only via API (no perms assigned)
        user_group.permissions.clear()

        created_accounts = []
        for role, email, pwd in ROLE_USERS:
            if role == "admin":
                user, created = User.objects.get_or_create(email=email, defaults={
                    "name": "Admin User",
                    "is_staff": True,
                    "is_superuser": True,
                    "is_author": True,
                })
                user.groups.add(admin_group)
            elif role == "author":
                user, created = User.objects.get_or_create(email=email, defaults={
                    "name": email.split("@")[0].title(),
                    "is_staff": True,
                    "is_superuser": False,
                    "is_author": True,
                })
                user.groups.add(author_group)
            else:  # regular user
                user, created = User.objects.get_or_create(email=email, defaults={
                    "name": email.split("@")[0].title(),
                    "is_staff": False,
                    "is_superuser": False,
                    "is_author": False,
                })
                user.groups.add(user_group)

            user.set_password(pwd)
            user.is_active = True
            user.save()
            created_accounts.append((role, email, pwd, created))

        self.stdout.write(self.style.SUCCESS("Roles and users bootstrapped."))
        for role, email, pwd, created in created_accounts:
            status = "created" if created else "updated"
            self.stdout.write(f"[{status}] {role}: {email} / {pwd}")