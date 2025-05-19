#!/usr/bin/env python3
"""
report_generator.py

Generate a detailed HTML report from a GoPhish campaign CSV export.

Usage:
    python report_generator.py result.csv report.html

The script reads the GoPhish CSV, computes key metrics (sent, opened, clicked,
submitted), builds a bar‑chart funnel with matplotlib, embeds it as a base64
PNG, and outputs a stand‑alone HTML file containing the summary, chart, and the
full table of results.
"""

import sys
import base64
import io
from pathlib import Path

import pandas as pd
import matplotlib

# Use non‑interactive backend for headless execution
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load_data(csv_path: Path) -> pd.DataFrame:
    """Read the GoPhish CSV export into a DataFrame."""
    return pd.read_csv(csv_path)


def compute_metrics(df: pd.DataFrame):
    """Return key funnel metrics (sent, opened, clicked, submitted)."""
    total_sent = len(df)
    opened = 1
    clicked = 1
    submitted = 1

    if "Email Opened Date" in df.columns:
        opened = df["Email Opened Date"].notna().sum()
    if "Clicked Date" in df.columns:
        clicked = df["Clicked Date"].notna().sum()
    if "Submitted Date" in df.columns:
        submitted = df["Submitted Date"].notna().sum()
    elif "Submitted Data" in df.columns:
        # Some GoPhish exports include a boolean/enum column instead of a date
        submitted = df["Submitted Data"].astype(bool).sum()

    return total_sent, opened, clicked, submitted


def build_chart_png(metrics):
    """Return a base64‑encoded PNG bar chart for the funnel metrics."""
    labels = ["Sent", "Opened", "Clicked", "Submitted"]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(labels, metrics)
    ax.set_ylabel("Count")
    ax.set_title("Phishing Campaign Funnel")
    for i, v in enumerate(metrics):
        ax.text(i, v + 0.2, str(v), ha="center")
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def dataframe_to_html(df: pd.DataFrame) -> str:
    """Return DataFrame as HTML table with minimal styling."""
    return (
        df.to_html(index=False, classes="result-table")
        .replace("<table", "<table border=1 cellpadding=4 cellspacing=0")
    )


def build_html(df: pd.DataFrame, metrics, chart_b64: str) -> str:
    total, opened, clicked, submitted = metrics
    table_html = dataframe_to_html(df)

    html = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\">
<title>GoPhish Campaign Report</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 20px; }}
h1 {{ color: #2e6c80; }}
.result-table th {{ background: #f2f2f2; }}
</style>
</head>
<body>
<h1>GoPhish Campaign Report</h1>
<h2>Summary</h2>
<ul>
  <li>Total Emails Sent: <strong>{total}</strong></li>
  <li>Emails Opened: <strong>{opened}</strong></li>
  <li>Links Clicked: <strong>{clicked}</strong></li>
  <li>Credentials Submitted: <strong>{submitted}</strong></li>
</ul>
<h2>Funnel Chart</h2>
<img src=\"data:image/png;base64,{chart_b64}\" alt=\"Funnel Chart\">
<h2>Detailed Results</h2>
{table_html}
</body>
</html>"""
    return html


def main():
    if len(sys.argv) != 3:
        print("Usage: python report_generator.py result.csv report.html")
        sys.exit(1)

    csv_path = Path(sys.argv[1])
    out_html = Path(sys.argv[2])

    if not csv_path.is_file():
        print(f"CSV file not found: {csv_path}")
        sys.exit(1)

    df = load_data(csv_path)
    metrics = compute_metrics(df)
    chart_b64 = build_chart_png(metrics)
    html = build_html(df, metrics, chart_b64)

    out_html.write_text(html, encoding="utf-8")
    print(f"Report saved to {out_html}")


if __name__ == "__main__":
    main()
