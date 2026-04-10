FROM node:18-alpine

WORKDIR /app

# Copy file quản lý thư viện và cài đặt
COPY package.json package-lock.json* ./
RUN npm install

# Copy toàn bộ source code giao diện
COPY . .

# Build dự án (Nếu dùng Next.js)
RUN npm run build

EXPOSE 3000

# Khởi chạy Frontend
CMD ["npm", "run", "start"]