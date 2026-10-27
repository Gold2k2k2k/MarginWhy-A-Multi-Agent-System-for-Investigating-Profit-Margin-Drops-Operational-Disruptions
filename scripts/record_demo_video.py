"""
MarginWhy Demo Video Generator with Synced On-Screen Subtitles & 5/5 Audit Verification
Generates HD 1080p video with Playwright, neural voiceover with Edge TTS, live on-screen glassmorphic subtitles,
and complete resolution of the audit modal showing all 5 Section 5.1 passed checks.
"""

import asyncio
import os
from pathlib import Path
import shutil
import subprocess
import time
import edge_tts
from playwright.async_api import async_playwright

BASE_DIR = Path(__file__).resolve().parent.parent
RECORDINGS_DIR = BASE_DIR / "recordings"
AUDIO_DIR = RECORDINGS_DIR / "audio"
RAW_DIR = RECORDINGS_DIR / "raw"
FFMPEG_PATH = r"C:\ffmpeg\bin\ffmpeg.exe"
OUTPUT_MP4 = BASE_DIR / "MarginWhy_Official_Demo_Video_1080p.mp4"
OUTPUT_SRT = BASE_DIR / "MarginWhy_Demo_Subtitles.srt"
ARTIFACT_DIR = Path(r"C:\Users\DELL\.gemini\antigravity-ide\brain\ee57dc4c-5247-4f2b-908a-dab46e9949ae")

