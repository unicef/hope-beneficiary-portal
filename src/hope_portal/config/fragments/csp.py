CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        "default-src": (
            "'self'",
            "inline",
            "unsafe-inline",
            "data:",
            "blob:",
            "'unsafe-inline'",
            "localhost:8000",
            "unpkg.com",
            "browser.sentry-cdn.com",
            "cdnjs.cloudflare.com",
            "unisitetracker.unicef.io",
            "cdn.jsdelivr.net",
            "register.unicef.org",
            "uni-hope-ukr-sr.azurefd.net",
            "uni-hope-ukr-sr-dev.azurefd.net",
            "uni-hope-ukr-sr-dev.unitst.org",
        ),
        "frame-ancestors": ("'self'",),
    }
}
