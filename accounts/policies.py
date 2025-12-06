from dataclasses import dataclass
from typing import Optional


@dataclass
class Policy:
    user: any

    # Base checks
    def is_authenticated_active(self) -> bool:
        return bool(getattr(self.user, "is_authenticated", False)) and bool(getattr(self.user, "is_active", False))

    def is_superuser(self) -> bool:
        return bool(getattr(self.user, "is_superuser", False))

    def is_author(self) -> bool:
        return bool(getattr(self.user, "is_author", False))

    # Admin access policy (first layer: superuser)
    def can_access_admin(self) -> bool:
        if self.is_superuser():
            return True
        return self.is_authenticated_active()

    # Post permissions
    def can_view_post(self, obj=None) -> bool:
        if self.is_superuser():
            return True
        return self.is_authenticated_active()

    def can_add_post(self) -> bool:
        if self.is_superuser():
            return True
        return self.is_author()

    def can_change_post(self, obj=None) -> bool:
        if self.is_superuser():
            return True
        if obj is None:
            return self.is_author()
        return self.is_author() and getattr(obj, "author", None) == self.user

    def can_delete_post(self, obj=None) -> bool:
        if self.is_superuser():
            return True
        if obj is None:
            return self.is_author()
        return self.is_author() and getattr(obj, "author", None) == self.user

    def readonly_post_fields(self, obj=None, model=None):
        if self.is_superuser():
            return []
        # regular user always readonly
        if not self.is_author():
            return [f.name for f in model._meta.fields] if model else []
        # author viewing others' post is readonly
        if obj is not None and getattr(obj, "author", None) != self.user:
            return [f.name for f in model._meta.fields] if model else []
        return []

    # Comment permissions
    def can_view_comment(self, obj=None) -> bool:
        if self.is_superuser():
            return True
        return self.is_authenticated_active()

    def can_add_comment(self) -> bool:
        return self.is_authenticated_active()

    def can_change_comment(self, obj=None) -> bool:
        if self.is_superuser():
            return True
        if obj is None:
            # Access change views when authenticated (ownership enforced at object level)
            return self.is_authenticated_active()
        # Any authenticated user can change their own comments
        return self.is_authenticated_active() and getattr(obj, "user", None) == self.user

    def can_delete_comment(self, obj=None) -> bool:
        if self.is_superuser():
            return True
        if obj is None:
            # Allow delete access page for authenticated; enforce ownership for concrete objects
            return self.is_authenticated_active()
        # Any authenticated user can delete their own comments
        return self.is_authenticated_active() and getattr(obj, "user", None) == self.user

    def readonly_comment_fields(self, obj=None, model=None):
        if self.is_superuser():
            return []
        # Regular users can edit their own comment; otherwise read-only
        if obj is not None and getattr(obj, "user", None) != self.user:
            return [f.name for f in model._meta.fields] if model else []
        return []
