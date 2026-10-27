"""
Export MarginWhy Presentation Deck (8 Slides) to High-Resolution 16:9 PDF
Captures each slide at 1920x1080 Full HD with Playwright and compiles into a presentation PDF.
"""

import asyncio
from pathlib import Path
from PIL import Image
from playwright.async_api import async_playwright
import shutil

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PDF = BASE_DIR / "MarginWhy_Presentation_Deck.pdf"
ARTIFACT_DIR = Path(r"C:\Users\DELL\.gemini\antigravity-ide\brain\ee57dc4c-5247-4f2b-908a-dab46e9949ae")
TEMP_DIR = BASE_DIR / "recordings" / "slides_temp"


async def export_slides():
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    slide_images = []

    print("Launching browser to capture 8 slides...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--start-maximized", "--no-sandbox"]
        )
        page = await browser.new_page(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=2 # 2x Retina rendering for ultra-crisp text
        )

        await page.goto("http://127.0.0.1:8000/slides", wait_until="networkidle")
        await asyncio.sleep(1)

        # Hide header and footer so each slide is pure widescreen content
        await page.evaluate("""
        (() => {
            const h = document.querySelector('header');
            if (h) h.style.display = 'none';
            const f = document.querySelector('footer');
            if (f) f.style.display = 'none';
            const dc = document.querySelector('.deck-container');
            if (dc) {
                dc.style.height = '1080px';
                dc.style.maxHeight = '1080px';
                dc.style.padding = '2.5rem 3.5rem';
                dc.style.boxSizing = 'border-box';
                dc.style.display = 'flex';
                dc.style.alignItems = 'center';
                dc.style.justifyContent = 'center';
            }
            document.querySelectorAll('.slide').forEach(s => {
                s.style.width = '100%';
                s.style.maxHeight = '980px';
                s.style.padding = '2.2rem 3rem';
                s.style.boxSizing = 'border-box';
            });
        })();
        """)
        await asyncio.sleep(0.5)

        for i in range(1, 9):
            print(f"  Capturing Slide {i} of 8...")
            await page.evaluate(f"showSlide({i});")
            await asyncio.sleep(0.3)

            img_path = TEMP_DIR / f"slide_{i}.png"
            await page.screenshot(path=str(img_path))
            slide_images.append(img_path)

        await browser.close()

    print("\nCompiling slides into master PDF...")
    pil_images = [Image.open(p).convert("RGB") for p in slide_images]
    if pil_images:
        pil_images[0].save(
            str(OUTPUT_PDF),
            save_all=True,
            append_images=pil_images[1:],
            resolution=150.0
        )
        print(f"Master Presentation PDF Created: {OUTPUT_PDF.name}")
        print(f"File Size: {OUTPUT_PDF.stat().st_size / (1024*1024):.2f} MB")

        if ARTIFACT_DIR.exists():
            target = ARTIFACT_DIR / OUTPUT_PDF.name
            shutil.copy2(OUTPUT_PDF, target)
            print(f"Copied to Artifacts: {target.name}")

    # Cleanup temp images
    shutil.rmtree(TEMP_DIR, ignore_errors=True)
    print("Done!")


if __name__ == "__main__":
    asyncio.run(export_slides())
