# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import shutil
from pathlib import Path
from anony import logger


def ensure_dirs():
    """
    Ensure necessary directories exist.
    Only ffmpeg required — yt-dlp and deno removed.
    """
    if not shutil.which("ffmpeg"):
        raise RuntimeError("FFmpeg must be installed and accessible in PATH.")

    Path("cache").mkdir(parents=True, exist_ok=True)
    logger.info("Cache directory ready.")
