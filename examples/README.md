# OptiLearn AI Example Learning Material

This directory contains project-authored sample optical-communication notes for testing the Lecture Notes and AI Tutor workflows.

## Files

- `sample_optical_notes.md` — editable Markdown source for the sample notes.

## How to use the sample notes

The repository includes the original sample notes as Markdown to keep the source reviewable. To test the PDF workflow, export this file to a text-based PDF using a word processor or browser print-to-PDF function. A binary sample PDF is intentionally not stored in this repository. The application itself still supports user-uploaded text-based PDFs.

1. Launch OptiLearn AI with `streamlit run app.py`.
2. Open `examples/sample_optical_notes.md` and export it manually as a text-based PDF.
3. Open the **Lecture Notes** page.
4. Upload the exported PDF.
5. Confirm that page text and metadata appear.
6. If OpenAI API access is configured, open **AI Tutor** and ask questions grounded in the uploaded notes.

Suggested questions:

- What happens when fiber distance increases?
- Why does spectral width matter for chromatic dispersion?
- Which parameters affect a free-space optical link budget?
- How are LP modes different from ray diagrams?

The content is intentionally concise and original so it can be used safely for repository validation and demonstration.
