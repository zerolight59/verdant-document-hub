# Walkthrough upload file

`battery-enclosure-v3.pdf` is entirely fictional and ready to upload during the visual guide's live demonstration.

Sign in as `EMP-1071`, open **DEMO - Atlas EV platform > Battery enclosure drawing**, read the feedback, and upload this PDF as a new version. Enter the change summary: "Increased the illustrative flange clearance from 12 mm to 16 mm." Then submit it to the assigned reviewer.

Sign in as `EMP-1088` to start review, compare versions and approve or request changes.

Never use these invented values for real engineering work. Uploading the file performs a real change in your demo database. The seed does not reset that change.

To regenerate a missing fixture, run `python -m scripts.export_demo_files` from backend/. Existing fixture files are preserved.
