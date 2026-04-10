// services/frontend_dashboard/src/api_client.js
export const createMetadataSocket = (onMessage) => {
    const socket = new WebSocket('ws://localhost:8000/ws/metadata');

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        onMessage(data);
    };

    socket.onclose = () => console.log("WebSocket Closed. Reconnecting...");
    return socket;
};