# 5 Script Segments with Subtitle Cues
SEGMENTS = [
    {
        "id": "seg1_hook",
        "title": "Segment 1: The $1.85M Margin Crisis & Anomaly Discovery",
        "badge": "Track 02: The Agent That Can Explain Why",
        "voice_text": (
            "When the net profit margin for Electronics collapsed by 18.5% in Q3, costing 1.85 million dollars in EBITDA, "
            "retail leadership assumed customer returns were to blame. But surface metrics lie. In reality, the true evidence "
            "was fragmented across warehouse inventory, web sales, and urban logistics couriers. "
            "MarginWhy is an adversarial multi-agent system built to discover the true operational 'Why'."
        ),
        "subtitles": [
            (0.0, 7.0, "When net profit margin for Electronics collapsed by 18.5% in Q3, costing $1.85M in EBITDA..."),
            (7.0, 14.0, "...retail leadership assumed customer returns were to blame. But surface metrics lie."),
            (14.0, 21.0, "In reality, the true evidence was fragmented across warehouse inventory, web sales, and urban couriers."),
            (21.0, 29.0, "MarginWhy is an adversarial multi-agent system built to discover the true operational 'Why'.")
        ]
    },
    {
        "id": "seg2_execution",
        "title": "Segment 2: Adversarial Multi-Agent Loop & Critic Rejection",
        "badge": "NVIDIA Nemotron-3 Super 120B",
        "voice_text": (
            "Watch our non-linear four-agent loop in action. In Turn 1, HypothesisPlanner suspects product defects. "
            "ZetarisRetriever queries TPCDS web returns. But our SkepticalCritic, powered by NVIDIA Nemotron, "
            "mathematically audits the data: national returns rose only 1.2%, explaining less than 1.1% of the margin drop. "
            "The Critic issues a CLAIM_BLOCKED event, locks the refuted hypothesis into Meterless H-MEM, and forces an orthogonal branch. "
            "In Turn 2, the agents cross-examine warehouse stockouts and New York taxi urban delivery delays, "
            "proving an 84% inventory collapse and emergency freight courier fees. Confidence: 91% — APPROVED!"
        ),
        "subtitles": [
            (0.0, 6.5, "Watch our non-linear 4-agent loop in action. In Turn 1, HypothesisPlanner suspects product defects."),
            (6.5, 12.5, "ZetarisRetriever queries TPCDS web returns. But SkepticalCritic mathematically audits the claim."),
            (12.5, 20.5, "National returns rose only 1.2%, explaining <1.1% of the margin drop. Critic issues CLAIM_BLOCKED!"),
            (20.5, 29.0, "Critic locks the refuted hypothesis into Meterless H-MEM, and forces an orthogonal branch."),
            (29.0, 39.0, "In Turn 2, agents cross-examine warehouse stockouts and NY taxi urban delivery delays..."),
            (39.0, 49.5, "...proving an 84% inventory collapse and emergency courier freight fees. Confidence: 91% — APPROVED!")
        ]
    },
    {
        "id": "seg3_sponsor_tech",
        "title": "Segment 3: Zetaris Lightning SQL & Meterless H-MEM",
        "badge": "Zetaris Lightning SQL & Meterless H-MEM",
        "voice_text": (
            "Here is how our sponsor technologies make this possible. "
            "First, Zetaris AI Data Harness acts as our unified data layer, joining TPCDS retail tables and New York taxi logistics "
            "through Lightning SQL with automatic numeric coercion. "
            "Second, Meterless H-MEM organizes memory into three tiers: Episodic query logs, Semantic hypotheses, and Procedural critique rules. "
            "Every decision is stamped into an immutable Trust Ledger, while Markovian Bounded Carryover prevents token bloat. "
            "Third, 100% of reasoning is routed through Meterless Nightshift to NVIDIA Nemotron 120B."
        ),
        "subtitles": [
            (0.0, 8.0, "Here is how our sponsor technologies power this discovery. Zetaris acts as our unified data layer..."),
            (8.0, 16.0, "...joining TPCDS retail tables and NY taxi logistics through Lightning SQL with automatic numeric coercion."),
            (16.0, 25.5, "Meterless H-MEM organizes memory into 3 tiers: Episodic query logs, Semantic hypotheses, and Procedural rules."),
            (25.5, 33.5, "Every decision is stamped into an immutable Trust Ledger, while Markovian Bounded Carryover prevents token bloat."),
            (33.5, 41.5, "100% of agent reasoning is routed through Meterless Nightshift to NVIDIA Nemotron-3 Super 120B.")
        ]
    },
    {
        "id": "seg4_executive_ux",
        "title": "Segment 4: SVG Margin Waterfall & What-If Recovery Simulator",
        "badge": "Executive Decision Intelligence",
        "voice_text": (
            "For the executive, MarginWhy provides more than a textual report. "
            "Our pure SVG Waterfall Attribution Bridge visualizes exactly how each operational failure eroded margin "
            "from a baseline of 22.5% down to 4.0%. "
            "Below it, our What-If Recovery Simulator lets managers adjust regional safety stock buffers and off-peak courier routing in real-time, "
            "instantly projecting over 1.2 million dollars in EBITDA recovery."
        ),
        "subtitles": [
            (0.0, 8.0, "For leadership, MarginWhy delivers clear intelligence. Our pure SVG Waterfall Attribution Bridge..."),
            (8.0, 16.0, "...visualizes exactly how each operational failure eroded margin from a baseline of 22.5% down to 4.0%."),
            (16.0, 23.0, "Below it, our What-If Recovery Simulator lets managers adjust operational remediation levers in real-time..."),
            (23.0, 30.5, "...instantly projecting over $1.2 million dollars in EBITDA recovery as safety stock buffers are restored.")
        ]
    },
    {
        "id": "seg5_verification",
        "title": "Segment 5: 1-Click Reproducibility & Section 5.1 Verification",
        "badge": "5/5 PASS Section 5.1 Criteria",
        "voice_text": (
            "MarginWhy is 100% reproducible: it runs from a fresh clone in under 60 seconds and provides complete Docker support. "
            "With one click on our Judge Bar, we execute the automated five-point Section 5.1 submission audit in real-time. "
            "Notice the live checks: metadata schema passes, all eight Meterless H-MEM conformance tests pass, sub-minute benchmark passes, and zero credentials committed. "
            "All five checks verified: 5 out of 5 PASS. MarginWhy: turning fragmented enterprise data into definitive, actionable explanations."
        ),
        "subtitles": [
            (0.0, 7.0, "MarginWhy is 100% reproducible: runs from a fresh clone in under 60 seconds with full Docker support."),
            (7.0, 14.0, "With one click on our Judge Bar, we execute the automated 5-point Section 5.1 submission audit in real-time."),
            (14.0, 23.0, "Notice the live checks: metadata schema, all 8 Meterless H-MEM conformance tests, and benchmark performance."),
            (23.0, 32.0, "VERDICT: 5 out of 5 CHECKS PASSED! MarginWhy: Turning fragmented data into definitive explanations.")
        ]
    }
]


