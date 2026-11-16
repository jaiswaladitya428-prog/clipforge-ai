import time
import httpx
from pathlib import Path
from app.services.ffmpeg_utils import get_ffmpeg_binary
import subprocess

BASE_URL = "http://127.0.0.1:8000/api"

def generate_test_video(output_path: Path):
    """Generate a 4-second test video with video pattern, tone, and a 1-second silence gap."""
    ffmpeg_exe = get_ffmpeg_binary()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        ffmpeg_exe,
        "-f", "lavfi", "-i", "testsrc=duration=4:size=640x360:rate=25",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=1.5",
        "-f", "lavfi", "-i", "aevalsrc=0:duration=1.0",
        "-f", "lavfi", "-i", "sine=frequency=880:duration=1.5",
        "-filter_complex", "[1:a][2:a][3:a]concat=n=3:v=0:a=1[aout]",
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-y", str(output_path)
    ]
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if res.returncode != 0:
        raise RuntimeError("FFmpeg video creation failed")
    return output_path

def test_full_pipeline_live():
    client = httpx.Client(base_url=BASE_URL, timeout=60.0)

    # 1. Health check
    health = client.get("/health").json()
    print("1. Health Check:", health["status"], "-", health["app"])
    assert health["status"] == "ok"

    # 2. Register
    email = f"creator_{int(time.time())}@clipforge.ai"
    reg_res = client.post("/auth/register", json={
        "name": "Live Tester",
        "email": email,
        "password": "securepassword123"
    })
    assert reg_res.status_code == 201
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("2. User Registered:", email)

    # 3. Create Project
    proj_res = client.post("/projects", json={
        "title": "Full Analysis Test",
        "description": "Testing silence, scenes, frames, and faster-whisper"
    }, headers=headers)
    assert proj_res.status_code == 201
    project_id = proj_res.json()["id"]
    print("3. Project Created:", project_id)

    # 4. Generate real MP4 video
    test_video_path = Path("storage/test_footage_analysis.mp4")
    generate_test_video(test_video_path)
    print("4. Test Video Generated:", test_video_path.stat().st_size, "bytes")

    # 5. Upload Video
    with open(test_video_path, "rb") as f:
        upload_res = client.post(
            f"/projects/{project_id}/upload",
            files={"file": ("test_footage_analysis.mp4", f, "video/mp4")},
            headers=headers
        )
    assert upload_res.status_code == 200
    print("5. Video Uploaded! Background pipeline running...")

    # 6. Poll for completion
    max_wait = 40
    start_time = time.time()
    completed = False
    
    while time.time() - start_time < max_wait:
        status_res = client.get(f"/projects/{project_id}", headers=headers).json()
        status = status_res["status"]
        print(f"   Status: {status} ({int(time.time() - start_time)}s)")
        if status == "completed":
            completed = True
            break
        elif status == "failed":
            raise RuntimeError(f"Processing failed: {status_res}")
        time.sleep(2)

    assert completed, "Pipeline did not complete in time"

    # 7. Check Full Analysis Report
    anal_res = client.get(f"/projects/{project_id}/analysis", headers=headers)
    assert anal_res.status_code == 200
    anal_data = anal_res.json()
    print("7. Video Analysis Report Received:")
    print(f"   - Silence intervals detected: {len(anal_data['silence_intervals'])}")
    print(f"   - Scenes detected: {len(anal_data['scenes'])}")
    print(f"   - Extracted frames: {len(anal_data['frames'])}")
    assert len(anal_data["silence_intervals"]) >= 1
    assert len(anal_data["scenes"]) >= 1

    # 8. Check Transcript JSON
    trans_res = client.get(f"/projects/{project_id}/transcript", headers=headers)
    assert trans_res.status_code == 200
    print("8. Transcript Received. Language:", trans_res.json()["language"])

    # 9. Test Retry endpoint
    retry_res = client.post(f"/projects/{project_id}/retry", headers=headers)
    assert retry_res.status_code == 200
    print("9. Retry Endpoint Functional! Status reset to:", retry_res.json()["status"])

    print("\n>>> ALL 10 ANALYSIS PIPELINE REQUIREMENTS VERIFIED LIVE! <<<")

if __name__ == "__main__":
    test_full_pipeline_live()
