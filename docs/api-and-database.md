# Backend API, Auth & Database Reference

## HTTP Endpoints

All `api_router` routes are mounted under `settings.api_v1_prefix` (`/api/v1`).

### Health
- `GET /health` and `GET /api/v1/health` — Public liveness check returning `{"status": "ok"}`.

### Authentication (`/api/v1/auth`)
- `POST /api/v1/auth/register` — Public customer registration (`role` forced to `"customer"`). Returns `201` with `user`, `access_token`, `refresh_token`, `token_type`.
- `POST /api/v1/auth/login` — Authenticates `username` + `password`. Returns `200` with `access_token`, `refresh_token`, `token_type`.
- `POST /api/v1/auth/refresh` — Exchanges a valid refresh token (`type == "refresh"`) for a fresh token pair.

### Users (`/api/v1/users`)
- `GET /api/v1/users?offset=0&limit=50` — **Admin only** (`UserRole.ADMIN`). Returns paginated `UserListResponse` ordered by `created_at DESC`.

### Blogs (`/api/v1/blogs`)
- `GET /api/v1/blogs?offset=0&limit=20` — **Public**. Lists published blogs (`is_published = true`) ordered by `published_at DESC NULLS LAST, created_at DESC`.
- `GET /api/v1/blogs/{slug}` — **Public**. Returns a single published blog by `slug` (`404` if missing or draft).
- `GET /api/v1/blogs/admin?offset=0&limit=20&is_published=` — **Admin only**. Lists all blogs (or filters by `is_published=true|false`).
- `GET /api/v1/blogs/admin/{blog_id}` — **Admin only**. Fetches any blog (published or draft) by UUID.
- `POST /api/v1/blogs` — **Admin only**. Creates a blog (`author_id` set from authenticated admin). If `slug` is omitted, auto-generates a Unicode-friendly slug from `title` (appending a short hex suffix on collision). Returns `201`.
- `PATCH /api/v1/blogs/{blog_id}` — **Admin only**. Partially updates `title`, `slug`, `summary`, `cover_image_url`, `content`, or `is_published`. Passing `null` for `summary` or `cover_image_url` clears the field.
- `DELETE /api/v1/blogs/{blog_id}` — **Admin only**. Deletes a blog (`204 No Content`).

### Media Uploads (`/api/v1/uploads` & `/uploads`)
- `POST /api/v1/uploads/images` — **Admin only**. Accepts `multipart/form-data` (`file`), verifies magic bytes (`JPEG`, `PNG`, `WebP`, `GIF`) and size (`MAX_UPLOAD_SIZE_MB`, default `10`), saves to `UPLOAD_DIR` (`/app/uploads`, host-mounted from `app/uploads/`), and returns `{ filename, url: "/uploads/<uuid>.<ext>", content_type, size_bytes }`.
- `GET /uploads/{filename}` — **Public**. Proxied by Nginx (`gateway/default.conf`) to `backend:8000`, which serves the file from `UPLOAD_DIR` (`app/uploads/` on the host) with immutable cache headers.

## Domain Error → HTTP Status Mapping

Defined in `src/presentation/api/exception_handlers.py`:

| Exception | HTTP Status |
|---|---|
| `EntityNotFoundError` | `404 Not Found` |
| `EntityAlreadyExistsError` | `409 Conflict` |
| `ValidationError` | `422 Unprocessable Entity` |
| `AuthenticationError` | `401 Unauthorized` (`WWW-Authenticate: Bearer`) |
| `AuthorizationError` | `403 Forbidden` |
| `DomainError` (base) | `400 Bad Request` |

## Database Schema & Migrations

### Tables
- **`users`** (`001_create_users_table.py`):
  `id` (UUID PK), `username` (unique, indexed), `hashed_password`, `full_name`, `phone_number` (unique, indexed), `full_address`, `job`, `work_page` (nullable), `income` (nullable), `role` (`'admin' | 'customer'`, default `'customer'`), `is_active` (default `true`), `created_at`, `updated_at`.
- **`blogs`** (`002_create_blogs_table.py`):
  `id` (UUID PK), `title`, `slug` (unique, indexed), `summary` (nullable), `content`, `cover_image_url` (nullable), `is_published` (indexed, default `true`), `published_at` (indexed, nullable), `author_id` (UUID FK → `users.id` `ON DELETE CASCADE`, indexed), `created_at`, `updated_at`.

### Docker Compose Networking (`app/docker-compose/backend.yml`)
- `backend` container runs on `backend_net` (private bridge to `backend-db`) and `gateway_net` (shared with Nginx reverse proxy at `gateway/default.conf`, which forwards `/api/` to `http://backend:8000`).
- `backend` bind-mounts `../uploads:/app/uploads` (host directory `app/uploads/`). `gateway-nginx` proxies `/uploads/` and `/api/` to `http://backend:8000`.
- `db` (`postgres:16-alpine`) runs only on `backend_net`; port `5432` is not published externally.
