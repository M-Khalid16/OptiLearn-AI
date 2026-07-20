"""Reusable Streamlit UI components for OptiLearn AI."""

import html

import streamlit as st

_TONES = {
    "neutral": "badge-neutral",
    "success": "badge-success",
    "warning": "badge-warning",
    "information": "badge-info",
}


def inject_global_styles() -> None:
    """Inject the small scoped visual system used by the app."""
    st.markdown(
        """
<style>
:root { --optilearn-navy:#0f2742; --optilearn-cyan:#0891b2; --optilearn-violet:#6d5bd0; }
html, body, [class*="css"] { font-family: "Aptos", "Segoe UI", Arial, sans-serif; }
.optilearn-hero, .optilearn-card, .optilearn-notice, .optilearn-next, .optilearn-footer, .optilearn-panel {
  border: 1px solid rgba(8, 145, 178, 0.22); border-radius: .9rem; padding: .95rem 1rem;
  background: linear-gradient(135deg, rgba(15, 39, 66, 0.06), rgba(109, 91, 208, 0.06));
}
.optilearn-hero { position: relative; padding: 1.35rem 1.45rem; overflow: hidden; }
.optilearn-hero::after { content:""; position:absolute; inset:0; pointer-events:none; background: radial-gradient(circle at 88% 18%, rgba(8,145,178,.16), transparent 26%), repeating-linear-gradient(168deg, transparent 0 22px, rgba(8,145,178,.06) 23px, transparent 24px); }
.optilearn-product { color: var(--optilearn-navy); font-size: clamp(2.2rem, 4vw, 2.6rem); font-weight: 750; margin-bottom: .15rem; }
.optilearn-tagline { font-size: 1.08rem; color: inherit; opacity: .86; margin-bottom: 1rem; }
.optilearn-hero-statement { font-family: "Book Antiqua", "Palatino Linotype", Palatino, Georgia, serif; font-size: clamp(1.55rem, 3vw, 2.08rem); line-height: 1.25; font-weight: 500; max-width: 58rem; margin: .5rem 0 .75rem 0; }
.optilearn-prose { font-size: 1.08rem; line-height: 1.62; max-width: 66rem; }
.optilearn-eyebrow { color: var(--optilearn-cyan); font-weight: 700; letter-spacing: .08em; text-transform: uppercase; font-size: .78rem; }
.optilearn-card { min-height: 7.6rem; margin-bottom: .7rem; }
.optilearn-card h3 { margin: .1rem 0 .32rem 0; font-size: 1.08rem; }
.optilearn-card p { margin-bottom: 0; line-height: 1.48; }
.optilearn-badge { display:inline-block; border-radius:999px; padding:.16rem .5rem; font-size:.76rem; font-weight:700; margin:.08rem .18rem .3rem 0; border:1px solid currentColor; }
.badge-neutral { color:#475569; background:rgba(100,116,139,.10); }
.badge-success { color:#078a58; background:rgba(16,185,129,.12); }
.badge-warning { color:#b45309; background:rgba(245,158,11,.14); }
.badge-info { color:#0869a1; background:rgba(14,165,233,.12); }
.optilearn-next { border-left: .28rem solid var(--optilearn-violet); }
.optilearn-footer { font-size:.9rem; color:inherit; opacity:.88; margin-top:2rem; }
@media (max-width: 760px) { .optilearn-card { min-height: auto; } .optilearn-hero { padding: 1rem; } .optilearn-prose { font-size: 1rem; } }
</style>
""",
        unsafe_allow_html=True,
    )


def _e(text: str) -> str:
    return html.escape(str(text))


def render_status_badge(text: str, tone: str) -> None:
    """Render a labelled badge with a validated tone."""
    if tone not in _TONES:
        raise ValueError(f"Unsupported badge tone: {tone}")
    st.markdown(f'<span class="optilearn-badge {_TONES[tone]}">{_e(text)}</span>', unsafe_allow_html=True)


def render_page_header(title: str, subtitle: str, eyebrow: str | None = None, badge: str | None = None) -> None:
    """Render a consistent page header."""
    if eyebrow:
        st.markdown(f'<div class="optilearn-eyebrow">{_e(eyebrow)}</div>', unsafe_allow_html=True)
    if badge:
        render_status_badge(badge, "information")
    st.title(title)
    st.write(subtitle)


def render_scope_notice(supported: str, excluded: str) -> None:
    """Render a concise model-scope notice."""
    st.markdown(
        f'<div class="optilearn-notice"><strong>Supported:</strong> {_e(supported)}<br><strong>Not included:</strong> {_e(excluded)}</div>',
        unsafe_allow_html=True,
    )


def render_feature_card(icon: str, title: str, body: str, badge: str | None = None) -> None:
    """Render one feature card."""
    badge_html = f'<span class="optilearn-badge badge-neutral">{_e(badge)}</span>' if badge else ""
    st.markdown(f'<div class="optilearn-card"><div>{_e(icon)}</div>{badge_html}<h3>{_e(title)}</h3><p>{_e(body)}</p></div>', unsafe_allow_html=True)


def render_learning_step(number: int, title: str, body: str) -> None:
    """Render one learning journey step. The number is accepted for API stability but not displayed."""
    st.markdown(f'<div class="optilearn-card"><h3>{_e(title)}</h3><p>{_e(body)}</p></div>', unsafe_allow_html=True)


def render_scientific_trust_panel() -> None:
    """Render the shared scientific trust panel."""
    st.markdown(
        """
<div class="optilearn-notice"><strong>Built for Scientific Transparency</strong><br>
<strong>Deterministic First:</strong> Python calculates scientific values and validates inputs.<br>
<strong>Evidence Before Explanation:</strong> AI receives locally prepared simulation evidence or retrieved lecture-note passages.<br>
<strong>Assumptions Made Visible:</strong> Every model states what is included and excluded.<br>
<strong>No Invented Performance Claims:</strong> Unsupported BER, SNR, receiver, turbulence, or full-vector results are not fabricated.<br>
<strong>Learning with Boundaries:</strong> Educational approximations are clearly distinguished from experimental-grade modelling.</div>
""",
        unsafe_allow_html=True,
    )


def render_next_step(title: str, body: str, destination: str) -> None:
    """Render a cross-page learning suggestion."""
    st.markdown(f'<div class="optilearn-next"><strong>{_e(title)}</strong><p>{_e(body)}</p><span class="optilearn-badge badge-info">Next: {_e(destination)}</span></div>', unsafe_allow_html=True)


def render_footer() -> None:
    """Render the shared footer once per page."""
    st.markdown('<div class="optilearn-footer">OptiLearn AI — deterministic educational optics with transparent AI assistance. No persistent learner profile.</div>', unsafe_allow_html=True)
