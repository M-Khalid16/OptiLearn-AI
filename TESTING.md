# OptiLearn AI Testing Guide

Run tests from the repository root after installing `requirements.txt`.

## Required release checks

```bash
git status
git diff --check
python -m tabnanny app.py
python -m py_compile app.py src/*.py
```

## Streamlit startup check

```bash
streamlit run app.py --server.headless true --server.port 8501
```

Wait until Streamlit reports a local URL, then stop the process with `Ctrl+C`.

## AppTest page-render check

```bash
python - <<'PY'
from streamlit.testing.v1 import AppTest
pages = ("Home", "Lecture Notes", "Digital Twin", "AI Tutor", "Quiz Lab", "Mode Explorer")
for page in pages:
    at = AppTest.from_file("app.py", default_timeout=15)
    at.session_state["sidebar_navigation"] = page
    at.run()
    if at.exception:
        raise RuntimeError(f"{page} failed: {at.exception}")
    print(f"OK {page}")
PY
```

## Structural audit

```bash
python - <<'PY'
import ast
from pathlib import Path
source = Path("app.py").read_text()
tree = ast.parse(source)
required = [
    "_is_demo_mode_enabled", "_request_page", "_consume_requested_page", "render_home",
    "parse_uploaded_pdf", "_display_empty_lecture_notes_state", "_format_metadata_value",
    "_download_filename", "render_lecture_notes", "render_digital_twin", "render_ai_tutor",
    "render_quiz", "render_mode_explorer", "render_sidebar", "main",
]
for name in required:
    count = sum(isinstance(n, ast.FunctionDef) and n.name == name for n in tree.body)
    assert count == 1, (name, count)
for name in ["PAGES", "APP_VERSION"]:
    count = sum(isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in n.targets) for n in tree.body)
    assert count == 1, (name, count)
navigation_radios = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == 'radio' and n.args and isinstance(n.args[0], ast.Constant) and n.args[0].value == 'Navigation']
assert len(navigation_radios) == 1
assert source.count('key="sidebar_navigation"') == 1
assert source.count('st.session_state["sidebar_navigation"] = requested_page') == 1
for forbidden in ["navigation_generation", "sidebar_navigation_"]:
    assert forbidden not in source, forbidden
assert source.rstrip().endswith('if __name__ == "__main__":\n    main()')
print("structural audit passed")
PY
```

## Deterministic feature checks

- Digital Twin: run fiber attenuation, chromatic dispersion, and FSO examples without setting `OPENAI_API_KEY`.
- Quiz Lab: answer questions and confirm deterministic feedback appears without OpenAI.
- Mode Explorer: generate LP mode, coupling, meridional ray, and skew ray visualizations without OpenAI.
- Lecture Notes:
  1. Open `examples/sample_optical_notes.md`.
  2. Export it manually as a text-based PDF.
  3. Upload the exported PDF to Lecture Notes.
  4. Confirm that page text is extracted.
  5. Confirm that the document is not classified as scanned.
- AI Tutor: with no API key, confirm the interface explains that live AI access is unavailable rather than crashing.

## Security and cleanliness checks

Manually confirm that no real OpenAI API key, committed `.env` secret, repository placeholder, or author placeholder appears in tracked files. Keep `OPENAI_API_KEY` values empty in examples and use Streamlit secrets for deployment.
