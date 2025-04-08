from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

User = get_user_model()

class EmailOrUsernameModelBackend(ModelBackend):
    """
    Authenticate against either email or username.
    Improved version with better error handling and querying.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        
        if username is None or password is None:
            return None
            
        try:
            # Use Q objects to search by either username or email
            user = User.objects.get(
                Q(username__iexact=username) | Q(email__iexact=username)
            )
            
            # Check the password
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            # Run the default password hasher once to reduce timing difference
            # between an existing and a non-existing user
            User().set_password(password)
            return None
        except User.MultipleObjectsReturned:
            # In case multiple users have the same email (shouldn't happen with proper validation)
            # Try to find the user with exact username match
            try:
                user = User.objects.get(username=username)
                if user.check_password(password):
                    return user
                return None
            except (User.DoesNotExist, User.MultipleObjectsReturned):
                return None
        
        return None

    def get_user(self, user_id):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
            
        return user if self.user_can_authenticate(user) else None