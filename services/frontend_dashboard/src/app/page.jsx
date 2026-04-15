"use client";

import React, { useEffect, useRef, useState } from 'react';
import { createMetadataSocket } from './api_client';
import { edgeApiOrigin, edgeWhepUrl } from './edgeEndpoints';
import './globals.css';

const AVAILABLE_MODELS = [
  { id: 'yolo11s.pt', name: 'YOLO11 Small (Cân bằng)' },
  { id: 'yolo11m.pt', name: 'YOLO11 Medium (Chính xác)' }
];

function Page() {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  // Logic so sánh HeadCount
  const lastPersonCount = useRef(-1);
  const [alerts, setAlerts] = useState([]);

  // Cài đặt AI Models
  const [selectedModel, setSelectedModel] = useState(AVAILABLE_MODELS[0].id);

  useEffect(() => {
    // Logic vẽ Bounding box lên Stream Canvas
    const drawDetections = (detections, captureTimestamp) => {
      const canvas = canvasRef.current;
      const video = videoRef.current;
      if (!canvas || !video || !detections) return;

      // TẠM TẮT BỘ LỌC ĐỂ DEBUG (Xem có dữ liệu bò về không)
      if (captureTimestamp) {
        const now = Date.now() / 1000;
        const delay = now - captureTimestamp;
        // console.log(`[Full Debug] Latency: ${delay.toFixed(3)}s`);
        
        /* 
        if (delay > 2.0) {
          const ctx = canvas.getContext('2d');
          ctx.clearRect(0, 0, canvas.width, canvas.height);
          return;
        }
        */
      }

      const ctx = canvas.getContext('2d');

      // Lấy độ phân giải THỰC TẾ của luồng video đang hiển thị trên Chrome
      const vw = video.videoWidth;
      const vh = video.videoHeight;

      // Nếu video chưa load xong (0x0) thì bỏ qua
      if (vw === 0 || vh === 0) return;

      // Đồng bộ kích thước nội bộ của Canvas với Video 1:1
      if (canvas.width !== vw) {
        console.log(`[Sync] Đang đồng bộ Canvas: ${vw}x${vh} (Theo Video) | Trước đó: ${canvas.width}x${canvas.height}`);
        canvas.width = vw;
        canvas.height = vh;
      }

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      detections.forEach((det) => {
        const [x1, y1, x2, y2] = det.bbox;
        const confidence = det.score;
        const objectId = det.object_id;

        // Vẽ Khung (Sử dụng tọa độ tuyệt đối vì Canvas đã được scale 1:1 với Video)
        ctx.strokeStyle = '#00FF00';
        ctx.lineWidth = 4;
        ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);

        // Vẽ Label
        ctx.fillStyle = '#10B981'; // Emerald-500
        const label = `ID:${objectId} (${(confidence * 100).toFixed(0)}%)`;
        ctx.font = 'bold 18px "Courier New", Courier, monospace';
        const textWidth = ctx.measureText(label).width;

        ctx.fillRect(x1 - 2, y1 - 30, textWidth + 10, 30);
        ctx.fillStyle = '#FFFFFF';
        ctx.fillText(label, x1 + 3, y1 - 8);
      });
    };

    // 1. Kết nối WebSocket nhận Metadata
    const socket = createMetadataSocket((data) => {
      console.log("[WS Debug] Nhận dữ liệu:", data); // KIỂM TRA QUAN TRỌNG

      // Vẽ Box lên Stream Canvas
      if (data.detections?.yolo11_default) {
        console.log(`[WS Debug] Có ${data.detections.yolo11_default.length} ô vuông`);
        drawDetections(data.detections.yolo11_default, data.capture_timestamp);
      } else {
        console.warn("[WS Debug] Không có key 'yolo11_default' trong detections", data.detections);
      }

      // Khai thác con số Quantity
      const currentCount = data.metadata?.total_count;

      // Nếu số người hợp lệ và (lần đầu ghi nhận khác -1) VÀ KHÁC SỐ NGƯỜI CŨ
      if (currentCount !== undefined && lastPersonCount.current !== -1 && currentCount !== lastPersonCount.current) {
        const time = new Date().toLocaleTimeString();

        // Đẩy Log Đỏ lên FE
        if (currentCount > lastPersonCount.current) {
          const msg = `🟢 [${time}] Sĩ số TĂNG: ${lastPersonCount.current} ➔ ${currentCount} người (Có học sinh mới vào / Đứng lên)`;
          setAlerts(prev => [msg, ...prev].slice(0, 30));
        } else {
          const msg = `🔴 [${time}] Sĩ số GIẢM: ${lastPersonCount.current} ➔ ${currentCount} người (Trốn học / Đi ra ngoài)`;
          setAlerts(prev => [msg, ...prev].slice(0, 30));
        }
      }

      // Sau khi so sánh xong, gán bằng số lượng hiện tại để theo dõi frame sau
      if (currentCount !== undefined) {
        lastPersonCount.current = currentCount;
      }
    });

    // 2. Thiết lập WebRTC (Sử dụng API WHEP của MediaMTX)
    const webrtcURL = edgeWhepUrl('/cam1/whep');
    const pc = new RTCPeerConnection();
    pc.addTransceiver('video', { direction: 'recvonly' });

    pc.ontrack = (event) => {
      if (videoRef.current) {
        videoRef.current.srcObject = event.streams[0];
      }
    };

    pc.createOffer().then(offer => {
      pc.setLocalDescription(offer);
      return fetch(webrtcURL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/sdp' },
        body: offer.sdp
      });
    }).then(response => {
      if (response.ok) {
        return response.text();
      }
      throw new Error('Không thể kết nối WebRTC MediaMTX');
    }).then(answer => {
      pc.setRemoteDescription({ type: 'answer', sdp: answer });
    }).catch(err => console.error("WebRTC Error:", err));

    return () => {
      socket.close();
      pc.close();
    };
  }, []);

  const handleSwitchModel = async () => {
    try {
      const res = await fetch(`${edgeApiOrigin()}/api/camera/control`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'switch_model', model_name: selectedModel, camera_id: 'cam1' })
      });
      if (res.ok) {
        setAlerts(prev => [`⚡ [${new Date().toLocaleTimeString()}] Đã gửi lệnh bắt bộ nạp đổi model AI thành công!`, ...prev].slice(0, 30));
      }
    } catch (e) {
      console.error(e);
      setAlerts(prev => [`❌ [${new Date().toLocaleTimeString()}] Lỗi không liên lạc được với API Control Backend!`, ...prev].slice(0, 30));
    }
  };

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 p-6 font-sans">
      {/* HEADER TILE */}
      <header className="mb-6 border-b border-neutral-800 pb-4">
        <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
          Smart Classroom Monitor
        </h1>
        <p className="text-neutral-400 text-sm mt-1">Hệ thống AI Edge theo dõi sĩ số trực tiếp </p>
      </header>

      {/* GRID GIAO DIỆN 3/4 Trái (Video) - 1/4 Phải (Logs/Control) */}
      <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">

        {/* === MAIN COLUMN: STREAM VIDEO (CHIẾM 3 CỘT / TRÁI) === */}
        <div className="xl:col-span-3 flex flex-col gap-4">
          {/* Container tỉ lệ 16:9 sử dụng kỹ thuật padding-bottom */}
          <div 
            className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden shadow-2xl"
            style={{ 
              position: 'relative', 
              width: '100%', 
              height: 0, 
              paddingBottom: '56.25%' 
            }}
          >
            {/* Nội dung bên trong container absolute-fill */}
            <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%' }}>
              {/* Lớp Video */}
              <video
                ref={videoRef}
                autoPlay
                muted
                playsInline
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: '100%',
                  objectFit: 'contain',
                  zIndex: 0
                }}
              />

              {/* Lớp Canvas */}
              <canvas
                ref={canvasRef}
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: '100%',
                  objectFit: 'contain',
                  pointerEvents: 'none',
                  zIndex: 10
                }}
              />

              {/* Badge Báo Live */}
              <div className="absolute top-4 left-4 bg-black/60 backdrop-blur-md px-3 py-1.5 rounded-md text-xs font-mono text-emerald-400 border border-emerald-500/30 flex items-center gap-2 z-20">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                LIVE VIEW - LỚP A1
              </div>
            </div>
          </div>
        </div>

        {/* === SIDEBAR COLUMN: LOGIC NGHIỆP VỤ (CHIẾM 1 CỘT / PHẢI) === */}
        <div className="xl:col-span-1 flex flex-col gap-6">

          {/* Cụm 1: Box AI Configuration Settings - Premium look */}
          <div className="bg-neutral-900/50 backdrop-blur-xl border border-neutral-800 rounded-xl p-6 shadow-2xl relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/5 blur-3xl rounded-full -mr-16 -mt-16 group-hover:bg-blue-500/10 transition-colors"></div>
            <h3 className="text-lg font-semibold text-neutral-100 mb-5 flex items-center gap-3">
              <div className="p-2 bg-blue-500/10 rounded-lg text-blue-400">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 18v-3a5.972 5.972 0 00-.75-2.906A3.005 3.005 0 0119 15v3h-3zM4.75 12.094A5.973 5.973 0 004 15v3H1v-3a3 3 0 013.75-2.906z" />
                </svg>
              </div>
              Cấu hình AI Edge
            </h3>
            <div className="flex flex-col gap-4 relative z-10">
              <div>
                <label className="text-xs font-semibold text-neutral-500 uppercase tracking-wider mb-2 block">Inference Engine</label>
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="w-full bg-neutral-950/80 border border-neutral-800 text-neutral-200 text-sm rounded-xl focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 block p-3 outline-none transition-all appearance-none cursor-pointer hover:bg-neutral-900"
                >
                  {AVAILABLE_MODELS.map(model => (
                    <option key={model.id} value={model.id}>{model.name}</option>
                  ))}
                </select>
              </div>

              <button
                onClick={handleSwitchModel}
                className="mt-2 w-full text-white bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 focus:ring-4 focus:ring-blue-800 font-bold rounded-xl text-sm px-5 py-3.5 transition-all shadow-lg shadow-blue-900/30 active:scale-[0.98] flex items-center justify-center gap-2"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M11.3 1.047a1 1 0 01.897.95L12.35 12.256l1.3-1.3a1 1 0 011.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 111.414-1.414l1.3 1.3L10.3 2.05a1 1 0 01.998-1.003z" clipRule="evenodd" />
                </svg>
                Áp dụng Model mới
              </button>
            </div>
          </div>

          {/* Cụm 2: Event Logs Console - Premium styled */}
          <div className="bg-neutral-900/50 backdrop-blur-xl border border-neutral-800 rounded-xl p-6 shadow-2xl flex-1 flex flex-col min-h-[450px]">
            <div className="flex items-center justify-between mb-5">
              <h3 className="text-lg font-semibold text-neutral-100 flex items-center gap-3">
                <div className="p-2 bg-amber-500/10 rounded-lg text-amber-400">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                Nhật ký Giám sát
              </h3>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-500/20 text-amber-500 uppercase tracking-widest border border-amber-500/30">Live Feed</span>
            </div>

            <div className="bg-neutral-950/40 border border-neutral-800/50 rounded-xl p-4 flex-1 overflow-y-auto max-h-[600px] scrollbar-hide">
              {alerts.length === 0 ? (
                <div className="text-neutral-600 italic h-full flex flex-col items-center justify-center font-mono text-sm gap-4 py-20">
                  <div className="relative">
                    <div className="absolute inset-0 bg-neutral-600 blur-lg opacity-20 animate-pulse"></div>
                    <span className="relative w-8 h-8 rounded-full border-2 border-neutral-700 border-t-blue-500 animate-spin block"></span>
                  </div>
                  Đang ghi nhận biến động...
                </div>
              ) : (
                <ul className="space-y-3">
                  {alerts.map((alert, i) => (
                    <li
                      key={i}
                      className={`text-xs py-3.5 px-4 rounded-xl border border-neutral-800/50 font-mono shadow-sm transition-all hover:scale-[1.02] active:scale-[0.98]
                        ${alert.includes('TĂNG') ? 'bg-gradient-to-r from-emerald-500/5 to-transparent border-l-emerald-500 text-emerald-300' :
                          alert.includes('GIẢM') ? 'bg-gradient-to-r from-rose-500/5 to-transparent border-l-rose-500 text-rose-300' :
                            'bg-gradient-to-r from-blue-500/5 to-transparent border-l-blue-500 text-blue-300'}`}
                      style={{ borderLeftWidth: '4px' }}
                    >
                      {alert}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}

export default Page;
