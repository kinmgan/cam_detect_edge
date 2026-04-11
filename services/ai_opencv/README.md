# AI OpenCV Preprocess Service

## Purpose
This folder contains the `ai_opencv` service for the smart camera edge system.

Its job is to:
- read a video source
- normalize frames into an internal contract
- compute light preprocessing and quality metrics
- store frames in a short-lived local frame store
- publish preprocess events to Redis Streams for downstream services

This service does **not** do:
- model inference
- tracking
- frontend playback
- drawing bounding boxes on video

## Current Flow
The current flow is:

`video source -> decoder -> FramePacket -> preprocessor -> frame store -> preprocess event -> Redis Streams`

Downstream services are expected to do the rest:
- model service reads `camera:preprocess_stream`
- tracker service reads `camera:detections_stream`
- metadata bridge or tracker writes legacy `camera:metadata:<camera_id>` for the current backend

## Main Entry Point
- `main_worker.py`

This is the runtime entrypoint for the preprocess service.

It loads settings, creates the runtime backend, and starts the preprocess pipeline.

## Important Folders

### `config/`
- `settings.py`: loads environment variables and normalizes runtime configuration.

### `domain/`
- `frame_packet.py`: canonical frame object used inside the service.
- `preprocess_result.py`: output of the preprocessing stage.
- `frame_store_record.py`: result of writing a frame into the frame store.

### `contracts/`
- `decoder.py`: decoder interface.
- `preprocessor.py`: preprocessor interface.
- `publisher.py`: publisher interface.
- `framestore.py`: frame store interface.

These files define the contracts so we can change implementations later without rewriting the pipeline.

### `adapters/`
- `decoder/opencv_decoder.py`: CPU decoder path using OpenCV.
- `decoder/pynv_decoder.py`: GPU decoder scaffold with runtime guard for NVIDIA dependencies.
- `frame_store/npy_frame_store.py`: v1 frame store using `.npy` files.
- `publisher/redis_stream_publisher.py`: publishes preprocess and health events to Redis Streams.

### `ingestion/`
- `stream_reader.py`: reads the video source, reconnects, keeps the latest frame, emits `FramePacket`.
- `preprocessor.py`: computes motion, blur, brightness, and contrast.

### `preprocess/`
- `frame_preprocessor.py`: CPU preprocessor wrapper.
- `gpu_frame_preprocessor.py`: GPU preprocessor scaffold with CPU fallback metrics.

### `events/`
- `preprocess_event.py`: builds and serializes preprocess and health event payloads.

### `metrics/`
- `health_monitor.py`: tracks simple service health metrics such as effective FPS and publish latency.

### `factories/`
- `runtime.py`: chooses the correct runtime objects based on config (`cpu` or `gpu`).

### `orchestration/`
- `pipeline.py`: glues decoder, preprocessor, frame store, event builder, publisher, and health monitor together.

### `stubs/`
- `model_consumer_stub.py`: fake downstream model consumer for observing frame handoff.
- `tracker_consumer_stub.py`: fake tracker-side consumer.
- `metadata_bridge_stub.py`: writes legacy metadata keys for the current backend/frontend path.

These stubs exist to validate data flow and contracts. They are not real model or tracker implementations.

### Legacy / Reference Files
- `ai_engine/wrapper.py`
- `command_listener.py`
- `output_handler/redis_publisher.py`
- `core/queues_manager.py`

These are older files kept for reference or compatibility. They are not the main path of the new preprocess architecture.

## Frame Storage
Frames are currently stored as short-lived `.npy` files in the local frame store.

Why:
- easy to debug
- easy to load from downstream consumers
- keeps raw frame data out of Redis Streams

This is a v1 design. It is acceptable for testing and contract validation, but it is not the final high-performance production design.

## Runtime Modes

### CPU Mode
Used for development and current testing.

Current stack:
- OpenCV decoder
- OpenCV / NumPy preprocessing
- local `.npy` frame store
- Redis Streams publisher

### GPU Mode
Prepared for Linux Docker production, but not fully runnable on this machine.

Current status:
- runtime guard exists
- NVIDIA dependency checks exist
- Docker scaffold exists
- final GPU frame export path is still intentionally blocked until tested on a real GPU host

## Configuration
Main config lives in:
- `.env`
- `.env.example`

Important variables:
- `PIPELINE_BACKEND`
- `INPUT_SOURCE`
- `CAMERA_ID`
- `TARGET_FPS`
- `FRAME_STORE_DIR`
- `FRAME_TTL_SEC`
- `REDIS_HOST`
- `REDIS_PORT`
- `PREPROCESS_STREAM`
- `HEALTH_STREAM`

## How To Run
From this folder:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main_worker.py
```

If Redis is available, you can observe the downstream handoff with:

```powershell
python stubs\model_consumer_stub.py
```

## Current Limitations
- one `main_worker` process currently handles one source
- real model inference is not implemented here
- real tracking is not implemented here
- frontend playback is not handled here
- GPU path is scaffolded, not production-verified on this machine

## Recommended Next Steps
- replace the `.npy` frame store with a higher-performance shared memory design
- add a real model consumer service
- add a real tracker service
- decide whether to keep backend compatibility through a metadata bridge or upgrade backend to consume streams directly
