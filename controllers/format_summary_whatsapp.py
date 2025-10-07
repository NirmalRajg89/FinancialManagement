import re

def format_summary_for_whatsapp(summary: str) -> str:
    """
    Converts raw text with '|' tables and section headers into 
    a readable WhatsApp-friendly summary with markdown and emojis.
    """
    # Clean up excessive pipes, dashes, and spacing
    text = re.sub(r'\|+', '|', summary)
    text = re.sub(r'-{2,}', '', text)
    text = re.sub(r'\s{2,}', ' ', text).strip()

    # Replace major sections with emojis + bold titles
    replacements = {
        "Investment Summary Overview": "📊 *Investment Summary Overview*",
        "Investment Options Analysis": "💡 *Investment Options*",
        "Mutual Funds (3 samples)": "📈 *Mutual Fund Samples*",
        "Equity Investments (3 samples)": "💹 *Equity Investments*",
        "Commodities & Alternatives": "🏠 *Commodities & Alternatives*",
        "Goal Feasibility": "✅ *Goal Feasibility*",
        "Long-term Plan Recommendations": "💼 *Recommendations*",
        "Investment Diversification": "📊 *Investment Diversification*",
        "Guaranteed Rate Services": "🔗 *Refinance Options*",
    }

    for old, new in replacements.items():
        text = text.replace(old, f"\n\n{new}\n")

    # Convert table-like sections into bullet-style lines
    text = re.sub(r"\|\s*([A-Za-z].*?)\s*\|", r"\n• \1", text)

    # Clean remaining table clutter
    text = text.replace("|", "").replace("\n\n\n", "\n\n")

    # Optional: compact spacing for WhatsApp
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Add friendly greeting and closing
    formatted = (
        "👋 *Hello!*\n\n"
        + text.strip()
        + "\n\nThanks,\n*Your Investment Assistant 💰*"
    )

    return formatted
