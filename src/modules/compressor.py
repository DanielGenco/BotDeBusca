"""
Módulo de compressão de imagens e vídeos.
Usa Pillow para imagens e FFmpeg (via imageio-ffmpeg) para vídeos.
"""

import io
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


def estimate_image_size(input_path, quality=75, output_format=None):
    """
    Estima o tamanho comprimido de uma imagem fazendo compressão em memória.
    Rápido e preciso.
    """
    try:
        img = Image.open(input_path)
        original_size = os.path.getsize(input_path)

        if output_format == "JPEG" or (output_format is None and input_path.lower().endswith((".jpg", ".jpeg"))):
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

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

        buffer = io.BytesIO()
        img.save(buffer, format=fmt, **save_kwargs)
        estimated_size = buffer.tell()

        return {"original_size": original_size, "estimated_size": estimated_size}
    except Exception:
        original_size = os.path.getsize(input_path) if os.path.exists(input_path) else 0
        return {"original_size": original_size, "estimated_size": original_size}


def estimate_video_size(input_path, quality_preset="medium", max_resolution=None):
    """
    Estima o tamanho comprimido de um vídeo baseado no CRF e resolução.
    Estimativa aproximada.
    """
    original_size = os.path.getsize(input_path) if os.path.exists(input_path) else 0
    # Reduction factors baseados em testes empíricos com CRF
    reduction_map = {
        "low":    0.85,   # CRF 18 — ~15% reduction
        "medium": 0.50,   # CRF 26 — ~50% reduction
        "high":   0.30,   # CRF 32 — ~70% reduction
    }
    factor = reduction_map.get(quality_preset, 0.50)

    # Fator adicional de redução por resolução
    if max_resolution:
        # Reduzir resolução reduz o tamanho proporcionalmente à área de pixels
        # Assumindo vídeo original ~1080p como referência
        res_factor_map = {
            1080: 1.0,    # Sem redução adicional
            720:  0.45,   # 720/1080 ≈ 0.67, ao quadrado ≈ 0.44
            480:  0.20,   # 480/1080 ≈ 0.44, ao quadrado ≈ 0.20
        }
        res_factor = res_factor_map.get(max_resolution, 1.0)
        factor = factor * res_factor

    estimated_size = int(original_size * factor)
    return {"original_size": original_size, "estimated_size": estimated_size}


def estimate_batch_size(files, image_quality=75, video_preset="medium"):
    """
    Estima o tamanho total comprimido de uma lista de arquivos.
    Faz estimativa real para imagens, aproximada para vídeos.
    """
    total_original = 0
    total_estimated = 0

    for finfo in files:
        if finfo["type"] == "image":
            est = estimate_image_size(finfo["path"], quality=image_quality)
        else:
            est = estimate_video_size(finfo["path"], quality_preset=video_preset)
        total_original += est["original_size"]
        total_estimated += est["estimated_size"]

    return {"original_size": total_original, "estimated_size": total_estimated}


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
                    "-preset", preset_config["preset"],
                    "-pix_fmt", "yuv420p",
                    "-profile:v", "high", "-level", "4.0"]

            # Limitar resolução
            if max_resolution:
                cmd += ["-vf", f"scale=-2:{max_resolution}"]

            # Codec de áudio
            cmd += ["-c:a", "aac", "-b:a", "128k"]

            # Otimização para reprodução: moov atom no início do arquivo
            cmd += ["-movflags", "+faststart"]

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


def scan_folder(folder_path):
    """
    Escaneia uma pasta recursivamente e retorna lista de arquivos suportados.

    Returns:
        list of dict: [{"path": str, "type": "image"|"video", "size": int, "relative": str}]
    """
    files = []
    for root, _dirs, filenames in os.walk(folder_path):
        for fname in filenames:
            full_path = os.path.join(root, fname)
            ftype = get_file_type(full_path)
            if ftype:
                rel_path = os.path.relpath(full_path, folder_path)
                files.append({
                    "path": full_path,
                    "type": ftype,
                    "size": os.path.getsize(full_path),
                    "relative": rel_path,
                })
    return files


