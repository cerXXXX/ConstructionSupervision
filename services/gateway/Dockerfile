FROM nginx:1.27-alpine

# Контекст сборки — корень репозитория, как у всех сервисов: одно правило на всех.
COPY services/gateway/nginx.conf /etc/nginx/conf.d/default.conf
COPY services/gateway/swagger /usr/share/nginx/swagger
COPY services/gateway/html /usr/share/nginx/html

EXPOSE 80
