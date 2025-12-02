from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from blog.models import Post


class Command(BaseCommand):
    help = "Print role capability summary for each user against existing posts."

    def handle(self, *args, **options):
        User = get_user_model()
        users = User.objects.all()
        posts = Post.objects.all()
        if not posts.exists():
            self.stdout.write(self.style.WARNING("No posts found. Run create_author_posts first."))
            return

        for user in users:
            role = (
                "admin" if user.is_superuser else
                "author" if user.is_author and user.is_staff else
                "user"
            )
            own_ids = set(posts.filter(author=user).values_list('id', flat=True))
            can_add = (user.is_superuser or (user.is_author and user.is_staff))
            can_publish = can_add  # limited further by ownership in admin code
            can_soft_delete = can_add
            editable = [p.id for p in posts if p.author == user and can_add]
            read_only = [p.id for p in posts if p.author != user]
            self.stdout.write(f"User: {user.email} | Role: {role}")
            self.stdout.write(f"  Own posts: {sorted(list(own_ids))}")
            self.stdout.write(f"  Editable post IDs: {editable}")
            self.stdout.write(f"  Read-only post IDs: {read_only}")
            self.stdout.write(f"  Can add: {can_add} | Can publish own: {can_publish} | Can soft delete own: {can_soft_delete}")
            self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Role diagnostics complete."))