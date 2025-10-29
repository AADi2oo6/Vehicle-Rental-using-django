from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

UserModel = get_user_model()

class EmailBackend(ModelBackend):
    """
    Authenticates against settings.AUTH_USER_MODEL.
    Allows users to log in using their email address.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Try to fetch the user by searching the username and email fields.
            user = UserModel.objects.get(Q(username__iexact=username) | Q(email__iexact=username))
        except UserModel.DoesNotExist:
            return None
        
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
