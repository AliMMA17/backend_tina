"""Authentication HTTP endpoints."""

from fastapi import APIRouter, status

from src.application.dto.auth import (
    LoginUserDTO,
    RefreshTokenDTO,
    RegisterUserDTO,
)
from src.presentation.api.dependencies import (
    LoginUserUC,
    RefreshTokenUC,
    RegisterUserUC,
)
from src.presentation.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(
    body: RegisterRequest,
    use_case: RegisterUserUC,
) -> RegisterResponse:
    dto = RegisterUserDTO(
        username=body.username,
        password=body.password,
        full_name=body.full_name,
        phone_number=body.phone_number,
        full_address=body.full_address,
        job=body.job,
        work_page=body.work_page,
        income=body.income,
    )
    result = await use_case.execute(dto)
    return RegisterResponse.model_validate(result)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and issue JWT tokens",
)
async def login(
    body: LoginRequest,
    use_case: LoginUserUC,
) -> TokenResponse:
    dto = LoginUserDTO(
        username=body.username,
        password=body.password,
    )
    result = await use_case.execute(dto)
    return TokenResponse.model_validate(result)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access and refresh tokens",
)
async def refresh_tokens(
    body: RefreshTokenRequest,
    use_case: RefreshTokenUC,
) -> TokenResponse:
    dto = RefreshTokenDTO(refresh_token=body.refresh_token)
    result = await use_case.execute(dto)
    return TokenResponse.model_validate(result)
