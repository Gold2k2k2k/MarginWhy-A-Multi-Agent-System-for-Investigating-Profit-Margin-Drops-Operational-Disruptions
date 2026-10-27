"""
Merges recorded WebM video with Edge-TTS audio segments into high quality 1080p MP4 demo video.
"""

from pathlib import Path
import shutil
import subprocess
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
RECORDINGS_DIR = BASE_DIR / "recordings"
AUDIO_DIR = RECORDINGS_DIR / "audio"
RAW_DIR = RECORDINGS_DIR / "raw"
FFMPEG_PATH = r"C:\ffmpeg\bin\ffmpeg.exe"
OUTPUT_MP4 = BASE_DIR / "MarginWhy_Official_Demo_Video_1080p.mp4"
ARTIFACT_DIR = Path(r"C:\Users\DELL\.gemini\antigravity-ide\brain\ee57dc4c-5247-4f2b-908a-dab46e9949ae")

SEGMENTS = ["seg1_hook", "seg2_execution", "seg3_sponsor_tech", "seg4_executive_ux", "seg5_verification"]


def get_duration(file_path: Path) -> float:
    cmd = [FFMPEG_PATH, "-i", str(file_path), "-f", "null", "-"]
    res = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
    for line in res.stderr.splitlines():
        if "Duration:" in line:
            parts = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = parts.split(":")
            return float(h) * 3600 + float(m) * 60 + float(s)
    return 0.0


def main():
    print("=" * 60)
    print("MERGING MARGINWHY DEMO VIDEO & AUDIO")
    print("=" * 60)

    # 1. Create Concat List
    concat_list = AUDIO_DIR / "concat_list.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for seg in SEGMENTS:
            p = AUDIO_DIR / f"{seg}.mp3"
            clean_path = str(p.resolve()).replace('\\', '/')
            f.write(f"file '{clean_path}'\n")

    full_audio = AUDIO_DIR / "full_narration.mp3"
    print("Concatenating audio segments into master narration track...")
    concat_cmd = [
        FFMPEG_PATH, "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy",
        str(full_audio)
    ]
    subprocess.run(concat_cmd, check=True, text=True, encoding="utf-8", errors="replace")
    audio_dur = get_duration(full_audio)
    print(f"Master audio generated: {audio_dur:.2f}s ({int(audio_dur//60)}m {int(audio_dur%60)}s)")

    # 2. Find WebM file
    webm_files = sorted(RAW_DIR.glob("*.webm"), key=lambda p: p.stat().st_size, reverse=True)
    if not webm_files:
        raise RuntimeError("No WebM files found!")
    target_webm = webm_files[0]
    webm_dur = get_duration(target_webm)
    print(f"Selected WebM file: {target_webm.name} ({target_webm.stat().st_size / (1024*1024):.2f} MB, Duration: {webm_dur:.2f}s)")

    # 3. Merge with FFmpeg
    print(f"\nEncoding broadcast-grade 1080p MP4: {OUTPUT_MP4.name}...")
    merge_cmd = [
        FFMPEG_PATH, "-y",
        "-i", str(target_webm),
        "-i", str(full_audio),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(OUTPUT_MP4)
    ]
    subprocess.run(merge_cmd, check=True, text=True, encoding="utf-8", errors="replace")
    out_dur = get_duration(OUTPUT_MP4)
    out_size_mb = OUTPUT_MP4.stat().st_size / (1024 * 1024)
    print(f"\nSUCCESS! Master MP4 Video Generated:")
    print(f"  Duration: {out_dur:.2f}s ({int(out_dur//60)}m {int(out_dur%60)}s)")
    print(f"  File Size: {out_size_mb:.2f} MB")
    print(f"  Path: {OUTPUT_MP4.name}")

    # 4. Copy to Artifacts folder
    if ARTIFACT_DIR.exists():
        dest = ARTIFACT_DIR / OUTPUT_MP4.name
        shutil.copy2(OUTPUT_MP4, dest)
        print(f"  Copied to Artifacts folder: {dest.name}")

    print("\nAll tasks completed successfully!")


if __name__ == "__main__":
    main()
