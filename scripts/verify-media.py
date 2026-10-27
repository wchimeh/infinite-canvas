"""完整验收必须实际执行媒体测试；显式错误目录不可被 PATH 掩盖。"""
import os
from pathlib import Path
import shutil
import subprocess


def main():
    directory = os.environ.get('FFMPEG_DIR')
    for name in ('ffmpeg', 'ffprobe'):
        candidate = str(Path(directory) / (name + ('.exe' if os.name == 'nt' else ''))) if directory else shutil.which(name)
        if not candidate or not Path(candidate).is_file():
            raise SystemExit(f'完整验收缺少 {name}，请设置正确的 FFMPEG_DIR；不允许跳过真实媒体测试。')
        try:
            subprocess.run([candidate, '-version'], check=True, capture_output=True, timeout=15,
                           creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        except (OSError, subprocess.SubprocessError):
            raise SystemExit(f'完整验收无法执行 {name}，请检查 FFMPEG_DIR。') from None
    print('媒体工具预检通过：ffmpeg 和 ffprobe 均可执行')


if __name__ == '__main__':
    main()
