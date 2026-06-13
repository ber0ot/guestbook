# guestbook

Гостевая книга на FastAPI с MySQL за nginx. Сборка, публикация и развёртывание
автоматизированы через GitLab CI/CD, Kubernetes и Argo CD.

## Эндпоинты

- `GET /health` — приложение запущено
- `GET /db-check` — доступность БД
- `GET /version` — версия приложения
- `POST /messages`, `GET /messages` — записи

## Структура

```
app/                код приложения
nginx/              reverse proxy для Compose
k8s/                манифесты Kubernetes
argocd/             Argo CD Application
ansible/            подготовка хостов
Dockerfile
docker-compose.yml
.gitlab-ci.yml
```

## Локальный запуск

```bash
cp .env.example .env
docker compose up --build -d
curl http://localhost:8080/health
curl -X POST http://localhost:8080/messages \
     -H "Content-Type: application/json" \
     -d '{"author":"Алла","text":"Привет"}'
curl http://localhost:8080/messages
```

Наружу открыт только nginx (порт 8080).

## Kubernetes

```bash
kubectl create namespace diploma
kubectl create secret generic guestbook-secret -n diploma \
  --from-literal=DB_NAME=guestbook \
  --from-literal=DB_USER=guestbook \
  --from-literal=DB_PASSWORD=... \
  --from-literal=MYSQL_ROOT_PASSWORD=...
kubectl apply -f k8s/
kubectl get svc nginx -n diploma
```

Внешний адрес приложения — в EXTERNAL-IP сервиса nginx.

GitOps: применить argocd/application.yaml (указав URL репозитория), дальше
Argo CD синхронизирует кластер по каталогу k8s/.
