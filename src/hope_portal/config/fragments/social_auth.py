from .. import env

AZURE_CLIENT_ID = env("AZURE_CLIENT_ID")
AZURE_CLIENT_SECRET = env("AZURE_CLIENT_SECRET")
AZURE_TENANT_ID = env("AZURE_TENANT_ID")
SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_KEY = AZURE_CLIENT_ID
SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_SECRET = AZURE_CLIENT_SECRET
SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_TENANT_ID = AZURE_TENANT_ID

SOCIAL_AUTH_ADMIN_USER_SEARCH_FIELDS = [
    "username",
    "first_name",
    "last_name",
    "email",
]

SOCIAL_AUTH_JSONFIELD_ENABLED = True
SOCIAL_AUTH_URL_NAMESPACE = "social"
SOCIAL_AUTH_PIPELINE = (
    "social_core.pipeline.social_auth.social_uid",
    "social_core.pipeline.social_auth.auth_allowed",
    "social_core.pipeline.social_auth.social_user",
    "social_core.pipeline.user.get_username",
    "social_core.pipeline.social_auth.associate_user",
    "social_core.pipeline.social_auth.load_extra_data",
    "social_core.pipeline.user.user_details",
    "hope_portal.modules.social.pipeline.save_to_group",
)
SOCIAL_AUTH_AZUREAD_B2C_OAUTH2_USER_FIELDS = [
    "email",
    "fullname",
]

SOCIAL_AUTH_AZUREAD_B2C_OAUTH2_SCOPE = [
    "openid",
    "email",
    "profile",
]

SOCIAL_AUTH_SANITIZE_REDIRECTS = True
