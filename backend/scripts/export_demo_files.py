"""Generate a ready-to-upload, fictional revision for the user-guide walkthrough."""

from pathlib import Path

from scripts.demo_files import demo_pdf


def main() -> None:
    folder = Path(__file__).resolve().parents[2] / "demo-files"
    folder.mkdir(exist_ok=True)
    path = folder / "battery-enclosure-v3.pdf"
    if path.exists():
        print(f"Preserved existing walkthrough file: {path}")
        return
    path.write_bytes(
        demo_pdf(
            "Battery enclosure drawing",
            "DEMO - Atlas EV platform",
            3,
            [
                "Corrected fictional flange clearance from 12 mm to 16 mm.",
                "Revision note updated in response to Vikram's sample review feedback.",
                "Fictional design parameter: clearance 16 mm.",
                "Prepared by Mira Nair for the local demonstration walkthrough.",
                "NOT FOR ENGINEERING, PROCUREMENT OR SAFETY DECISIONS.",
            ],
        )
    )
    print(path)


if __name__ == "__main__":
    main()
