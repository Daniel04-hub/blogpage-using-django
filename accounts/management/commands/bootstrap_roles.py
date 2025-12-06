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

        # Assign permissions
        from django.contrib.contenttypes.models import ContentType
        from blog.models import Post, Comment
        post_ct = ContentType.objects.get_for_model(Post)
        comment_ct = ContentType.objects.get_for_model(Comment)

        post_perms = Permission.objects.filter(content_type=post_ct)
        comment_perms = Permission.objects.filter(content_type=comment_ct)

        # Specific codenames
        add_post = post_perms.filter(codename="add_post").first()
        change_post = post_perms.filter(codename="change_post").first()
        delete_post = post_perms.filter(codename="delete_post").first()
        publish_post = post_perms.filter(codename="publish_post").first()

        # Admin: all model permissions
        admin_group.permissions.set(list(post_perms) + list(comment_perms))
        # Author: add/change/delete posts (ownership enforced in views/admin); no publish by default
        author_perms = [p for p in [add_post, change_post, delete_post] if p]
        author_group.permissions.set(author_perms)
        
        # Editor: change/publish any post (optional role for publishing workflow)
        editor_group, _ = Group.objects.get_or_create(name="Editor")
        editor_perms = [p for p in [change_post, publish_post] if p]
        editor_group.permissions.set(editor_perms)
        # User: CRUD comments only (add/change/delete comment)
        add_comment = comment_perms.filter(codename="add_comment").first()
        change_comment = comment_perms.filter(codename="change_comment").first()
        delete_comment = comment_perms.filter(codename="delete_comment").first()
        user_group.permissions.set([p for p in [add_comment, change_comment, delete_comment] if p])

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
            elif role == "user":  # regular user
                user, created = User.objects.get_or_create(email=email, defaults={
                    "name": email.split("@")[0].title(),
                    "is_staff": False,
                    "is_superuser": False,
                    "is_author": False,
                })
                user.groups.add(user_group)
            else:
                # Unknown role placeholder
                user, created = User.objects.get_or_create(email=email, defaults={
                    "name": email.split("@")[0].title(),
                    "is_staff": False,
                    "is_superuser": False,
                    "is_author": False,
                })

            user.set_password(pwd)
            user.is_active = True
            user.save()
            created_accounts.append((role, email, pwd, created))

        self.stdout.write(self.style.SUCCESS("Roles and users bootstrapped."))
        for role, email, pwd, created in created_accounts:
            status = "created" if created else "updated"
            self.stdout.write(f"[{status}] {role}: {email} / {pwd}")