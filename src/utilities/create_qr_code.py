"""
Push-button QR generator with centered logo and white rounded border.
- Size: 800x800
- Logo: 25% of QR width
- Event ID auto-generated from local time (America/Toronto): YYYYMMDD-HHmm
- Permanent signature token via itsdangerous
TODO: Validate the url signatures on the backend later on

"""
from __future__ import annotations

import os
import pendulum
import qrcode

from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlencode
from qrcode.constants import ERROR_CORRECT_H
from itsdangerous import URLSafeSerializer
from PIL import Image, ImageDraw


# --------- CONFIG -----------
@dataclass(frozen=True)
class QRCodeConfig:
    base_url: str
    secret_key: str

    logo_path: Path = field(default_factory=lambda: Path("static/Odyssey_Logo.png"))
    qr_size: int = 800
    logo_scale: float = 0.25
    border_frac: float = 0.03
    corner_radius: int = 18

    sign_salt: str = "attendance-token"
    timezone: str = "America/Toronto"

    def __post_init__(self) -> None:
        if not self.base_url:
            raise RuntimeError(f"{self.__class__.__name__}: base_url must be provided.")
        if not self.secret_key:
            raise RuntimeError(f"{self.__class__.__name__}: secret_key must be provided.")

    @property
    def base_url_norm(self) -> str:
        return self.base_url.rstrip("/")


class QRCodeGenerator:
    """Generate a QR code pointing to a signed URL."""

    def __init__(self, config: QRCodeConfig) -> None:
        self._cfg = config
        self._serializer = URLSafeSerializer(self._cfg.secret_key, salt=self._cfg.sign_salt)

    @staticmethod
    def _round_corners(img: Image.Image, radius: int) -> Image.Image:
        if img.mode != "RGBA":
            img = img.convert("RGBA")

        width, height = img.size
        mask = Image.new("L", (width, height), 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle([0, 0, width, height], radius=radius, fill=255)
        img.putalpha(mask)
        return img

    @staticmethod
    def _rounded_rect(
        size: tuple[int, int],
        radius: int,
        color: tuple[int, int, int, int] = (255, 255, 255, 255),
    ) -> Image.Image:
        width, height = size
        rect = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        mask = Image.new("L", (width, height), 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle([0, 0, width, height], radius=radius, fill=255)
        overlay = Image.new("RGBA", (width, height), color)
        rect.paste(overlay, (0, 0), mask)
        return rect

    def _new_event_id(self) -> str:
        now_local = pendulum.now(self._cfg.timezone)
        return now_local.format("YYYYMMDD-HHmm")

    def _build_signed_url(self, event_id: str) -> tuple[str, dict]:
        payload = {
            "event_id": event_id,
            "issued_at_utc": pendulum.now("UTC").to_iso8601_string(),  # optional; handy for logs
        }
        sig = self._serializer.dumps(payload)

        query = urlencode({"event": event_id, "sig": sig})
        url = f"{self._cfg.base_url_norm}/?{query}"
        return url, payload

    def generate_qr_code_with_image(self) -> str:
        event_id = self._new_event_id()
        url, payload = self._build_signed_url(event_id)

        qr = qrcode.QRCode(
            version=None,
            error_correction=ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)

        qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")
        qr_img = qr_img.resize((self._cfg.qr_size, self._cfg.qr_size), Image.Resampling.LANCZOS)

        if self._cfg.logo_path.exists():
            logo = Image.open(self._cfg.logo_path).convert("RGBA")

            max_w = int(self._cfg.qr_size * self._cfg.logo_scale)
            max_h = int(self._cfg.qr_size * self._cfg.logo_scale)
            logo.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)

            border_px = max(2, int(logo.width * self._cfg.border_frac))
            bordered_size = (logo.width + 2 * border_px, logo.height + 2 * border_px)

            border_bg = self._rounded_rect(
                bordered_size,
                radius=self._cfg.corner_radius,
                color=(255, 255, 255, 255),
            )
            logo = self._round_corners(logo, self._cfg.corner_radius)

            bx = (qr_img.width - border_bg.width) // 2
            by = (qr_img.height - border_bg.height) // 2
            qr_img.alpha_composite(border_bg, (bx, by))

            lx = bx + border_px
            ly = by + border_px
            qr_img.alpha_composite(logo, (lx, ly))

        out_png = f"QR_{event_id}.png"
        qr_img.save(out_png)

        print("Event: ", event_id)
        print("URL:   ", url)
        print("Meta:  ", payload)
        print("Saved: ", out_png)
        return out_png


if __name__ == "__main__":
    BASE_URL: str = os.getenv("CLOUDFLARE_PAGES_QRCODE_REDIRECT", "")
    SECRET: str = os.getenv("CLOUDFLARE_PAGES_QRCODE_SECRET", "")

    QRCodeGenerator(QRCodeConfig(base_url=BASE_URL, secret_key=SECRET)).generate_qr_code_with_image()
