from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from accounts.policies import Policy  # middleware attaches request.policy
from django.contrib.auth import authenticate, login
from .models import Post, Comment

# Small helpers to keep views DRY
def json_error(message, status):
    return JsonResponse({"error": message}, status=status)

def get_post_active(pk):
    return get_object_or_404(Post, pk=pk, deleted_at__isnull=True)

def post_list_api(request):
    posts = Post.objects.filter(
        deleted_at__isnull=True,
        status="published"
    ).order_by('-created_at').values('id', 'title', 'author__email', 'status', 'created_at')
    return JsonResponse({"posts": list(posts)})

def _comment_to_dict(c):
    return {
        "id": c.id,
        "user": getattr(c.user, 'email', None),
        "content": c.content,
        "created_at": c.created_at,
        "replies": [
            _comment_to_dict(rc) for rc in c.replies.filter(deleted_at__isnull=True).order_by('created_at')
        ],
    }

def post_detail_api(request, pk):
    post = get_object_or_404(Post, pk=pk, deleted_at__isnull=True, status='published')
    root_comments = post.comments.filter(deleted_at__isnull=True, parent__isnull=True).order_by('created_at')
    comments = [_comment_to_dict(c) for c in root_comments]
    data = {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "author": post.author.email,
        "status": post.status,
        "created_at": post.created_at,
        "comments": comments,
    }
    return JsonResponse(data)

@csrf_exempt
@require_POST
@login_required
def create_post_api(request):
    # Use request.policy RBAC (admin full access; author can add)
    if not getattr(request, "policy", Policy(request.user)).can_add_post():
        return json_error("forbidden", 403)
    title = (request.POST.get("title") or "").strip()
    content = (request.POST.get("content") or "").strip()
    if not title or not content:
        return json_error("title and content required", 400)
    post = Post.objects.create(
        author=request.user,
        title=title,
        content=content,
        status="draft",
        created_by=request.user.email,
        updated_by=request.user.email,
    )
    return JsonResponse({"id": post.id, "status": post.status}, status=201)

@csrf_exempt
@require_POST
@login_required
def update_post_api(request, pk):
    post = get_post_active(pk)
    if not getattr(request, "policy", Policy(request.user)).can_change_post(post):
        return json_error("forbidden", 403)
    title = request.POST.get("title")
    content = request.POST.get("content")
    status = request.POST.get("status")
    if title is not None:
        post.title = title
    if content is not None:
        post.content = content
    if status in {"draft", "published", "archived"}:
        post.status = status
    post.updated_by = request.user.email
    post.save()
    return JsonResponse({"id": post.id, "status": post.status})

@csrf_exempt
@require_POST
@login_required
def delete_post_api(request, pk):
    post = get_post_active(pk)
    if not getattr(request, "policy", Policy(request.user)).can_delete_post(post):
        return json_error("forbidden", 403)
    post.soft_delete()
    post.updated_by = request.user.email
    post.save(update_fields=["updated_by", "deleted_at", "updated_at"])
    return JsonResponse({"id": post.id, "deleted": True})

@csrf_exempt
@require_POST
@login_required
def publish_post_api(request, pk):
    post = get_post_active(pk)
    # Publish restricted: admin or author of the post (simple rule)
    p = getattr(request, "policy", Policy(request.user))
    if not (p.is_superuser() or post.author_id == request.user.id):
        return json_error("forbidden", 403)
    post.status = "published"
    post.updated_by = request.user.email
    post.save(update_fields=["status", "updated_by", "updated_at"])
    return JsonResponse({"id": post.id, "status": post.status})

@csrf_exempt
@require_POST
def add_comment_api(request, pk):
    # Require authenticated active per policy chain
    p = getattr(request, "policy", Policy(request.user))
    if not p.can_add_comment():
        return json_error("authentication required", 401)
    post = get_post_active(pk)
    if post.status != "published":
        return json_error("comments allowed only on published posts", 403)
    content = (request.POST.get('content') or '').strip()
    if not content:
        return json_error("content required", 400)

    c = Comment.objects.create(
        post=post,
        user=request.user,
        content=content,
        created_by=request.user.email,
        updated_by=request.user.email,
    )
    return JsonResponse({
        "id": c.id,
        "post_id": post.id,
        "user": request.user.email,
        "content": c.content,
        "created_at": c.created_at,
    }, status=201)

#-> session login by the middleware
@csrf_exempt#-> middleware actively global
@require_POST
def session_login_api(request):
    """Simple session login for curl: POST username/password returns ok when authenticated."""
    username = (request.POST.get('username') or '').strip()
    password = request.POST.get('password') or ''
    user = authenticate(request, username=username, password=password)
    if not user or not user.is_active:
        return json_error("invalid credentials", 401)
    login(request, user)
    return JsonResponse({"status": "ok", "user": username})