def compress_batch(folder_path, output_folder, image_quality=75,
                   video_preset="medium", video_max_resolution=None,
                   on_file_start=None, on_file_progress=None,
                   on_file_complete=None, on_batch_complete=None,
                   cancel_event=None):
    """
    Comprime todos os arquivos de imagem/vídeo de uma pasta em thread separada.
    Mantém a estrutura de subpastas no destino.

    Args:
        folder_path: Pasta de origem
        output_folder: Pasta de destino
        image_quality: Qualidade para imagens (1-100)
        video_preset: 'low', 'medium' ou 'high'
        video_max_resolution: Resolução máxima para vídeos (None = original)
        on_file_start: Callback(index, total, filename, filetype)
        on_file_progress: Callback(percent) — progresso do arquivo atual (vídeos)
        on_file_complete: Callback(index, total, result)
        on_batch_complete: Callback(summary) — relatório final
        cancel_event: threading.Event — cancela o lote

    Returns:
        Thread que está processando
    """
    files = scan_folder(folder_path)

    if not files:
        if on_batch_complete:
            on_batch_complete({
                "success": True,
                "total_files": 0,
                "message": "No supported files found in this folder.",
            })
        return None

    def _run():
        total = len(files)
        total_original = 0
        total_compressed = 0
        completed = 0
        failed = 0

        for i, finfo in enumerate(files):
            if cancel_event and cancel_event.is_set():
                if on_batch_complete:
                    on_batch_complete({
                        "success": False, "error": "cancelled",
                        "total_files": total, "completed": completed, "failed": failed,
                        "total_original": total_original,
                        "total_compressed": total_compressed,
                    })
                return

            # Criar subpasta no destino mantendo a estrutura
            rel_dir = os.path.dirname(finfo["relative"])
            dest_dir = os.path.join(output_folder, rel_dir) if rel_dir else output_folder
            os.makedirs(dest_dir, exist_ok=True)

            out_path = os.path.join(dest_dir, os.path.basename(finfo["path"]))

            if on_file_start:
                on_file_start(i, total, os.path.basename(finfo["path"]), finfo["type"])

            if finfo["type"] == "image":
                result = compress_image(finfo["path"], out_path, quality=image_quality)
                if result.get("success"):
                    total_original += result["original_size"]
                    total_compressed += result["compressed_size"]
                    completed += 1
                else:
                    failed += 1
                if on_file_complete:
                    on_file_complete(i, total, result)

            elif finfo["type"] == "video":
                # Compressão síncrona (já estamos em thread)
                video_done = threading.Event()
                video_result = [None]

                def _on_vid_progress(pct):
                    if on_file_progress:
                        on_file_progress(pct)

                def _on_vid_complete(res):
                    video_result[0] = res
                    video_done.set()

                compress_video(
                    finfo["path"], out_path,
                    quality_preset=video_preset,
                    max_resolution=video_max_resolution,
                    on_progress=_on_vid_progress,
                    on_complete=_on_vid_complete,
                    cancel_event=cancel_event,
                )
                video_done.wait()

                result = video_result[0]
                if result and result.get("success"):
                    total_original += result["original_size"]
                    total_compressed += result["compressed_size"]
                    completed += 1
                elif result and result.get("error") == "cancelled":
                    if on_batch_complete:
                        on_batch_complete({
                            "success": False, "error": "cancelled",
                            "total_files": total, "completed": completed, "failed": failed,
                            "total_original": total_original,
                            "total_compressed": total_compressed,
                        })
                    return
                else:
                    failed += 1

                if on_file_complete:
                    on_file_complete(i, total, result)

        # Relatório final
        reduction = 0
        if total_original > 0:
            reduction = ((total_original - total_compressed) / total_original) * 100

        if on_batch_complete:
            on_batch_complete({
                "success": True,
                "total_files": total,
                "completed": completed,
                "failed": failed,
                "total_original": total_original,
                "total_compressed": total_compressed,
                "reduction_percent": max(0, reduction),
            })

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
