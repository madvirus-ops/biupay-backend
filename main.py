from fastapi import FastAPI, Depends, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware import Middleware
from routers import payments,admin

# print(datetime.now())

# middleware = [
#     Middleware(
#         CORSMiddleware,
#         allow_origins=["*"],
#         allow_credentials=True,
#         allow_methods=["*"],
#         allow_headers=["*"],
#     )
# ]


app = FastAPI(
    title="Backend APIs",
    debug=True,
    description="API endpoints for biupay backend (..))",
    version="1.0.0",
    # middleware=middleware,
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
)

app.include_router(payments.router)
app.include_router(admin.router)