FROM node:22-bookworm-slim
WORKDIR /app
COPY package*.json ./
RUN npm install --omit=dev --no-audit --no-fund
COPY app.js dealership.js review.js ./
COPY data ./data
USER node
EXPOSE 3030
CMD ["node", "app.js"]
