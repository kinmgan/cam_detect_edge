FROM node:18-alpine

WORKDIR /app

# Tuỳ chọn: ép host API/MediaMTX vào bundle (vd. NEXT_PUBLIC_EDGE_HOST=127.0.0.1)
ARG NEXT_PUBLIC_EDGE_HOST
ARG NEXT_PUBLIC_API_PORT
ARG NEXT_PUBLIC_MEDIAMTX_HTTP_PORT
ENV NEXT_PUBLIC_EDGE_HOST=$NEXT_PUBLIC_EDGE_HOST
ENV NEXT_PUBLIC_API_PORT=$NEXT_PUBLIC_API_PORT
ENV NEXT_PUBLIC_MEDIAMTX_HTTP_PORT=$NEXT_PUBLIC_MEDIAMTX_HTTP_PORT

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