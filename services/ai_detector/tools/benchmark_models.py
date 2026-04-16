import argparse
import csv
import statistics
import time
from pathlib import Path

import cv2
from ultralytics import YOLO


DEFAULT_WEIGHTS_DIR = Path(__file__).resolve().parents[1] / "models" / "person_detector" / "weights"


def parse_model_arg(value):
    if "=" not in value:
        raise argparse.ArgumentTypeError("Use NAME=PATH, for example yolo11s=models/.../yolo11s.pt")
    name, path = value.split("=", 1)
    name = name.strip()
    path = Path(path.strip())
    if not name:
        raise argparse.ArgumentTypeError("Model name cannot be empty")
    if not path.exists():
        raise argparse.ArgumentTypeError(f"Model path does not exist: {path}")
    return name, path


def discover_default_models():
    candidates = [
        ("yolo11n", DEFAULT_WEIGHTS_DIR / "yolo11n.pt"),
        ("yolo11s", DEFAULT_WEIGHTS_DIR / "yolo11s.pt"),
        ("yolo11m", DEFAULT_WEIGHTS_DIR / "yolo11m.pt"),
    ]
    return [(name, path) for name, path in candidates if path.exists()]


def draw_detections(frame, detections, model_name):
    output = frame.copy()
    for det in detections:
        x1, y1, x2, y2 = [int(v) for v in det["bbox"]]
        conf = det["confidence"]
        cv2.rectangle(output, (x1, y1), (x2, y2), (0, 220, 0), 2)
        cv2.putText(
            output,
            f"person {conf:.2f}",
            (x1, max(20, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 220, 0),
            2,
            cv2.LINE_AA,
        )

    cv2.putText(
        output,
        model_name,
        (16, 32),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (0, 220, 255),
        2,
        cv2.LINE_AA,
    )
    return output


def run_model(model_name, weights_path, video_path, output_dir, imgsz, conf, iou, device, max_frames):
    model = YOLO(str(weights_path))
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    source_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0

    overlay_path = output_dir / f"{model_name}_overlay.mp4"
    writer = cv2.VideoWriter(
        str(overlay_path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        source_fps,
        (width, height),
    )

    frame_rows = []
    latencies_ms = []
    detection_counts = []
    confidences = []
    frame_index = 0

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if max_frames is not None and frame_index >= max_frames:
                break

            started = time.perf_counter()
            results = model.predict(
                frame,
                classes=[0],
                imgsz=imgsz,
                conf=conf,
                iou=iou,
                device=device,
                verbose=False,
            )
            elapsed_ms = (time.perf_counter() - started) * 1000.0

            detections = []
            if results and results[0].boxes is not None:
                for box in results[0].boxes:
                    confidence = float(box.conf[0])
                    xyxy = box.xyxy[0].tolist()
                    detections.append({"bbox": xyxy, "confidence": confidence})
                    confidences.append(confidence)

            latencies_ms.append(elapsed_ms)
            detection_counts.append(len(detections))
            frame_rows.append(
                {
                    "model": model_name,
                    "frame_index": frame_index,
                    "latency_ms": round(elapsed_ms, 3),
                    "detections": len(detections),
                    "avg_confidence": round(statistics.mean([d["confidence"] for d in detections]), 4)
                    if detections
                    else "",
                }
            )

            writer.write(draw_detections(frame, detections, model_name))
            frame_index += 1
    finally:
        cap.release()
        writer.release()

    avg_latency = statistics.mean(latencies_ms) if latencies_ms else 0.0
    return {
        "summary": {
            "model": model_name,
            "weights": str(weights_path),
            "frames": len(latencies_ms),
            "avg_latency_ms": round(avg_latency, 3),
            "fps": round(1000.0 / avg_latency, 3) if avg_latency > 0 else 0.0,
            "avg_detections_per_frame": round(statistics.mean(detection_counts), 3) if detection_counts else 0.0,
            "avg_confidence": round(statistics.mean(confidences), 4) if confidences else 0.0,
            "overlay_video": str(overlay_path),
        },
        "frames": frame_rows,
    }


def write_csv(path, rows, fieldnames):
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark person detector models without ground truth: speed, detection count, and overlay video."
    )
    parser.add_argument("--video", required=True, type=Path, help="Input test video path")
    parser.add_argument("--output-dir", type=Path, default=Path("benchmark_outputs"))
    parser.add_argument(
        "--model",
        action="append",
        type=parse_model_arg,
        help="Model to benchmark as NAME=PATH. Can be used multiple times.",
    )
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--conf", type=float, default=0.25)
    parser.add_argument("--iou", type=float, default=0.5)
    parser.add_argument("--device", default=None, help="Ultralytics device, for example cpu, 0, or cuda:0")
    parser.add_argument("--max-frames", type=int, default=None, help="Optional frame limit for quick tests")
    args = parser.parse_args()

    if not args.video.exists():
        raise FileNotFoundError(f"Video does not exist: {args.video}")

    models = args.model if args.model else discover_default_models()
    if not models:
        raise RuntimeError(
            f"No local model weights found in {DEFAULT_WEIGHTS_DIR}. "
            "Add yolo11n.pt/yolo11s.pt/yolo11m.pt or pass --model NAME=PATH."
        )

    args.output_dir.mkdir(parents=True, exist_ok=True)

    summary_rows = []
    frame_rows = []
    for model_name, weights_path in models:
        print(f"Benchmarking {model_name}: {weights_path}")
        result = run_model(
            model_name=model_name,
            weights_path=weights_path,
            video_path=args.video,
            output_dir=args.output_dir,
            imgsz=args.imgsz,
            conf=args.conf,
            iou=args.iou,
            device=args.device,
            max_frames=args.max_frames,
        )
        summary_rows.append(result["summary"])
        frame_rows.extend(result["frames"])

    summary_path = args.output_dir / "summary.csv"
    frames_path = args.output_dir / "per_frame.csv"
    write_csv(
        summary_path,
        summary_rows,
        [
            "model",
            "weights",
            "frames",
            "avg_latency_ms",
            "fps",
            "avg_detections_per_frame",
            "avg_confidence",
            "overlay_video",
        ],
    )
    write_csv(frames_path, frame_rows, ["model", "frame_index", "latency_ms", "detections", "avg_confidence"])

    print(f"Summary: {summary_path}")
    print(f"Per-frame details: {frames_path}")
    for row in summary_rows:
        print(
            f"{row['model']}: {row['fps']} FPS | {row['avg_latency_ms']} ms | "
            f"{row['avg_detections_per_frame']} detections/frame | overlay={row['overlay_video']}"
        )


if __name__ == "__main__":
    main()
