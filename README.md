# Report Checker

Сервис для автоматической проверки учебных PDF-отчетов по набору правил (структура, оформление, нумерация, формулы, таблицы и т.д.) с веб-интерфейсом и хранением файлов в S3-совместимом хранилище.

## Что делает сервис

- Принимает PDF через веб-интерфейс.
- Проверяет документ набором правил по типу документа (`practice_report`, шаблон ВКР и др.).
- Сохраняет исходный файл и результаты проверок.
- Отдает результаты в интерфейс и через API.
- Позволяет скачать исходник и экспортировать отчет проверки (CSV).
- Поддерживает роли пользователей (`student`, `teacher`, `admin`) и два режима авторизации:
  - `dev` (локальная регистрация/логин),
  - `itmo_id` (OAuth через ITMO.ID).

## Архитектура и компоненты

Стек разворачивается через Docker Compose:

- `backend` — FastAPI, запуск миграций Alembic и API на `:8000`.
- `frontend` — React/Vite, отдается через внутренний nginx на `:80`.
- `postgres` — хранение метаданных, пользователей, правил, результатов проверок.
- `minio` — хранение загруженных PDF.
- `minio-init` — автосоздание bucket при старте.
- `caddy` — единая входная точка и reverse proxy на `:80` (в prod также обрабатывает TLS по шаблону).

Маршрутизация Caddy:

- `/api/*`, `/internal/*`, `/docs`, `/openapi.json`, `/health` -> `backend:8000`
- `/s3/*` -> `minio:9000`
- `/minio-console/*` -> `minio:9001`
- все остальное -> `frontend:80`

## Основные API-эндпоинты

Префикс API: `/api/v1`.

- `GET /auth/mode` — текущий режим авторизации.
- `POST /auth/dev/register`, `POST /auth/dev/login` — dev-авторизация.
- `GET /auth/login`, `GET /auth/callback` — OAuth-флоу ITMO.ID.
- `POST /documents` — загрузка документов и запуск проверок.
- `GET /documents` — список документов (с пагинацией/фильтрами).
- `GET /documents/{id}` — детали документа и результаты проверок.
- `GET /documents/{id}/download` — скачать PDF.
- `GET /documents/{id}/report?format=csv` — экспорт отчета.
- `POST /documents/{id}/checks` — принудительный перезапуск проверок.
- `GET /rules`, `PATCH /rules/{id}` — просмотр/настройка правил (изменение только для admin).
- `GET /health` — health-check.

## Локальный запуск

### Требования

- Docker + Docker Compose plugin (`docker compose`)
- Git

### Команды

1. Подготовить переменные:

```bash
cp backend/.env.example backend/.env
```

2. Поднять стек:

```bash
docker compose up --build -d
```

3. Проверить доступность:

```bash
curl -f http://127.0.0.1/health
```

4. Остановить:

```bash
docker compose down
```

## Развертывание через Ansible

Все шаги выполняются из директории `deploy/` на машине, откуда запускается Ansible.

### 1) Требования к управляющей машине

- Ansible
- `ansible-vault`
- SSH-доступ к целевой VM

### 2) Подготовить файлы конфигурации

```bash
cd deploy
cp group_vars/all/vault.yml.example group_vars/all/vault.yml
```

`vault.yml.example` уже содержит актуальный каркас под текущий стенд.  
Нужно скопировать его в `vault.yml` и заполнить/проверить следующие поля:

- подключение к серверу:
  - `vault_server_host`
  - `vault_deploy_user`
  - `vault_deploy_password` (если используете парольную авторизацию)
  - `vault_ssh_key_path` (если используете ключ)
  - `vault_ssh_common_args` (опционально, для ProxyJump и т.п.)
- репозиторий:
  - `vault_repo_url`
- секреты приложения:
  - `vault_postgres_password`
  - `vault_minio_root_user`
  - `vault_minio_root_password`
  - `vault_jwt_secret_key`
- авторизация:
  - `vault_auth_mode` (`dev` или `itmo_id`)
  - для `itmo_id`: `vault_itmo_id_client_id`, `vault_itmo_id_client_secret`, `vault_itmo_id_redirect_uri`
- домен/TLS:
  - `vault_base_domain` и/или `vault_caddy_domain_override`
  - `vault_caddy_tls_email`
  - `vault_edge_tls_terminated`

Текущие значения в примере по умолчанию:

- `vault_server_host: 192.168.10.86`
- `vault_deploy_user: root`
- `vault_repo_url: https://github.com/vovibssnff/report_checker.git`
- `vault_auth_mode: itmo_id`
- `vault_caddy_domain_override: checker.se.ifmo.ru`
- `vault_edge_tls_terminated: true`

### 3) Зашифровать переменные

```bash
ansible-vault encrypt group_vars/all/vault.yml
```

### 4) Настроить пароль от vault

В `deploy/ansible.cfg` уже указан файл:

- `vault_password_file = .vault_pass`

Создать `deploy/.vault_pass` с паролем от Ansible Vault.

### 5) Проверить inventory

`deploy/inventory.yml` использует значения из `vault.yml`:

- `ansible_host: "{{ vault_server_host }}"`
- `ansible_user: "{{ vault_deploy_user }}"`

Дополнительно можно задать:

- `vault_ssh_common_args` (например, ProxyJump),
- `vault_ssh_key_path`.

### 6) Запустить деплой

```bash
ansible-playbook deploy.yml
```

Что делает playbook:

1. Проверяет, что на сервере доступен `docker compose`.
2. Ставит `git`.
3. Создает каталог приложения (`/opt/report-checker`).
4. Клонирует/обновляет репозиторий (ветка задается `app_repo_branch`, сейчас `sync-checks`).
5. Генерирует `backend/.env` из переменных Ansible.
6. Генерирует `caddy/Caddyfile` по шаблону `deploy/templates/Caddyfile.j2`.
7. Выполняет `docker compose up -d --build --force-recreate --pull always`.

### 7) Проверка после деплоя

На целевой VM:

```bash
cd /opt/report-checker
docker compose ps
docker compose logs --tail=100 caddy
curl -vk https://127.0.0.1/health
```

Если TLS терминируется внешним балансировщиком, а именно это происходит в сети университета (`vault_edge_tls_terminated: true`), проверка может быть через HTTP на `:80`.

## Как обновлять сервис

1. Закоммитить изменения в ветку, указанную в `app_repo_branch` (`deploy/group_vars/all/vars.yml`).
2. Запустить:

```bash
cd deploy
ansible-playbook deploy.yml
```

Playbook сам подтянет изменения и пересоберет контейнеры.

## Текущее развертывание (актуальное состояние)

Текущий target-сервер:

- VM: `192.168.10.86`
- каталог приложения: `/opt/report-checker`
- управление: `ansible-playbook deploy.yml` из этого репозитория
- публичный хост сервиса: `checker.se.ifmo.ru` (через `vault_caddy_domain_override`)
- `vault_edge_tls_terminated: true` (TLS завершается на внешнем контуре, Caddy обслуживает HTTP на `:80`)

Ограничение доступа:

- VM доступна только из сети VPN.
- Конфиг VPN для подключения: [https://se.ifmo.ru/ca/students.ovpn](https://se.ifmo.ru/ca/students.ovpn).

Типовой рабочий цикл сейчас:

1. Поднять VPN:

```bash
sudo openvpn --config ~/Downloads/students.ovpn
```

2. Убедиться в доступе до VM по SSH.
3. Выполнить деплой:

```bash
cd deploy
ansible-playbook deploy.yml
```

По всем вопросам (для получения ключей, токенов и тд) писать в ТГ @mc_vovi

