import factory
from faker import Faker
from .models import Post, Comment
from accounts.models import CustomUser

fake = Faker()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CustomUser

    email = factory.LazyAttribute(lambda x: fake.unique.email())
    mobile = factory.LazyAttribute(lambda x: fake.phone_number())
    is_author = True
    password = "password123"
    created_by = "system@seed.com"
    updated_by = "system@seed.com"


class PostFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Post

    author_id = 1
    title = factory.LazyAttribute(lambda x: fake.sentence())
    content = factory.LazyAttribute(lambda x: fake.text())
    status = "published"
    created_by = "system@seed.com"
    updated_by = "system@seed.com"


class CommentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Comment

    post = factory.SubFactory(PostFactory)
    user_id = 1
    content = factory.LazyAttribute(lambda x: fake.sentence())
    created_by = "system@seed.com"
    updated_by = "system@seed.com"
