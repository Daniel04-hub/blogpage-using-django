from .factories import UserFactory, PostFactory, CommentFactory

def run():
    print("Seeding database...")

    # Create Users
    users = UserFactory.create_batch(5)

    # Create Posts
    posts = PostFactory.create_batch(10)

    # Create Comments
    for post in posts:
        CommentFactory.create_batch(3, post=post)

    print("Seeding done!")
