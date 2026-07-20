# OptiLearn AI Demo Script (3–5 minutes)

## 1. Opening
- **Action:** Launch `streamlit run app.py`.

- **What to say:** “Students today can access more information than any previous generation, but information alone does not create engineering understanding. OptiLearn AI helps learners move from reading an equation to questioning it, changing its parameters, visualizing its consequences, and testing what they understand.”


- **What to say:** “Students today can access more information than any previous generation, but information alone does not create engineering understanding. OptiLearn AI helps learners move from reading an equation to questioning it, changing its parameters, visualizing its consequences, and testing what they understand.”

- **What to say:** “OptiLearn AI is an educational digital twin for optical communication. Deterministic Python calculates the physics; AI only explains supplied results or retrieved notes.”

- **Expected result:** App opens on the Home page.
- **Fallback if live AI is unavailable:** Enable `OPTILEARN_DEMO_MODE=true` to show labelled local templates.

## 2. Home page
- **Action:** Point to the hero, capability cards, guided journey, trust section, and Start Exploring button.
- **What to say:** “A new learner can see where to begin and why deterministic simulation matters.”
- **Expected result:** Clear routes to Digital Twin, Mode Explorer, and Lecture Notes.
- **Fallback:** Home never requires API access.

## 3. Fiber attenuation
- **Action:** Open Digital Twin → Optical Fiber → Attenuation Only. Use bit sequence `10110010`, bit rate `10 Gbit/s`, transmitted power `1 mW`, fiber length `20 km`, attenuation `0.2 dB/km`.
- **What to say:** “The model calculates loss in Python using the displayed equations.”
- **Expected result:** `4 dB` loss, approximately `0.398107 mW` received, and approximately `39.8107%` remaining.
- **Fallback:** Demo explanation can summarize these deterministic values without calling OpenAI.

## 4. Chromatic dispersion
- **Action:** Switch to Attenuation + Chromatic Dispersion. Use `D = 17 ps/(nm·km)`, spectral width `0.1 nm`, length `20 km`.
- **What to say:** “Dispersion broadens pulses in time; this is an educational Gaussian-convolution approximation.”
- **Expected result:** `34 ps`, `0.034 ns`, broadening ratio `0.34`, regime `Noticeable`.
- **Fallback:** Deterministic charts and equations remain available.

## 5. FSO link
- **Action:** Switch to Free-Space Optical. Use `1 km`, `10 mW`, `2 cm` beam radius, `1 mrad`, `20 cm` aperture, `1 dB/km`, zero pointing offset.
- **What to say:** “FSO power depends strongly on beam spreading and aperture collection.”
- **Expected result:** Approximately `1.02 m` beam radius, `1.904%` geometric capture, `0.151238 mW` received, regime `Weak collection`.
- **Fallback:** No API is needed.

## 6. Mode Explorer
- **Action:** Open Mode Explorer. Show Single-Mode Example, Multimode Example, select `LP11`, switch `cos(lφ)` and `sin(lφ)`, add beam offset, and show a skew ray.
- **What to say:** “Wave optics and ray optics are complementary educational views, not the same model.”
- **Expected result:** Mode fields, longitudinal view, launch coupling, meridional/skew ray paths.
- **Fallback:** Mode Explorer is fully deterministic.

## 7. Quiz Lab
- **Action:** Open Quiz Lab, start a quiz, submit one question, then create current-simulation questions if a simulation is active.
- **What to say:** “The quiz is locally graded and helps learners check understanding immediately.”
- **Expected result:** Deterministic feedback and score progress.
- **Fallback:** Quiz Lab never requires OpenAI.

## 8. Grounded AI Tutor
- **Action:** Upload a text-based PDF in Lecture Notes, then ask a question in AI Tutor.
- **What to say:** “The tutor retrieves page-level passages first, then asks OpenAI to answer from evidence.”
- **Expected result:** Answer, cited pages, evidence passages, model, and learning level.
- **Fallback:** If API access is unavailable, show the readiness state and transparent demo-mode label; do not claim a live answer.

## 9. Closing
- **Action:** Return to Home or Scientific Transparency.
- **What to say:** “OptiLearn AI is designed to help future engineers build not only knowledge, but also visual intuition, critical judgement, confidence, and lifelong-learning habits—the foundations they will need to contribute to the next generation of communication, photonic, and quantum technologies.”


- **What to say:** “OptiLearn AI is designed to help future engineers build not only knowledge, but also visual intuition, critical judgement, confidence, and lifelong-learning habits—the foundations they will need to contribute to the next generation of communication, photonic, and quantum technologies.”

- **What to say:** “OptiLearn AI turns equations into an explorable, trustworthy learning flow: calculate, visualize, explain, practise, and investigate.”


- **Expected result:** Audience understands the deterministic scientific architecture and AI boundaries.
- **Fallback:** The demo still works with deterministic pages only.
