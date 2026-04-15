/**
 * URL backend / mediamtx nhìn từ trình duyệt (không phải từ container Next).
 * Trong Docker: map cổng host (8000, 8889) — trình duyệt gọi host đang mở dashboard.
 * NEXT_PUBLIC_EDGE_HOST: optional, ép host (vd. 127.0.0.1 khi Windows lỗi phân giải localhost).
 */
export function getEdgePublicHost() {
  const envHost = process.env.NEXT_PUBLIC_EDGE_HOST;
  if (envHost && String(envHost).trim()) {
    return String(envHost).trim();
  }
  if (typeof window !== 'undefined' && window.location?.hostname) {
    return window.location.hostname;
  }
  return 'localhost';
}

function getBrowserProtocol() {
  if (typeof window !== 'undefined' && window.location?.protocol) {
    return window.location.protocol;
  }
  return 'http:';
}

export function edgeApiOrigin() {
  const host = getEdgePublicHost();
  const port = process.env.NEXT_PUBLIC_API_PORT || '8000';
  const protocol = getBrowserProtocol() === 'https:' ? 'https' : 'http';
  return `${protocol}://${host}:${port}`;
}

export function edgeWsMetadataUrl() {
  const host = getEdgePublicHost();
  const port = process.env.NEXT_PUBLIC_API_PORT || '8000';
  const protocol = getBrowserProtocol() === 'https:' ? 'wss' : 'ws';
  return `${protocol}://${host}:${port}/ws/metadata`;
}

export function edgeWhepUrl(pathSuffix = '/cam1/whep') {
  const host = getEdgePublicHost();
  const port = process.env.NEXT_PUBLIC_MEDIAMTX_HTTP_PORT || '8889';
  const protocol = getBrowserProtocol() === 'https:' ? 'https' : 'http';
  return `${protocol}://${host}:${port}${pathSuffix}`;
}
