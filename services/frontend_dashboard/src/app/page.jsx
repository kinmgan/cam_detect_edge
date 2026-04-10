// services/frontend_dashboard/src/App.jsx
"use client";

import React, { useEffect, useRef, useState } from 'react';
import { createMetadataSocket } from './api_client';
import './globals.css';

function Page() {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    // 1. Kết nối WebSocket nhận Metadata [Task 4]
    const socket = createMetadataSocket((data) => {
      drawDetections(data.detections.yolo11_default);
      if (data.detections.yolo11_default.length > 0) {
          addAlert(data.camera_id, data.detections.yolo11_default);
      }
    });

    // 2. Thiết lập WebRTC (Sử dụng API của MediaMTX) [Task 4]
    // Giả sử mediamtx đang chạy tại localhost:8889
    const webrtcURL = 'http://localhost:8889/cam1/whep'; 
    // Lưu ý: Thực tế bạn sẽ dùng thư viện của MediaMTX hoặc WHEP client
    
    return () => socket.close();
  }, []);

  const drawDetections = (detections) => {
    const ctx = canvasRef.current.getContext('2d');
    ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
    
    ctx.strokeStyle = '#00ff00';
    ctx.lineWidth = 2;
    ctx.font = '16px Arial';
    ctx.fillStyle = '#00ff00';

    detections.forEach(det => {
      const [x, y, w, h] = det.bbox; // Tọa độ từ Redis 
      ctx.strokeRect(x, y, w, h);
      ctx.fillText(`${det.label} ${det.score}`, x, y - 5);
    });
  };

  const addAlert = (camId, dets) => {
      const msg = `Phát hiện ${dets.length} đối tượng tại ${camId}`;
      setAlerts(prev => [msg, ...prev].slice(0, 5)); // Lưu 5 cảnh báo mới nhất 
  };

  return (
    <div className="dashboard-container">
      <header><h1>AI Camera Edge Dashboard (RTX 4070)</h1></header>
      
      <div className="main-layout">
        <div className="video-wrapper">
          {/* Luồng Video gốc mượt mà  */}
          <video ref={videoRef} autoPlay muted playsInline className="live-video" />
          {/* Lớp vẽ AI đè lên  */}
          <canvas ref={canvasRef} width="1920" height="1080" className="overlay-canvas" />
        </div>

        <div className="sidebar">
          <h3>Cảnh báo thời gian thực</h3>
          <ul>
            {alerts.map((a, i) => <li key={i} className="alert-item">{a}</li>)}
          </ul>
        </div>
      </div>
    </div>
  );
}

export default Page;
