# 階段 1：建置 Angular 應用
FROM node:20-alpine AS build

WORKDIR /app

# 複製 package.json 並安裝依賴
COPY package*.json ./
RUN npm install

# 複製源代碼
COPY . .

# 建置 Angular 應用
RUN npm run build

# 階段 2：使用 Nginx 提供靜態檔案
FROM nginx:alpine

# 複製建置好的檔案到 Nginx
COPY --from=build /app/dist/attachment3-manager /usr/share/nginx/html

# 複製 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 開放端口
EXPOSE 80

# 啟動 Nginx
CMD ["nginx", "-g", "daemon off;"]
