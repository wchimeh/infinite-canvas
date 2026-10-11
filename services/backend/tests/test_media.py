import json
import pytest

from app.exporter import binary, command, export_timeline, probe
from app.store import Store


def test_real_five_shot_export(tmp_path):
    try:
        ffmpeg = binary("ffmpeg")
        binary("ffprobe")
    except ValueError:
        pytest.skip("未安装 FFmpeg/ffprobe；不能验证真实导出")
    source = tmp_path / "source.mp4"
    voice = tmp_path / "voice.wav"
    command([ffmpeg, "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=navy:s=320x568:r=30:d=3", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(source)])
    command([ffmpeg, "-y", "-v", "error", "-f", "lavfi", "-i", "sine=frequency=440:duration=15", "-ar", "48000", str(voice)])
    store = Store(tmp_path / "workspace")
    project = store.create_project("五镜头导出验收")
    video = store.add_asset(project["id"], source.read_bytes(), "source.mp4")
    audio = store.add_asset(project["id"], voice.read_bytes(), "voice.wav")
    timeline = {"width": 1080, "height": 1920, "fps": 30,
                "clips": [{"assetId": video["id"], "durationMs": 3000, "inMs": 0, "approved": True} for _ in range(5)],
                "audio": [{"assetId": audio["id"], "durationMs": 15000, "startMs": 0, "gain": 0.2}],
                "subtitles": [{"text": "雨夜，故事从这里开始。", "startMs": 0, "endMs": 3000}]}
    result = export_timeline(store, project["id"], timeline, "fixture")
    output = store.project_dir(project["id"]) / result["path"]
    info = probe(output)
    video_stream = next(s for s in info["streams"] if s["codec_type"] == "video")
    audio_stream = next(s for s in info["streams"] if s["codec_type"] == "audio")
    assert (video_stream["width"], video_stream["height"], video_stream["codec_name"]) == (1080, 1920, "h264")
    assert audio_stream["codec_name"] == "aac"
    assert abs(float(info["format"]["duration"]) - 15) <= 1 / 30
    assert output.with_suffix(".srt").exists()
    manifest = json.loads(output.with_suffix(".manifest.json").read_text(encoding="utf-8"))
    assert manifest["sha256"] == result["sha256"]
    command([ffmpeg, "-v", "error", "-i", str(output), "-f", "null", "-"])
