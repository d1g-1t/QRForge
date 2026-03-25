# QRForge

Generate beautiful QR codes with embedded logos. Track every scan. Analyze geo, device, time-of-day. Production-ready.

## Features

- **QR Code Generation** — PNG/SVG/WebP/PDF output via segno + Pillow
- **Custom Logo Embedding** — Error correction H + ≤30% coverage guarantee
- **1D Barcode Support** — EAN13, Code128, UPC, ISBN13, Code39, GS1-128
- **Dynamic QR Codes** — Change target URL without reprinting
- **Scan Tracking** — Zero-latency 302 redirect with async fire-and-forget analytics
- **Tracking Pixel** — 1x1 transparent GIF for email open tracking
- **Time-Series Analytics** — Hourly/daily/weekly/monthly scan aggregation
- **Geo Distribution** — Country + city breakdown per code
- **Device Analytics** — Mobile/tablet/desktop + OS + browser breakdown
- **GDPR-Friendly** — IP anonymization with daily-rotating salt
- **Generation Cache** — Redis-backed, SHA-256 keyed, configurable TTL

## Tech Stack

| Package | Purpose |
|---------|---------|
| FastAPI 0.115+ | REST API |
| segno 1.6+ | QR code generation (primary) |
| Pillow 11.x | Image processing, logo embedding |
| python-barcode 0.15+ | 1D barcode generation |
| cairosvg 2.7+ | SVG → PDF/PNG conversion |
| SQLAlchemy 2.0+ async | Code registry, scan event log |
| Redis + hiredis | Cache, counters, rate limiting |
| arq | Async scan event processing |

## Quick Start

```bash
git clone https://github.com/d1g-1t/QRForge.git
cd QRForge

cp .env.example .env

docker compose up -d

alembic upgrade head

uvicorn qrcode_service.main:app --reload
```

## API Endpoints

### Generation (stateless)
- `POST /api/v1/generate/qr` — Generate QR code (PNG/SVG/WebP/PDF)
- `POST /api/v1/generate/qr/preview` — 150x150 preview thumbnail
- `POST /api/v1/generate/barcode` — Generate 1D barcode

### Code Management
- `POST /api/v1/codes` — Create tracked code
- `GET /api/v1/codes` — List codes (paginated)
- `GET /api/v1/codes/{id}` — Get code details
- `PATCH /api/v1/codes/{id}` — Update target URL / status
- `DELETE /api/v1/codes/{id}` — Archive code
- `GET /api/v1/codes/{id}/image` — Regenerate image

### Scan Tracking
- `GET /s/{short_code}` — Scan redirect (302)
- `GET /s/{short_code}/pixel.gif` — Tracking pixel

### Analytics
- `GET /api/v1/codes/{id}/stats` — Time-series + geo + device
- `GET /api/v1/codes/{id}/stats/geo` — Geo distribution
- `GET /api/v1/codes/{id}/stats/devices` — Device breakdown
- `GET /api/v1/codes/{id}/stats/heatmap` — 24×7 heatmap

## Testing

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT
