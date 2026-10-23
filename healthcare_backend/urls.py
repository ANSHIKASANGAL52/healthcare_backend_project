from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView


def api_root(request):
    """
    Health check and root API metadata endpoint.
    """
    return JsonResponse({
        "name": "Healthcare Backend API",
        "version": "1.0.0",
        "status": "healthy",
        "documentation": "/api/docs/",
        "endpoints": {
            "auth": {
                "register": "/api/auth/register/",
                "login": "/api/auth/login/"
            },
            "patients": "/api/patients/",
            "doctors": "/api/doctors/",
            "mappings": "/api/mappings/"
        }
    })


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', api_root, name='api-root'),

    # API Documentation (Swagger & ReDoc)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Application APIs
    path('api/', include('apps.accounts.urls')),
    path('api/', include('apps.patients.urls')),
    path('api/', include('apps.doctors.urls')),
    path('api/', include('apps.mappings.urls')),
]
