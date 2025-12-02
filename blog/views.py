from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from .models import Post, Comment

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
def add_comment_api(request, pk):
    # Require authenticated user
    if not request.user.is_authenticated or not request.user.is_active:
        return JsonResponse({"error": "authentication required"}, status=401)

    post = get_object_or_404(Post, pk=pk, deleted_at__isnull=True)
    content = (request.POST.get('content') or '').strip()
    if not content:
        return JsonResponse({"error": "content required"}, status=400)

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

@csrf_exempt
@require_POST
def reply_comment_api(request, comment_id):
    # Require authenticated user
    if not request.user.is_authenticated or not request.user.is_active:
        return JsonResponse({"error": "authentication required"}, status=401)

    parent = get_object_or_404(Comment, pk=comment_id, deleted_at__isnull=True)
    post = parent.post
    content = (request.POST.get('content') or '').strip()
    if not content:
        return JsonResponse({"error": "content required"}, status=400)

    c = Comment.objects.create(
        post=post,
        user=request.user,
        parent=parent,
        content=content,
        created_by=request.user.email,
        updated_by=request.user.email,
    )
    return JsonResponse({
        "id": c.id,
        "post_id": post.id,
        "parent_id": parent.id,
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
        return JsonResponse({"error": "invalid credentials"}, status=401)
    login(request, user)
    return JsonResponse({"status": "ok", "user": username})


# middleware handles cookie based session 
# authenticateview message 