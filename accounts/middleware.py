from .policies import Policy

class PolicyMiddleware:
    """
    Attaches a Policy object to each request as `request.policy`.
    Policy chain prioritizes `is_superuser` first, then other common checks.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        request.policy = Policy(user)
        return self.get_response(request)
