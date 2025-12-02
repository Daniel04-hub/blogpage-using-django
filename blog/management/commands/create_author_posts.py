from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from blog.models import Post


class Command(BaseCommand):
    help = "Create sample posts for each author user (draft & published)."

    def add_arguments(self, parser):
        parser.add_argument("--per", type=int, default=2, help="Posts per author")

    def handle(self, *args, **options):
        User = get_user_model()
        authors = User.objects.filter(is_author=True)
        per = options["per"]
        created = 0
        for author in authors:
            for i in range(per):
                status = "published" if i % 2 else "draft"
                Post.objects.create(
                    author=author,
                    title=f"Sample {status.title()} Post {i+1} by {author.email}",
                    content=f"Auto-generated {status} post {i+1} for {author.email}.",
                    status=status,
                    created_at=timezone.now(),
                    updated_at=timezone.now(),
                    created_by=author.email,
                    updated_by=author.email,
                )
                created += 1
        self.stdout.write(self.style.SUCCESS(f"Created {created} posts for {authors.count()} authors."))