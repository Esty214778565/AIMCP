# Weather Chat MCP

A simple MCP-based weather assistant that can answer USA weather questions via a tool-backed API and Israeli weather questions via browser automation on `https://www.weather2day.co.il/forecast`.

## מה הפרויקט עושה

- מריץ מערכת MCP עם שני כלי Python:
  - `weather_USA.py` – כלי מזג אוויר ל־USA שניגש ל־API רשמי
  - `weather_Israel.py` – כלי מזג אוויר לישראל שמפעיל דפדפן באמצעות Playwright כדי לחפש עיר ולקרוא תחזית
- המארח (`host.py`) משלב את שני הכלים ומאפשר למודל Gemini לקרוא להם דרך כלי חיצוני
- התקשורת נעשית דרך STDIO בין ה־host ל־MCP servers

## דרישות

- Python 3.13+ (הפרויקט מוגדר ב־`pyproject.toml`)
- תלותיות:
  - `google-genai`
  - `mcp`
  - `python-dotenv`
  - `playwright`
  - `openai`
  - `netfree-unstrict-ssl`

## התקנה

1. צרו וירטואלenv ותקינו תלותיות:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

> אם אין לכם `requirements.txt`, ניתן להתקין את התלויות ישירות מ־`pyproject.toml` או ליצור את הקובץ בעצמכם.

2. התקינו Playwright בדפדפן:

```powershell
.\.venv\Scripts\python.exe -m playwright install
```

3. הגדרתם את משתני הסביבה ב־`.env`:

```env
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

## איך להריץ

ב־PowerShell:

```powershell
.\.venv\Scripts\python.exe host.py
```

אם ברצונכם להריץ את כל כלי ה־MCP מתוך `weather_Israel.py` או `weather_USA.py` ישירות, ודאו שיש את `__main__` שלהם או שמפעילים אותם דרך `host.py`.

## שימוש

לאחר הרצת `host.py`, תתבקשו להזין שאילתה.

דוגמאות לשאלות:

- `What is the weather in New York today?`
- `תן תחזית לירושלים היום ונראה לי אם יש סופה מחר.`
- `Open the Israel weather site and select Tel Aviv.`
- `What is the current USA weather forecast for San Francisco?`

## הערות מיוחדות

- השימוש במודל Gemini יכול לדרוש חשבון ו־API key תקין.
- אם תקבלו שגיאת `429 RESOURCE_EXHAUSTED`, זה אומר שגמרתם קווטת בקשות במודל הנבחר.
- קובץ זה נועד להסביר את מטרת הפרויקט, את אופן ההפעלה, ואת הפקודות הנפוצות.

## מבנה קבצים ראשי

- `host.py` – מארח ה־MCP שמנהל את כל הכלים והבקשות
- `client.py` – חיבור ל־MCP server דרך STDIO
- `weather_USA.py` – כלי מזג אוויר ל־USA
- `weather_Israel.py` – כלי מזג אוויר לישראל עם Playwright
- `.env` – הגדרות סביבה ל־Gemini API
- `pyproject.toml` – התלויות והגדרות הפרויקט
