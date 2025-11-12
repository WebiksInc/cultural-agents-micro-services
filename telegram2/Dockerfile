from node:22-alpine
WORKDIR /app

copy ./dist ./
copy ./package.json ./
copy ./package-lock.json ./
copy ./node_modules ./node_modules

EXPOSE 4000

ENV NODE_ENV=production
ENV PORT=4000
ENV DATA_DIR=/app/data

CMD ["node", "server.js"]
