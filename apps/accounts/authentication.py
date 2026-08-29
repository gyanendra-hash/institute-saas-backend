from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed, InvalidToken
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import Token
from rest_framework_simplejwt.utils import get_md5_hash_password

from apps.tenants.middleware import get_current_tenant


class TenantAwareJWTAuthentication(JWTAuthentication):
    """SimpleJWT's default get_user() resolves the token's subject via
    `self.user_model.objects` -- the tenant-scoped default manager, which
    returns nothing unless a tenant has already been resolved for this
    request (TenantMiddleware only does that on a real tenant subdomain).
    On every exempt host -- localhost, admin/www, and Render's bare
    *.onrender.com domain, which has no wildcard DNS for subdomains -- that
    means a perfectly valid access token still fails auth with
    "User not found", because the lookup silently returns .none().

    Look the token's own subject up unscoped, then re-apply the same
    tenant check TenantAwareAuthBackend already applies at login: exempt
    host (no tenant resolved) -- any tenant's user may authenticate, same
    as login already allows there; a real tenant subdomain -- only that
    tenant's own users. Doing the lookup fully unscoped without this check
    would let a valid token from tenant A authenticate successfully
    against tenant B's subdomain, since nothing else here verifies the
    token's subject actually belongs to the resolved tenant.
    """

    def get_user(self, validated_token: Token):
        try:
            user_id = validated_token[api_settings.USER_ID_CLAIM]
        except KeyError:
            raise InvalidToken("Token contained no recognizable user identification")

        try:
            user = self.user_model.all_objects.get(**{api_settings.USER_ID_FIELD: user_id})
        except self.user_model.DoesNotExist:
            raise AuthenticationFailed("User not found", code="user_not_found")

        current_tenant = get_current_tenant()
        if current_tenant is not None and user.tenant_id != current_tenant.id:
            raise AuthenticationFailed("User not found", code="user_not_found")

        if not user.is_active:
            raise AuthenticationFailed("User is inactive", code="user_inactive")

        if api_settings.CHECK_REVOKE_TOKEN:
            if validated_token.get(
                api_settings.REVOKE_TOKEN_CLAIM
            ) != get_md5_hash_password(user.password):
                raise AuthenticationFailed(
                    "The user's password has been changed.", code="password_changed"
                )

        return user
