FROM nginx:alpine

# Copy frontend files into nginx default web root
COPY ./index.html /usr/share/nginx/html/

# Copy custom nginx config that proxies /api → backend
COPY ./nginx.conf /etc/nginx/conf.d/default.conf
