FROM node:22-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --omit=dev --no-audit --no-fund
COPY app.js inventory.js ./
COPY data ./data
USER node
EXPOSE 3050
CMD ["node", "app.js"]
