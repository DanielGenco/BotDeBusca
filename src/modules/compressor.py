"""
Módulo de compressão de imagens e vídeos.
Usa Pillow para imagens e FFmpeg (via imageio-ffmpeg) para vídeos.
"""

import os
import subprocess
import threading
import logging
from PIL import Image

try:
    import imageio_ffmpeg
    FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
except ImportError:
    FFMPEG_EXE = None
    logging.warning("imageio-ffmpeg não encontrado — compressão de vídeo indisponível")


# ── Formatos suportados ───────────────────────────────────────────
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".wmv", ".flv"}

QUALITY_PRESETS = {
    "low":    {"crf": 18, "preset": "slow",   "label": "Low compression (best quality)"},
    "medium": {"crf": 26, "preset": "medium", "label": "Medium compression"},
    "high":   {"crf": 32, "preset": "fast",   "label": "High compression (smallest file)"},
}


def get_file_type(filepath):
    """Retorna 'image', 'video' ou None baseado na extensão."""
    ext = os.path.splitext(filepath)[1].lower()
    if ext in IMAGE_EXTENSIONS:
        return "image"
    if ext in VIDEO_EXTENSIONS:
        return "video"
    return None


def get_file_size_str(size_bytes):
    """Formata bytes em string legível (KB, MB, GB)."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def compress_image(input_path, output_path, quality=75, max_width=None, max_height=None,
                   output_format=None):
    """
    Comprime uma imagem usando Pillow.

    Args:
        input_path: Caminho do arquivo original
        output_path: Caminho para salvar o arquivo comprimido
        quality: Qualidade de 1-100 (só para JPEG/WebP)
        max_width: Largura máxima (mantém proporção)
        max_height: Altura máxima (mantém proporção)
        output_format: Formato de saída ('JPEG', 'PNG', 'WEBP') — None mantém o original

    Returns:
        dict com informações do resultado
    """
    try:
        img = Image.open(input_path)
        original_size = os.path.getsize(input_path)
        original_dimensions = img.size

        # Converter RGBA para RGB se salvando como JPEG
        if output_format == "JPEG" or (output_format is None and input_path.lower().endswith((".jpg", ".jpeg"))):
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

        # Redimensionar se necessário
        if max_width or max_height:
            w, h = img.size
            ratio = 1.0
            if max_width and w > max_width:
                ratio = min(ratio, max_width / w)
            if max_height and h > max_height:
                ratio = min(ratio, max_height / h)
            if ratio < 1.0:
                new_w = int(w * ratio)
                new_h = int(h * ratio)
                img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # Determinar formato de saída
        save_kwargs = {}
        if output_format:
            fmt = output_format.upper()
        else:
            ext = os.path.splitext(input_path)[1].lower()
            fmt_map = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".webp": "WEBP",
                       ".bmp": "BMP", ".tiff": "TIFF", ".tif": "TIFF"}
            fmt = fmt_map.get(ext, "JPEG")

        if fmt in ("JPEG", "WEBP"):
            save_kwargs["quality"] = quality
            save_kwargs["optimize"] = True
        elif fmt == "PNG":
            save_kwargs["optimize"] = True

        img.save(output_path, format=fmt, **save_kwargs)

        compressed_size = os.path.getsize(output_path)
        reduction = ((original_size - compressed_size) / original_size) * 100 if original_size > 0 else 0

        return {
            "success": True,
            "original_size": original_size,
            "compressed_size": compressed_size,
            "reduction_percent": max(0, reduction),
            "original_dimensions": original_dimensions,
            "new_dimensions": img.size,
        }
    except Exception as e:
        logging.error(f"Erro ao comprimir imagem: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


def compress_video(input_path, output_path, quality_preset="medium",
                   max_resolution=None, on_progress=None, on_complete=None,
                   cancel_event=None):
    """
    Comprime um vídeo usando FFmpeg em thread separada.

    Args:
        input_path: Caminho do arquivo original
        output_path: Caminho para salvar o arquivo comprimido
        quality_preset: 'low', 'medium' ou 'high'
        max_resolution: Resolução máxima (ex: 1080, 720, 480) — None mantém original
        on_progress: Callback(percent: float) chamado durante o progresso
        on_complete: Callback(result: dict) chamado quando termina
        cancel_event: threading.Event — quando set(), cancela a compressão

    Returns:
        Thread que está processando o vídeo
    """
    if not FFMPEG_EXE:
        result = {"success": False, "error": "FFmpeg not available"}
        if on_complete:
            on_complete(result)
        return None

    preset_config = QUALITY_PRESETS.get(quality_preset, QUALITY_PRESETS["medium"])

    def _run():
        process = None
        try:
            original_size = os.path.getsize(input_path)

            # Obter duração do vídeo
            duration = _get_video_duration(input_path)

            # Montar comando FFmpeg
            cmd = [FFMPEG_EXE, "-i", input_path, "-y"]

            # Codec de vídeo
            cmd += ["-c:v", "libx264", "-crf", str(preset_config["crf"]),
                    "-preset", preset_config["preset"]]

            # Limitar resolução
            if max_resolution:
                cmd += ["-vf", f"scale=-2:'{max_resolution}'"]

            # Codec de áudio
            cmd += ["-c:a", "aac", "-b:a", "128k"]

            # Progresso
            cmd += ["-progress", "pipe:1", "-nostats"]

            cmd.append(output_path)

            logging.info(f"FFmpeg cmd: {' '.join(cmd)}")

            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                universal_newlines=True, creationflags=subprocess.CREATE_NO_WINDOW
            )

            # Ler progresso
            for line in process.stdout:
                # Verificar cancelamento
                if cancel_event and cancel_event.is_set():
                    process.terminate()
                    process.wait(timeout=5)
                    # Remover arquivo parcial
                    if os.path.exists(output_path):
                        os.remove(output_path)
                    logging.info("Compressão de vídeo cancelada pelo usuário")
                    result = {"success": False, "error": "cancelled"}
                    if on_complete:
                        on_complete(result)
                    return

                line = line.strip()
                if on_progress and line.startswith("out_time_us="):
                    try:
                        val = line.split("=")[1]
                        if val == "N/A":
                            continue
                        current_us = int(val)
                        current_s = current_us / 1_000_000
                        if duration and duration > 0:
                            percent = min(99.0, (current_s / duration) * 100)
                        else:
                            # Sem duração: estimar pelo tamanho do output
                            if os.path.exists(output_path):
                                out_size = os.path.getsize(output_path)
                                percent = min(95.0, (out_size / original_size) * 100)
                            else:
                                percent = 0
                        on_progress(percent)
                    except (ValueError, ZeroDivisionError, OSError):
                        pass

            process.wait()

            if cancel_event and cancel_event.is_set():
                if os.path.exists(output_path):
                    os.remove(output_path)
                result = {"success": False, "error": "cancelled"}
            elif process.returncode != 0:
                logging.error(f"FFmpeg failed with code {process.returncode}")
                result = {"success": False, "error": f"FFmpeg failed (code {process.returncode})"}
            else:
                compressed_size = os.path.getsize(output_path)
                reduction = ((original_size - compressed_size) / original_size) * 100 if original_size > 0 else 0

                if on_progress:
                    on_progress(100.0)

                result = {
                    "success": True,
                    "original_size": original_size,
                    "compressed_size": compressed_size,
                    "reduction_percent": max(0, reduction),
                }

        except Exception as e:
            logging.error(f"Erro ao comprimir vídeo: {e}", exc_info=True)
            if process and process.poll() is None:
                process.terminate()
            result = {"success": False, "error": str(e)}

        if on_complete:
            on_complete(result)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return thread


def _get_video_duration(filepath):
    """Obtém duração do vídeo em segundos usando FFmpeg."""
    try:
        cmd = [FFMPEG_EXE, "-i", filepath, "-hide_banner"]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=10,
            encoding="utf-8", errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        # FFmpeg imprime informação no stderr (retorna erro pois não tem output file)
        for line in result.stderr.split("\n"):
            if "Duration:" in line:
                # Format: Duration: 00:05:32.10, ...
                time_str = line.split("Duration:")[1].split(",")[0].strip()
                if time_str == "N/A":
                    continue
                parts = time_str.split(":")
                hours = float(parts[0])
                minutes = float(parts[1])
                seconds = float(parts[2])
                duration = hours * 3600 + minutes * 60 + seconds
                logging.info(f"Duração do vídeo detectada: {duration:.1f}s")
                return duration
    except Exception as e:
        logging.warning(f"Não foi possível obter duração do vídeo: {e}")
    return None