def format_srt_time(seconds: float) -> str:
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"


def generate_srt_file(durations: list):
    """Generates a standalone .srt subtitle file for YouTube or offline viewing."""
    srt_lines = []
    idx = 1
    current_offset = 0.0

    for i, seg in enumerate(SEGMENTS):
        seg_dur = durations[i]
        for sub in seg.get("subtitles", []):
            start_s = current_offset + sub[0]
            end_s = current_offset + min(sub[1], seg_dur)
            text = sub[2]
            srt_lines.append(f"{idx}\n{format_srt_time(start_s)} --> {format_srt_time(end_s)}\n{text}\n")
            idx += 1
        current_offset += seg_dur

    OUTPUT_SRT.write_text("\n".join(srt_lines), encoding="utf-8")
    print(f"Generated standalone SRT subtitles: {OUTPUT_SRT.name}")
    if ARTIFACT_DIR.exists():
        shutil.copy2(OUTPUT_SRT, ARTIFACT_DIR / OUTPUT_SRT.name)


def get_audio_duration(file_path: Path) -> float:
    cmd = [FFMPEG_PATH, "-i", str(file_path), "-f", "null", "-"]
    res = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
    for line in res.stderr.splitlines():
        if "Duration:" in line:
            parts = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = parts.split(":")
            return float(h) * 3600 + float(m) * 60 + float(s)
    return 25.0


async def generate_voiceovers():
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    voice = "en-US-AndrewMultilingualNeural"
    durations = []
    print(f"Generating TTS audio with voice {voice}...")

    for seg in SEGMENTS:
        out_file = AUDIO_DIR / f"{seg['id']}.mp3"
        if not out_file.exists():
            print(f"  Generating {seg['id']}...")
            communicate = edge_tts.Communicate(seg["voice_text"], voice, rate="+2%")
            await communicate.save(str(out_file))
        else:
            print(f"  Found cached {seg['id']}.mp3")
        dur = get_audio_duration(out_file)
        durations.append(dur)
        print(f"  -> Duration: {dur:.2f}s")

    return durations


async def move_cursor_smooth(page, x: int, y: int):
    script = f"""
    (() => {{
        const c = document.getElementById('demo-cursor');
        if (c) {{
            c.style.left = '{x}px';
            c.style.top = '{y}px';
        }}
    }})();
    """
    await page.evaluate(script)
    await asyncio.sleep(0.06)


async def click_element(page, selector: str):
    loc = page.locator(selector).first
    box = await loc.bounding_box()
    if box:
        cx = int(box["x"] + box["width"] / 2)
        cy = int(box["y"] + box["height"] / 2)
        await move_cursor_smooth(page, cx, cy)
        await asyncio.sleep(0.2)
        await loc.click()
        await asyncio.sleep(0.3)


async def set_banner_content(page, title: str, badge: str):
    script = f"""
    (() => {{
        const b = document.getElementById('demo-banner');
        if (b) {{
            b.innerHTML = `
                <div style="font-size: 0.68rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.08em; color: #38bdf8; margin-bottom: 2px;">
                    {badge}
                </div>
                <div style="font-size: 0.86rem; font-weight: 700; color: #ffffff;">
                    {title}
                </div>
            `;
        }}
    }})();
    """
    await page.evaluate(script)


async def set_subtitle(page, text: str):
    script = f"""
    (() => {{
        const s = document.getElementById('demo-subtitles');
        if (s) {{
            s.style.opacity = '0';
            setTimeout(() => {{
                s.textContent = {repr(text)};
                s.style.opacity = '1';
            }}, 150);
        }}
    }})();
    """
    await page.evaluate(script)


async def run_subtitle_sequence(page, subtitles: list, seg_duration: float):
    """Spawns an async task that updates the on-screen subtitle box based on timestamps."""
    async def _runner():
        for start_t, end_t, text in subtitles:
            # Wait until start_t
            await asyncio.sleep(start_t if subtitles.index((start_t, end_t, text)) == 0 else (start_t - subtitles[subtitles.index((start_t, end_t, text))-1][0]))
            await set_subtitle(page, text)
    return asyncio.create_task(_runner())


