# # import os
# # from fastapi import FastAPI
# # from django.core.asgi import get_asgi_application
# # from fastapi.middleware.wsgi import WSGIMiddleware

# # # Set default Django settings
# # os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

# # # Create FastAPI app
# # fastapi_app = FastAPI()

# # # Import and include your FastAPI routes
# # from fastapi_auth.routes import auth
# # fastapi_app.include_router(auth.router)

# # # Combine with Django
# # django_app = get_asgi_application()
# # fastapi_app.mount("/", WSGIMiddleware(django_app))

# # # This is what Uvicorn uses
# # application = fastapi_app
# import os
# from fastapi import FastAPI
# from django.core.asgi import get_asgi_application
# from fastapi.middleware.wsgi import WSGIMiddleware
# from fastapi_auth.routes import auth

# # Set Django settings
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

# # Setup FastAPI
# fastapi_app = FastAPI(
#     title="FastAPI Auth + Django Integration",
#     version="1.0.0"
# )

# # Include your FastAPI routes under /api
# fastapi_app.include_router(auth.router, prefix="/api")

# # Setup Django ASGI
# django_app = get_asgi_application()

# # Mount Django at /
# application = FastAPI()
# application.mount("/", WSGIMiddleware(django_app))     # Django handles /
# application.mount("/api", fastapi_app)                 # FastAPI handles /api/*
# import os
# from fastapi import FastAPI
# from django.core.asgi import get_asgi_application
# from fastapi_auth.routes import auth

# # Set the default Django settings module
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

# # Create Django ASGI app
# django_app = get_asgi_application()

# # Create FastAPI app and include routes
# fastapi_app = FastAPI(
#     title="FastAPI Auth + Django Integration",
#     docs_url="/api/docs",             # Swagger UI
#     redoc_url="/api/redoc",           # ReDoc UI
#     openapi_url="/api/openapi.json"   # OpenAPI schema
# )
# fastapi_app.include_router(auth.router, prefix="/api")

# # Mount FastAPI app under /api path using Starlette
# from starlette.applications import Starlette
# from starlette.routing import Mount

# application = Starlette(
#     routes=[
#         Mount("/api", app=fastapi_app),   # FastAPI routes
#         Mount("/", app=django_app),       # Django handles the rest
#     ]
# )
from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html

# Set this when FastAPI is mounted on a subpath (like /api)
fastapi_app = FastAPI(
    title="FastAPI Auth + Django Integration",
    version="1.0.0",
    docs_url=None,  # disable default docs
    redoc_url=None  # disable redoc
)

# Custom docs route
@fastapi_app.get("/docs", include_in_schema=False)
async def custom_swagger_ui():
    return get_swagger_ui_html(openapi_url="/api/openapi.json", title="FastAPI Docs")
