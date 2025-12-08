from dataclasses import dataclass
from enum import Enum
from typing import Dict, Set


class Role(str, Enum):
    ADMIN = "admin"
    AUTHOR = "author"
    USER = "user"  # authenticated non-author
    ANON = "anon"  # unauthenticated


class Permission(str, Enum):
    ADMIN_ACCESS = "admin.access"
    POST_VIEW = "post.view"
    POST_ADD = "post.add"
    POST_CHANGE_OWN = "post.change.own"
    POST_DELETE_OWN = "post.delete.own"
    COMMENT_VIEW = "comment.view"
    COMMENT_ADD = "comment.add"
    COMMENT_CHANGE_OWN = "comment.change.own"
    COMMENT_DELETE_OWN = "comment.delete.own"


# Central role -> permission grants (coarse-grained)
ROLE_GRANTS: Dict[Role, Set[Permission]] = {
    Role.ADMIN: set(p for p in Permission),  # full access
    Role.AUTHOR: {
        Permission.ADMIN_ACCESS,
        Permission.POST_VIEW,
        Permission.POST_ADD,
        Permission.POST_CHANGE_OWN,
        Permission.POST_DELETE_OWN,
        Permission.COMMENT_VIEW,
        Permission.COMMENT_ADD,
        Permission.COMMENT_CHANGE_OWN,
        Permission.COMMENT_DELETE_OWN,
    },
    Role.USER: {
        Permission.ADMIN_ACCESS,
        Permission.POST_VIEW,
        Permission.COMMENT_VIEW,
        Permission.COMMENT_ADD,
        Permission.COMMENT_CHANGE_OWN,
        Permission.COMMENT_DELETE_OWN,
    },
}


@dataclass
class Policy:
    user: any

    # Role resolution
    def role(self) -> Role:
        if not bool(getattr(self.user, "is_authenticated", False)) or not bool(getattr(self.user, "is_active", False)):
            return Role.ANON
        if bool(getattr(self.user, "is_superuser", False)):
            return Role.ADMIN
        if bool(getattr(self.user, "is_author", False)):
            return Role.AUTHOR
        return Role.USER

    # Permission check helper (admins get all by grant table)
    def has(self, perm: Permission) -> bool:
        return perm in ROLE_GRANTS.get(self.role(), set())

    # Generic object-ownership helper
    def is_owner(self, obj, owner_attr: str) -> bool:
        return obj is not None and getattr(obj, owner_attr, None) == self.user

    # Admin access
    def can_access_admin(self) -> bool:
        return self.has(Permission.ADMIN_ACCESS)

    # Post
    def can_view_post(self, obj=None) -> bool:
        return self.has(Permission.POST_VIEW)

    def can_add_post(self) -> bool:
        return self.has(Permission.POST_ADD)

    def can_change_post(self, obj=None) -> bool:
        return self.has(Permission.POST_CHANGE_OWN) and (obj is None or self.is_owner(obj, "author"))

    def can_delete_post(self, obj=None) -> bool:
        return self.has(Permission.POST_DELETE_OWN) and (obj is None or self.is_owner(obj, "author"))

    # Comment
    def can_view_comment(self, obj=None) -> bool:
        return self.has(Permission.COMMENT_VIEW)

    def can_add_comment(self) -> bool:
        return self.has(Permission.COMMENT_ADD)

    def can_change_comment(self, obj=None) -> bool:
        return self.has(Permission.COMMENT_CHANGE_OWN) and (obj is None or self.is_owner(obj, "user"))

    def can_delete_comment(self, obj=None) -> bool:
        return self.has(Permission.COMMENT_DELETE_OWN) and (obj is None or self.is_owner(obj, "user"))

    # Readonly helpers used by admin UI
    def readonly_post_fields(self, obj=None, model=None):
        # Admin: no readonly
        if self.role() is Role.ADMIN:
            return []
        # Non-authenticated and normal users: always readonly
        if self.role() in {Role.ANON, Role.USER}:
            return [f.name for f in model._meta.fields] if model else []
        # Author: readonly if editing someone else's post
        if obj is not None and not self.is_owner(obj, "author"):
            return [f.name for f in model._meta.fields] if model else []
        return []

    def readonly_comment_fields(self, obj=None, model=None):
        if self.role() is Role.ADMIN:
            return []
        # Users can edit their own comment; otherwise readonly
        if obj is not None and not self.is_owner(obj, "user"):
            return [f.name for f in model._meta.fields] if model else []
        return []