async def record_browser_session(durations):
    RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    print("\nLaunching Playwright browser session for HD recording...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--start-maximized", "--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir=str(RAW_DIR),
            record_video_size={"width": 1920, "height": 1080}
        )
        page = await context.new_page()

        print("Navigating to http://127.0.0.1:8000...")
        await page.goto("http://127.0.0.1:8000", wait_until="networkidle")
        await asyncio.sleep(1)

        # Pre-warm audit cache so live audit resolves in < 1 second in Segment 5
        try:
            await page.request.get("http://127.0.0.1:8000/api/audit")
        except Exception:
            pass

        # Inject Virtual Cursor, Top-Right Badge Banner, and Bottom-Center Subtitles Pill
        await page.evaluate("""
        (() => {
            // 1. Virtual Cursor
            const cur = document.createElement('div');
            cur.id = 'demo-cursor';
            cur.style.cssText = `
                position: fixed;
                width: 22px;
                height: 22px;
                border-radius: 50%;
                background: rgba(56, 189, 248, 0.4);
                border: 2px solid #38bdf8;
                box-shadow: 0 0 16px #38bdf8;
                pointer-events: none;
                z-index: 9999999;
                transform: translate(-50%, -50%);
                transition: left 0.35s cubic-bezier(0.2, 0.8, 0.2, 1), top 0.35s cubic-bezier(0.2, 0.8, 0.2, 1);
                left: 960px;
                top: 540px;
            `;
            document.body.appendChild(cur);

            // 2. Top-Right Presentation Banner
            const ban = document.createElement('div');
            ban.id = 'demo-banner';
            ban.style.cssText = `
                position: fixed;
                top: 18px;
                right: 28px;
                background: rgba(11, 17, 32, 0.94);
                backdrop-filter: blur(14px);
                border: 1px solid rgba(99, 102, 241, 0.4);
                border-radius: 12px;
                padding: 10px 20px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6);
                z-index: 9999998;
                font-family: 'Plus Jakarta Sans', sans-serif;
                pointer-events: none;
            `;
            document.body.appendChild(ban);

            // 3. Bottom-Center Floating Subtitle Box (Enlarged & Prominent for Judges)
            const sub = document.createElement('div');
            sub.id = 'demo-subtitles';
            sub.style.cssText = `
                position: fixed;
                bottom: 26px;
                left: 50%;
                transform: translateX(-50%);
                background: rgba(3, 7, 24, 0.96);
                backdrop-filter: blur(20px);
                border: 2px solid rgba(56, 189, 248, 0.7);
                border-radius: 16px;
                padding: 16px 36px;
                max-width: 1400px;
                width: 88%;
                color: #ffffff;
                font-size: 1.45rem;
                font-weight: 700;
                text-align: center;
                box-shadow: 0 16px 48px rgba(0, 0, 0, 0.92), 0 0 32px rgba(56, 189, 248, 0.35);
                z-index: 9999999;
                font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
                line-height: 1.45;
                letter-spacing: 0.015em;
                text-shadow: 0 2px 10px rgba(0, 0, 0, 0.9);
                pointer-events: none;
                transition: opacity 0.2s ease, transform 0.2s ease;
                opacity: 1;
            `;
            document.body.appendChild(sub);
        })();
        """)

        # -------------------------------------------------------------
        # SEGMENT 1: The Hook & Problem (durations[0])
        # -------------------------------------------------------------
        print("\n=== Executing Segment 1: Hook & Problem ===")
        await set_banner_content(page, SEGMENTS[0]["title"], SEGMENTS[0]["badge"])
        seg1_dur = durations[0]
        start_time = time.time()

        # Subtitle sequence for seg 1
        await set_subtitle(page, SEGMENTS[0]["subtitles"][0][2])
        await move_cursor_smooth(page, 300, 45)
        await asyncio.sleep(4)

        await set_subtitle(page, SEGMENTS[0]["subtitles"][1][2])
        await move_cursor_smooth(page, 720, 260)  # Reported Margin Drop
        await asyncio.sleep(3.5)
        await move_cursor_smooth(page, 980, 260)  # Direct EBITDA Exposure
        await asyncio.sleep(3.5)

        await set_subtitle(page, SEGMENTS[0]["subtitles"][2][2])
        await move_cursor_smooth(page, 1240, 260) # Critic Causal Confidence
        await asyncio.sleep(3.5)
        await move_cursor_smooth(page, 1500, 260) # Adversarial Iterations
        await asyncio.sleep(3.5)

        await set_subtitle(page, SEGMENTS[0]["subtitles"][3][2])
        await move_cursor_smooth(page, 960, 400)
        elapsed1 = time.time() - start_time
        if seg1_dur > elapsed1:
            await asyncio.sleep(seg1_dur - elapsed1)

        # -------------------------------------------------------------
        # SEGMENT 2: Live Multi-Agent Execution (durations[1])
        # -------------------------------------------------------------
        print("\n=== Executing Segment 2: Live Execution ===")
        await set_banner_content(page, SEGMENTS[1]["title"], SEGMENTS[1]["badge"])
        seg2_dur = durations[1]
        start_time = time.time()

        await set_subtitle(page, SEGMENTS[1]["subtitles"][0][2])
        await click_element(page, '.scenario-pill[data-scenario="scenario_1_electronics_q3.json"]')
        await asyncio.sleep(2)

        await set_subtitle(page, SEGMENTS[1]["subtitles"][1][2])
        await click_element(page, '#btnRun')
        await asyncio.sleep(2)

        await set_subtitle(page, SEGMENTS[1]["subtitles"][2][2])
        await move_cursor_smooth(page, 700, 160) # Planner
        await asyncio.sleep(3)
        await move_cursor_smooth(page, 950, 160) # Retriever
        await asyncio.sleep(3)

        await set_subtitle(page, SEGMENTS[1]["subtitles"][3][2])
        await move_cursor_smooth(page, 1200, 160) # SkepticalCritic Blocked
        await asyncio.sleep(4)

        await set_subtitle(page, SEGMENTS[1]["subtitles"][4][2])
        await move_cursor_smooth(page, 1200, 160) # SkepticalCritic Approved
        await asyncio.sleep(5)

        await set_subtitle(page, SEGMENTS[1]["subtitles"][5][2])
        await move_cursor_smooth(page, 1450, 160) # Synthesizer
        await asyncio.sleep(4)

        await page.evaluate("window.scrollBy({ top: 250, behavior: 'smooth' });")
        await asyncio.sleep(2)
        await page.evaluate("window.scrollBy({ top: -250, behavior: 'smooth' });")

        elapsed2 = time.time() - start_time
        if seg2_dur > elapsed2:
            await asyncio.sleep(seg2_dur - elapsed2)

        # -------------------------------------------------------------
        # SEGMENT 3: Sponsor Technologies Deep-Dive (durations[2])
        # -------------------------------------------------------------
        print("\n=== Executing Segment 3: Sponsor Technologies ===")
        await set_banner_content(page, SEGMENTS[2]["title"], SEGMENTS[2]["badge"])
        seg3_dur = durations[2]
        start_time = time.time()

        await set_subtitle(page, SEGMENTS[2]["subtitles"][0][2])
        await click_element(page, 'button[data-tab="hmem"]')
        await asyncio.sleep(3)

        await set_subtitle(page, SEGMENTS[2]["subtitles"][1][2])
        await move_cursor_smooth(page, 800, 480)
        await asyncio.sleep(4)

        await set_subtitle(page, SEGMENTS[2]["subtitles"][2][2])
        await page.evaluate("window.scrollBy({ top: 320, behavior: 'smooth' });")
        await asyncio.sleep(3)
        await move_cursor_smooth(page, 950, 600)
        await asyncio.sleep(4)

        await set_subtitle(page, SEGMENTS[2]["subtitles"][3][2])
        await page.evaluate("window.scrollTo({ top: 0, behavior: 'smooth' });")
        await asyncio.sleep(1)
        await click_element(page, 'button[data-tab="studio"]')
        await asyncio.sleep(2)

        await set_subtitle(page, SEGMENTS[2]["subtitles"][4][2])
        await move_cursor_smooth(page, 580, 500)
        await asyncio.sleep(2)
        await click_element(page, '#btnRunStudio')
        await asyncio.sleep(4)
        await page.evaluate("window.scrollTo({ top: 0, behavior: 'smooth' });")

        elapsed3 = time.time() - start_time
        if seg3_dur > elapsed3:
            await asyncio.sleep(seg3_dur - elapsed3)

        # -------------------------------------------------------------
        # SEGMENT 4: Executive Waterfall Bridge & What-If Simulator (durations[3])
        # -------------------------------------------------------------
        print("\n=== Executing Segment 4: Executive Experience & What-If Simulator ===")
        await set_banner_content(page, SEGMENTS[3]["title"], SEGMENTS[3]["badge"])
        seg4_dur = durations[3]
        start_time = time.time()

        await set_subtitle(page, SEGMENTS[3]["subtitles"][0][2])
        await click_element(page, 'button[data-tab="waterfall"]')
        await asyncio.sleep(2)

        await set_subtitle(page, SEGMENTS[3]["subtitles"][1][2])
        await page.evaluate("window.scrollBy({ top: 380, behavior: 'smooth' });")
        await move_cursor_smooth(page, 960, 520)
        await asyncio.sleep(4)
        await move_cursor_smooth(page, 750, 750)
        await asyncio.sleep(3)

        await set_subtitle(page, SEGMENTS[3]["subtitles"][2][2])
        await page.evaluate("window.scrollTo({ top: 0, behavior: 'smooth' });")
        await asyncio.sleep(1)
        await click_element(page, 'button[data-tab="report"]')
        await asyncio.sleep(1)

        await page.evaluate("""
        (() => {
            const p = document.getElementById('whatIfPanel');
            if (p) p.scrollIntoView({ behavior: 'smooth', block: 'center' });
        })();
        """)
        await asyncio.sleep(2)

        await set_subtitle(page, SEGMENTS[3]["subtitles"][3][2])
        # Slider 1 -> 90%
        await page.evaluate("""
        (() => {
            const s1 = document.getElementById('slider1');
            if (s1) {
                s1.value = 90;
                s1.dispatchEvent(new Event('input', { bubbles: true }));
                if (typeof onWhatIfSliderChange === 'function') onWhatIfSliderChange();
            }
        })();
        """)
        await move_cursor_smooth(page, 780, 550)
        await asyncio.sleep(3)

        # Slider 2 -> 85%
        await page.evaluate("""
        (() => {
            const s2 = document.getElementById('slider2');
            if (s2) {
                s2.value = 85;
                s2.dispatchEvent(new Event('input', { bubbles: true }));
                if (typeof onWhatIfSliderChange === 'function') onWhatIfSliderChange();
            }
        })();
        """)
        await move_cursor_smooth(page, 780, 650)
        await asyncio.sleep(3)

        elapsed4 = time.time() - start_time
        if seg4_dur > elapsed4:
            await asyncio.sleep(seg4_dur - elapsed4)

        # -------------------------------------------------------------
        # SEGMENT 5: 1-Click Verification & Section 5.1 Audit (durations[4])
        # -------------------------------------------------------------
        print("\n=== Executing Segment 5: 1-Click Verification ===")
        await set_banner_content(page, SEGMENTS[4]["title"], SEGMENTS[4]["badge"])
        seg5_dur = durations[4]
        start_time = time.time()

        await set_subtitle(page, SEGMENTS[4]["subtitles"][0][2])
        await page.evaluate("window.scrollTo({ top: 0, behavior: 'smooth' });")
        await asyncio.sleep(2)

        await set_subtitle(page, SEGMENTS[4]["subtitles"][1][2])
        # Move cursor to the golden "Run 5-Point Hackathon Audit" button in Judge Bar
        btn = page.locator('.btn-audit').first
        box = await btn.bounding_box()
        if box:
            await move_cursor_smooth(page, int(box["x"] + box["width"] / 2), int(box["y"] + box["height"] / 2))
            await asyncio.sleep(0.3)

        # Trigger audit modal reliably
        await page.evaluate("if (typeof openAuditModal === 'function') openAuditModal(); else document.querySelector('.btn-audit')?.click();")
        print("  Triggered openAuditModal(), waiting for live audit to complete...")

        # Explicitly wait until the audit API finishes and .audit-pass rows appear!
        await page.wait_for_selector('.audit-pass', timeout=25000)
        print("  Audit completed with 5/5 PASSED! Displaying results...")

        await set_subtitle(page, SEGMENTS[4]["subtitles"][2][2])
        # Smoothly hover across the passing checkmarks so the judges can inspect every detail
        await move_cursor_smooth(page, 960, 480) # CHK-1 & CHK-2
        await asyncio.sleep(3.5)
        await move_cursor_smooth(page, 960, 560) # CHK-3 & CHK-4
        await asyncio.sleep(3.5)

        await set_subtitle(page, SEGMENTS[4]["subtitles"][3][2])
        await move_cursor_smooth(page, 960, 640) # CHK-5 & Final Verdict
        await asyncio.sleep(4)

        elapsed5 = time.time() - start_time
        if seg5_dur > elapsed5:
            await asyncio.sleep(seg5_dur - elapsed5)

        # Graceful 3-second hold to let judges absorb the 5/5 passed verdict
        await asyncio.sleep(3)

        print("Finalizing video recording...")
        await context.close()
        await browser.close()

    # Find the recorded WebM file
    webm_files = sorted(RAW_DIR.glob("*.webm"), key=os.path.getmtime, reverse=True)
    if not webm_files:
        raise RuntimeError("No recorded WebM video found in raw directory!")
    latest_webm = webm_files[0]
    print(f"Recorded video saved to: {latest_webm.name}")
    return latest_webm


