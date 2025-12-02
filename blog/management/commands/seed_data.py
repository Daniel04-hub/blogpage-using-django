from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
import random

from blog.models import Post, Comment  # UPDATE appname


try:
    from faker import Faker
    fake = Faker()
    USE_FAKER = True
except Exception:
    fake = None
    USE_FAKER = False


class Command(BaseCommand):
    help = "Seed database with Users (5), Posts (10), Comments (30)"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("Deleting old data..."))
        Comment.objects.all().delete()
        Post.objects.all().delete()
        User = get_user_model()
        User.objects.all().delete()

        self.stdout.write(self.style.SUCCESS("Old data removed."))

        # ============================================
        # CREATE USERS (5)
        # ============================================
        users = []
        base_emails = [
            "alice@example.com",
            "bob@example.com",
            "carol@example.com",
            "dave@example.com",
            "erin@example.com",
        ]
        for i in range(5):
            if USE_FAKER:
                name = fake.name()
                email = fake.unique.email()
                mobile = str(fake.random_number(digits=10))
                is_author = fake.boolean()
                created_by = fake.email()
                updated_by = fake.email()
            else:
                name = ["Alice", "Bob", "Carol", "Dave", "Erin"][i]
                email = base_emails[i]
                mobile = f"90000000{i}"
                is_author = True if i % 2 == 0 else False
                created_by = "seed@system.local"
                updated_by = "seed@system.local"

            user = User.objects.create_user(
                email=email,
                password="password123",
                name=name,
                is_author=is_author,
                mobile=mobile,
                created_at=timezone.now(),
                updated_at=timezone.now(),
                deleted_at=None,
                created_by=created_by,
                updated_by=updated_by,
            )
            users.append(user)

        self.stdout.write(self.style.SUCCESS("5 Users created."))

        # ============================================
        # CREATE POSTS (10)
        # ============================================
        posts = []
        statuses = ["draft", "published", "archived"]

        for i in range(10):
            author = random.choice(users)
            if USE_FAKER:
                title = fake.sentence()
                content = fake.paragraph(nb_sentences=8)
            else:
                title = f"Sample Post {i+1}"
                content = "This is a sample post body used for seeding without Faker."

            post = Post.objects.create(
                author=author,
                title=title,
                content=content,
                status=random.choice(statuses),
                created_at=timezone.now(),
                updated_at=timezone.now(),
                deleted_at=None,
                created_by=author.email,
                updated_by=author.email,
            )
            posts.append(post)

        self.stdout.write(self.style.SUCCESS("10 Posts created."))

        # ============================================
        # CREATE COMMENTS (30)
        # ============================================
        for i in range(30):
            post = random.choice(posts)
            user = random.choice(users)
            if USE_FAKER:
                content = fake.paragraph(nb_sentences=3)
            else:
                content = f"Seeded comment #{i+1} without Faker."

            Comment.objects.create(
                post=post,
                user_id=user.id,
                content=content,
                created_at=timezone.now(),
                updated_at=timezone.now(),
                deleted_at=None,
                created_by=user.email,
                updated_by=user.email,
            )

        self.stdout.write(self.style.SUCCESS("30 Comments created."))
        self.stdout.write(self.style.SUCCESS("Database seeding completed successfully!"))
