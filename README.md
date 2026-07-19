# Weather Chat MCP

עוזר צ'אט למזג אוויר, מבוסס על **MCP (Model Context Protocol)** ומודל **Gemini**. המערכת מריצה שני שרתי MCP נפרדים — אחד למזג אוויר בארה"ב (דרך ה-API הרשמי של ה-NWS) ואחד לישראל (דרך אוטומציית דפדפן על אתר `weather2day.co.il`) — ומאפשרת למודל השפה להחליט מתי ואיזה כלי לקרוא כדי לענות על שאלת המשתמש.

## מטרת הפרויקט

- להדגים ארכיטקטורת **host + multiple MCP servers**: `host.py` מתחבר לשני שרתי MCP דרך STDIO, אוסף מהם את רשימת הכלים הזמינים, ומעביר אותה למודל Gemini.
- Gemini בוחר האם לענות ישירות או לבקש קריאה לכלי (בפורמט JSON), ה-host מריץ את הכלי ומחזיר את התוצאה חזרה למודל עד שמתקבלת תשובה סופית.
- שני "עולמות" של מזג אוויר מיוצגים על ידי שני שרתים נפרדים:
  - `weather_USA.py` — ניגש ל-API הרשמי של שירות מזג האוויר האמריקאי (NWS).
  - `weather_Israel.py` — מפעיל דפדפן אמיתי (Playwright) ומבצע חיפוש עיר באתר תחזית ישראלי.

## ארכיטקטורה

```
host.py  (Gemini + לולאת שיחה)
   │
   ├── client.py → MCPClient  ──STDIO──► weather_USA.py     (שרת MCP - USA)
   │
   └── client.py → MCPClient  ──STDIO──► weather_Israel.py  (שרת MCP - ישראל)
```

## כלים זמינים (Tools)

| שרת | כלי | תיאור |
|---|---|---|
| `weather_USA` | `get_alerts_in_USA(state)` | התראות מזג אוויר פעילות למדינה אמריקאית לפי קוד דו-אותיות (למשל `CA`, `NY`) |
| `weather_USA` | `get_forecast_in_USA(latitude, longitude)` | תחזית ל-5 התקופות הקרובות לפי קואורדינטות |
| `weather_Israel` | `open_weather_forecast_israel()` | פתיחת אתר התחזית הישראלי בדפדפן |
| `weather_Israel` | `enter_weather_forecast_city_israel(city)` | הקלדת שם עיר בשדה החיפוש באתר |
| `weather_Israel` | `select_weather_forecast_city_israel()` | בחירת הצעת ההשלמה האוטומטית הראשונה עבור העיר |
| `weather_Israel` | `read_weather_forecast_content_israel()` | קריאת התוכן הטקסטואלי הגלוי בעמוד התחזית הנוכחי, כדי שהמודל יוכל לענות ישירות לפי תוכן העמוד |

> לב לב: הכלים לישראל מבצעים אוטומציית דפדפן שלב-אחר-שלב (פתיחה → הקלדת עיר → בחירה → קריאת תוכן) — Gemini קורא להם ברצף הנכון כדי להגיע לעמוד התחזית של העיר המבוקשת ולחלץ ממנו את התשובה בפועל.

## דרישות

- Python 3.13+
- מנהל חבילות [`uv`](https://docs.astral.sh/uv/) (קיים `uv.lock` בפרויקט) — או `pip` באופן ידני
- מפתח API תקף ל-Gemini

## התקנה

עם `uv` (מומלץ, ישתמש ב-`uv.lock` הקיים):

```powershell
uv sync
uv run playwright install
```

או עם `pip`:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install google-genai mcp python-dotenv playwright openai netfree-unstrict-ssl
python -m playwright install
```

### הגדרת משתני סביבה

צרו קובץ `.env` בשורש הפרויקט (הקובץ מוחרג מ-git ב-`.gitignore`):

```env
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

## איך להריץ

```powershell
uv run host.py
```

או אם השתמשתם ב-`venv` רגיל:

```powershell
.\.venv\Scripts\python.exe host.py
```

לאחר ההרצה, `host.py` מתחבר אוטומטית לשני שרתי ה-MCP ופותח שיחה אינטראקטיבית בטרמינל. הקלידו שאלה בשורת `Query:`, או `quit` ליציאה.

## דוגמאות לשאלות שה-Agent יודע לענות עליהן

**מזג אוויר בארה"ב:**
- `What are the active weather alerts in California?`
- `Are there any severe weather warnings in NY right now?`
- `What is the weather forecast for San Francisco for the next few days?`
- `Give me the forecast for New York City.`

**מזג אוויר בישראל (אוטומציית דפדפן):**
- `מה מזג האוויר בתל אביב היום?`
- `תן לי תחזית לירושלים ותגיד לי אם צפוי גשם מחר`
- `Open the Israel weather site and tell me the forecast for Haifa.`

> עבור שאלות ארה"ב, המודל עצמו מזהה את הקואורדינטות של העיר ומעביר אותן לכלי `get_forecast_in_USA`. עבור שאלות ישראל, הדפדפן נפתח בפועל (`headless=False`) כך שניתן לצפות בתהליך החיפוש בזמן אמת.

## הערות מיוחדות

- כתובת ה-API הרשמית של NWS תומכת רק במיקומים בתוך ארה"ב.
- אם תקבלו שגיאת `429 RESOURCE_EXHAUSTED` ממודל Gemini — סימן שמכסת הבקשות למודל הנבחר נגמרה.
- דפדפן Playwright לישראל נפתח בחלון גלוי (לא headless) כדי לאפשר מעקב אחר תהליך החיפוש; חלון הדפדפן נשאר פתוח בין קריאות עוקבות עד לסיום התהליך.

## מבנה קבצים ראשי

- `host.py` — ה-host שמריץ את לולאת השיחה עם Gemini ומתאם בין שני שרתי ה-MCP
- `client.py` — מחלקת `MCPClient` לחיבור STDIO אל שרת MCP בודד
- `weather_USA.py` — שרת MCP למזג אוויר בארה"ב
- `weather_Israel.py` — שרת MCP למזג אוויר בישראל, מבוסס Playwright
- `.env` — משתני סביבה (לא נשמר ב-git)
- `pyproject.toml` / `uv.lock` — הגדרות התלויות של הפרויקט