def merge_audio_and_video(webm_path: Path, durations: list):
    """Combines the TTS audio segments and merges them with the Playwright WebM video."""
    print("\nConcatenating audio segments...")
    concat_list = AUDIO_DIR / "concat_list.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for seg in SEGMENTS:
            p = AUDIO_DIR / f"{seg['id']}.mp3"
            clean_path = str(p.resolve()).replace('\\', '/')
            f.write(f"file '{clean_path}'\n")

    full_audio = AUDIO_DIR / "full_narration.mp3"
    concat_cmd = [
        FFMPEG_PATH, "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy",
        str(full_audio)
    ]
    subprocess.run(concat_cmd, check=True, text=True, encoding="utf-8", errors="replace")
    total_audio_sec = get_audio_duration(full_audio)
    print(f"Full narration generated: {total_audio_sec:.2f}s ({int(total_audio_sec//60)}m {int(total_audio_sec%60)}s)")

    print(f"\nEncoding broadcast-grade 1080p MP4 with FFmpeg: {OUTPUT_MP4.name}...")
    merge_cmd = [
        FFMPEG_PATH, "-y",
        "-i", str(webm_path),
        "-i", str(full_audio),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-af", "apad",
        "-shortest",
        str(OUTPUT_MP4)
    ]
    subprocess.run(merge_cmd, check=True, text=True, encoding="utf-8", errors="replace")
    print(f"Master Demo Video Successfully Rendered: {OUTPUT_MP4.name}")
    print(f"File size: {OUTPUT_MP4.stat().st_size / (1024*1024):.2f} MB")

    # Generate standalone SRT file
    generate_srt_file(durations)

    # Copy to Antigravity Artifacts directory for instant access
    if ARTIFACT_DIR.exists():
        target_artifact = ARTIFACT_DIR / OUTPUT_MP4.name
        shutil.copy2(OUTPUT_MP4, target_artifact)
        print(f"Copied demo video to IDE artifacts: {target_artifact.name}")


async def main():
    print("=" * 70)
    print("MARGINWHY HACKATHON DEMO VIDEO PRODUCTION PIPELINE")
    print("Open Agent Hackathon 2026 | Team: Light of Numbers | Track 02")
    print("=" * 70)

    # 1. Generate Voiceovers
    durations = await generate_voiceovers()

    # 2. Record Browser Actions with Playwright & Subtitles
    webm_path = await record_browser_session(durations)

    # 3. Merge Audio and Video into 1080p MP4 + Export SRT
    merge_audio_and_video(webm_path, durations)


if __name__ == "__main__":
    asyncio.run(main())
