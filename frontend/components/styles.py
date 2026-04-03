import streamlit as st


def inject_global_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

        :root {
            --ink: #0f1f1a;
            --muted: #4b5b54;
            --accent: #1a9f78;
            --accent-dark: #137a5c;
            --bg: #f7f3ed;
            --card: #ffffff;
            --sand: #efe7da;
            --line: #d9d0c4;
        }

        html, body, [class*="css"]  {
            font-family: 'IBM Plex Sans', sans-serif;
            color: var(--ink);
        }

        .stApp {
            background: radial-gradient(1200px 600px at 15% 0%, #ffffff 0%, var(--bg) 60%);
        }

        header, footer { visibility: hidden; }

        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 3rem;
        }

        h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
            font-family: 'Space Grotesk', sans-serif;
            letter-spacing: -0.01em;
        }

        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #f2ece3 0%, #f9f6f1 100%);
            border-right: 1px solid var(--line);
        }

        .stButton > button, .stDownloadButton > button {
            background: var(--accent);
            color: white;
            border: 0;
            border-radius: 10px;
            padding: 0.6rem 1rem;
            font-weight: 600;
        }

        .stButton > button:hover, .stDownloadButton > button:hover {
            background: var(--accent-dark);
        }

        .stTextInput input, .stTextArea textarea, .stSelectbox select {
            border-radius: 10px !important;
            border: 1px solid var(--line) !important;
            background: #fffdf9 !important;
        }

        .card {
            background: var(--card);
            border: 1px solid var(--line);
            border-radius: 16px;
            padding: 1.25rem 1.5rem;
            box-shadow: 0 6px 20px rgba(15, 31, 26, 0.06);
        }

        .tag {
            display: inline-block;
            padding: 0.2rem 0.6rem;
            border-radius: 999px;
            background: var(--sand);
            color: var(--muted);
            font-size: 0.85rem;
            margin-right: 0.4rem;
        }

        .hero-grid {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 1.2rem;
        }

        @media (max-width: 900px) {
            .hero-grid {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
