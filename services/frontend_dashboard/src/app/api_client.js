import { edgeWsMetadataUrl } from './edgeEndpoints';

export const createMetadataSocket = (onMessage) => {
    const socket = new WebSocket(edgeWsMetadataUrl());

    socket.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            onMessage(data);
        } catch (e) {
            console.error("Lỗi parse dữ liệu WebSocket:", e);
        }
    };

    socket.onclose = () => {
        console.log("WebSocket bị ngắt. Đang thử kết nối lại sau 3 giây...");
        setTimeout(() => createMetadataSocket(onMessage), 3000);
    };

    socket.onerror = (err) => {
        console.error("Lỗi kết nối WebSocket:", err);
    };

    return socket;
};