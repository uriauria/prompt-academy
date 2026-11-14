# -*- coding: utf-8 -*-
"""
אקדמיית הפרומפטים - AI Prompt Academy (Gemini, Hebrew)

HOW TO RUN:   python ai_prompt_academy.py
It starts a small local server (nothing to install, no tkinter) and opens the app in your browser.
Press Ctrl+C in this window to stop it.

SET YOUR KEY (nothing is hardcoded in this file). Any ONE of these works:
  1. Environment variable:  GEMINI_API_KEY  (or GOOGLE_API_KEY)
       Windows (PowerShell):  $env:GEMINI_API_KEY="your-key"; python ai_prompt_academy.py
       Mac/Linux:             GEMINI_API_KEY="your-key" python3 ai_prompt_academy.py
  2. A file named  .env  next to this script, containing one line:
       GEMINI_API_KEY=your-key
  3. Leave it unset and paste the key in the box on the page
     (it is then stored only in your browser).

USE FROM OTHER DEVICES (phone, tablet, another computer on the same Wi-Fi):
  python ai_prompt_academy.py --share
  It prints an address like http://192.168.1.23:8765/ - open it on the other device.
  Your key stays on this computer: the page talks to this server, and the server talks to Gemini.
  Anyone on your network who opens the address can use the app (and your key's quota),
  so only do this on a network you trust.

HOSTING ONLINE (anyone with the link, from anywhere):
  Deploy this file to a host such as Render, Railway or Koyeb and set
  this environment variable there:
     GEMINI_API_KEY = your key
  The host sets PORT automatically; the app detects it and listens publicly.
  There is no password: anyone with the link can use the app (and your key's quota).

MODEL FALLBACK:
  If a model returns "high demand" (503), a rate limit (429), a server error (500)
  or "not found" (404), the app automatically tries the next model in the MODELS list
  (edit the list in the JavaScript below if Google renames models).

WHAT'S NEW IN THIS VERSION:
  - Cleaner, card-based design (light + dark mode, mobile friendly)
  - Much more detailed lessons, glossary and a pre-send checklist
  - Random examples: good/bad examples and quiz questions are drawn at random
    from larger pools (new draw every time you press the shuffle buttons)
  - Interactive prompt builder and templates
  - Course alignment: AI literacy, how LLMs work (live next-word demo + random quiz),
    and the Hebrew prompt framework תמה״פ (תפקיד, משימה, הקשר, פורמט)

Keep this file private once your key is inside it.
"""
import sys

if sys.version_info[0] < 3:
    print("This app needs Python 3. Run it with:  python3 ai_prompt_academy.py")
    sys.exit(1)

import http.server
import json
import os
import socket
import threading
import urllib.error
import urllib.request
import webbrowser



def load_key():
    """Read the key from the environment, or from a .env file next to this script."""
    for name in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
        v = os.environ.get(name, "").strip()
        if v:
            return v
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    try:
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                if k.strip() in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
                    v = v.strip().strip('"').strip("'")
                    if v:
                        return v
    except OSError:
        pass
    return ""


KEY = load_key()
HOSTED = bool(os.environ.get("PORT"))  # cloud hosts set PORT

HTML = r'''<!doctype html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>אקדמיית הפרומפטים</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Heebo:wght@400;500;700;800&display=swap" rel="stylesheet">
<style>
:root{
 --bg:#f4f7f9;--p:#ffffff;--p2:#f8fafb;--tx:#14232c;--mu:#5f7380;--ac:#0f766e;--ac2:#14b8a6;--acx:#ffffff;
 --bd:#dde6eb;--ex:#e6f4f2;--ok:#15803d;--bad:#b91c1c;--warn:#b45309;--sh:0 1px 2px rgba(16,40,50,.05),0 8px 24px rgba(16,40,50,.06);
 --hero:linear-gradient(135deg,#0f766e 0%,#0e5f8a 100%);
}
@media(prefers-color-scheme:dark){:root{
 --bg:#0b161c;--p:#13232b;--p2:#101e25;--tx:#e8f0f3;--mu:#92a8b3;--ac:#2dd4bf;--ac2:#5eead4;--acx:#06201d;
 --bd:#25404a;--ex:#143a38;--ok:#4ade80;--bad:#f87171;--warn:#fbbf24;--sh:0 1px 2px rgba(0,0,0,.3),0 8px 24px rgba(0,0,0,.25);
 --hero:linear-gradient(135deg,#0d4f4a 0%,#0c3f5c 100%);
}}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--tx);font:16px/1.65 "Heebo",system-ui,"Segoe UI",Arial,sans-serif}
.wrap{max-width:980px;margin:0 auto;padding:18px 16px 60px}

/* header */
header{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-bottom:14px}
.brand{display:flex;align-items:center;gap:12px}
.logo{width:44px;height:44px;border-radius:12px;background:var(--hero);display:grid;place-items:center;color:#fff;font-size:22px;box-shadow:var(--sh)}
h1{font-size:24px;font-weight:800;margin:0;line-height:1.2}
.sub{font-size:13px;color:var(--mu)}
.hd-r{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
#modelinfo{font-size:12px;color:var(--mu);direction:ltr}

/* tabs */
nav{position:sticky;top:0;z-index:5;display:flex;gap:6px;overflow-x:auto;padding:8px;margin:0 -8px 16px;background:color-mix(in srgb,var(--bg) 88%,transparent);backdrop-filter:blur(8px);border-radius:14px;scrollbar-width:none}
nav::-webkit-scrollbar{display:none}
nav button{flex:1 0 auto;white-space:nowrap;border-radius:10px;padding:9px 14px;background:transparent;border-color:transparent;color:var(--mu)}
nav button:hover{background:var(--p);color:var(--tx)}
nav button.on{background:var(--ac);color:var(--acx);border-color:var(--ac);box-shadow:var(--sh)}

/* basics */
button{font:inherit;font-weight:600;padding:8px 14px;border:1px solid var(--bd);background:var(--p);color:var(--tx);border-radius:10px;cursor:pointer;transition:.15s}
button:hover{border-color:var(--ac)}
button:focus-visible,textarea:focus-visible,select:focus-visible,input:focus-visible,summary:focus-visible{outline:2px solid var(--ac);outline-offset:2px}
button.pri{background:var(--ac);color:var(--acx);border-color:var(--ac)}
button.pri:hover{filter:brightness(1.07)}
button.ghost{background:transparent}
button:disabled{opacity:.5;cursor:default}
button.sm{font-size:13px;padding:5px 11px}
section{display:none}
section.on{display:block;animation:fade .25s ease}
@keyframes fade{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
h2{font-size:19px;font-weight:800;margin:0 0 8px}
h3{font-size:16px;font-weight:700;margin:0 0 6px}
p{margin:6px 0}
ul,ol{padding-inline-start:22px;margin:6px 0}
li{margin:3px 0}
.mu{color:var(--mu)}
.bad{color:var(--bad);font-weight:700}
.good{color:var(--ok);font-weight:700}

/* cards */
.hero{background:var(--hero);color:#fff;border-radius:18px;padding:22px 24px;margin-bottom:16px;box-shadow:var(--sh)}
.hero h2{font-size:22px;margin:0 0 6px;color:#fff}
.hero p{margin:0;opacity:.92}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px;margin-bottom:14px}
.card{background:var(--p);border:1px solid var(--bd);border-radius:16px;padding:18px 20px;box-shadow:var(--sh)}
.card .ic{font-size:22px;display:block;margin-bottom:2px}
.card.full{grid-column:1/-1}
.tag{display:inline-block;font-size:12px;font-weight:700;padding:2px 9px;border-radius:999px;background:var(--ex);color:var(--ac);margin-inline-end:6px}
.steps{counter-reset:s;list-style:none;padding:0}
.steps li{counter-increment:s;position:relative;padding-inline-start:38px;margin:9px 0}
.steps li::before{content:counter(s);position:absolute;inset-inline-start:0;top:0;width:28px;height:28px;border-radius:50%;background:var(--ac);color:var(--acx);display:grid;place-items:center;font-weight:700;font-size:14px}
.ing{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px}
.ing .card{padding:14px 16px;box-shadow:none;background:var(--p2)}
.ing small{display:block;color:var(--mu);margin-top:4px}
.ex{background:var(--ex);border-radius:12px;padding:12px 14px;margin:10px 0;font-size:15px}
.pair{border:1px solid var(--bd);border-radius:12px;overflow:hidden;margin:10px 0;background:var(--p2)}
.pair>div{padding:10px 14px}
.pair>div:first-child{border-bottom:1px dashed var(--bd)}
.bar{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap;margin-bottom:6px}
details{border:1px solid var(--bd);border-radius:12px;background:var(--p2);margin:8px 0;padding:0 14px}
summary{cursor:pointer;font-weight:700;padding:10px 0;list-style:none;display:flex;justify-content:space-between;gap:8px}
summary::after{content:"+";color:var(--ac);font-size:20px;line-height:1}
details[open] summary::after{content:"–"}
details p{padding-bottom:10px;margin:0}
.chk label{display:flex;gap:10px;align-items:flex-start;padding:6px 0;cursor:pointer}
.chk input{margin-top:6px;accent-color:var(--ac);width:17px;height:17px}
.chk label.done span{text-decoration:line-through;color:var(--mu)}

/* inputs */
textarea,select,input[type=text]{width:100%;font:inherit;padding:10px 12px;border:1px solid var(--bd);border-radius:10px;background:var(--p2);color:var(--tx)}
textarea{resize:vertical;min-height:90px}
label.f{display:block;font-weight:700;font-size:14px;margin:10px 0 4px}
.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:10px 0}
.out{white-space:pre-wrap;word-wrap:break-word;background:var(--p2);border:1px solid var(--bd);border-radius:12px;padding:12px 14px;min-height:56px;margin-top:8px}
.out:empty{display:none}
.chips{display:flex;gap:6px;flex-wrap:wrap}
.chips button{border-radius:999px;padding:5px 13px;font-size:14px;background:var(--p2)}
.chips button.on{background:var(--ex);border-color:var(--ac);color:var(--ac)}

/* key box */
.keybox{background:var(--p);border:1px solid var(--ac);border-radius:16px;padding:14px 18px;margin:0 0 14px;box-shadow:var(--sh)}
#keyin{flex:1 1 260px;font:inherit;padding:10px;border:1px solid var(--bd);border-radius:10px;background:var(--p2);color:var(--tx)}
#key{font-size:13px;padding:6px 12px}


/* chat */
#chat{height:48vh;min-height:280px;overflow-y:auto;background:var(--p2);border:1px solid var(--bd);border-radius:14px;padding:12px;margin-bottom:10px}
.m{white-space:pre-wrap;word-wrap:break-word;padding:10px 14px;border-radius:14px;margin:8px 0;max-width:92%}
.m.user{background:var(--ac);color:var(--acx);margin-inline-start:auto;border-end-end-radius:4px}
.m.ai{background:var(--p);border:1px solid var(--bd);border-end-start-radius:4px}
.m.err{background:transparent;border:1px solid var(--bad);color:var(--bad)}
.box{background:var(--ex);border-radius:12px;padding:10px 14px;margin-top:10px;white-space:normal}
.box pre{white-space:pre-wrap;margin:6px 0 10px;font:14px/1.55 ui-monospace,Consolas,monospace}
pre{white-space:pre-wrap;background:var(--ex);padding:8px;border-radius:8px}
code{background:var(--ex);padding:1px 6px;border-radius:5px}
.dots i{display:inline-block;width:7px;height:7px;margin:0 2px;border-radius:50%;background:var(--mu);animation:b 1s infinite}
.dots i:nth-child(2){animation-delay:.15s}.dots i:nth-child(3){animation-delay:.3s}
@keyframes b{0%,80%,100%{opacity:.25}40%{opacity:1}}
#toast{position:fixed;bottom:22px;inset-inline-start:50%;transform:translateX(50%) translateY(20px);background:var(--tx);color:var(--bg);padding:8px 18px;border-radius:999px;opacity:0;pointer-events:none;transition:.25s;font-weight:600;z-index:20}
#toast.on{opacity:1;transform:translateX(50%) translateY(0)}
.qq{border:1px solid var(--bd);border-radius:12px;background:var(--p2);padding:12px 14px;margin:10px 0}
.qh{font-weight:700;margin-bottom:8px}
.qo{display:block;width:100%;text-align:start;margin:6px 0;font-weight:500}
.qo:disabled{opacity:1;cursor:default}
.qo:disabled:not(.ok):not(.no){opacity:.6}
.qo.ok{border-color:var(--ok);background:color-mix(in srgb,var(--ok) 14%,var(--p))}
.qo.no{border-color:var(--bad);background:color-mix(in srgb,var(--bad) 12%,var(--p))}
.qexp{background:var(--ex);border-radius:10px;padding:8px 12px;margin-top:8px;font-size:15px}
.tmf{display:grid;grid-template-columns:auto 1fr;gap:4px 12px;align-items:baseline}
.tmf b{color:var(--ac)}
@media(max-width:560px){.wrap{padding:12px 10px 50px}h1{font-size:20px}.card{padding:14px 15px}}
</style>
</head>
<body>
<div class="wrap">
<header>
 <div class="brand"><div class="logo" aria-hidden="true">✦</div><div><h1>אקדמיית הפרומפטים</h1><div class="sub">לומדים לדבר עם בינה מלאכותית, בלי מילים גדולות</div></div></div>
 <div class="hd-r"><span id="modelinfo"></span><button id="key" type="button"></button></div>
</header>

<div id="keybox" class="keybox">
<b>הוספת מפתח API של Google AI Studio</b>
<div class="row" style="margin:8px 0 0"><input id="keyin" type="password" dir="ltr" placeholder="AQ.…" autocomplete="off" spellcheck="false" aria-label="מפתח API"><button class="pri" id="keysave" type="button">שמירת מפתח</button><button id="keyrm" type="button" hidden>הסרת מפתח</button></div>
<label class="mu" style="font-size:14px"><input type="checkbox" id="keyrem" checked> לזכור במכשיר הזה</label>
<div id="keymsg" style="font-size:14px;margin-top:4px"></div>
</div>

<nav id="nav" role="tablist">
<button role="tab">📘 1. אוריינות AI</button><button role="tab">⚙️ 2. איך LLM עובד</button><button role="tab">✍️ 3. תמה״פ ופרומפטים</button><button role="tab">🧩 4. תבניות ובונה</button><button role="tab">💬 5. מאמן</button>
</nav>

<!-- ===================== 1. LEARN ===================== -->
<section>
<div class="hero"><h2>אוריינות AI והנדסת פרומפטים</h2><p>להבין איך מודלי שפה עובדים, לכתוב פרומפטים בשיטת תמה״פ, ולהשתמש בהם באחריות.</p></div>
<div class="grid">
 <div class="card"><span class="ic">🧭</span><h3>מהי אוריינות AI?</h3>
 <ul><li><b>להבין</b> איך זה עובד ומה המגבלות</li><li><b>להשתמש</b> בפרומפטים ברורים</li><li><b>להעריך</b> דיוק, מקורות והטיות</li><li><b>לנהוג באחריות</b> בפרטיות וביושרה</li></ul></div>

 <div class="card"><span class="ic">⚖️</span><h3>במה AI טוב ובמה פחות</h3>
 <p><b class="good">טוב ב:</b> ניסוח, הסברים, סיכום, רעיונות וקוד.</p>
 <p><b class="bad">פחות טוב ב:</b> עובדות מדויקות, מידע עדכני, ולדעת את המצב שלכם בלי שתספרו.</p></div>

 <div class="card"><span class="ic">🏆</span><h3>כללי זהב</h3>
 <ul><li>בדקו עובדות, מספרים ומקורות.</li><li>אל תדביקו סיסמאות או מידע פרטי.</li><li>התשובה הראשונה היא טיוטה.</li><li>ציינו שימוש ב-AI לפי כללי המוסד.</li></ul></div>

 <div class="card"><span class="ic">🔁</span><h3>תהליך עבודה</h3>
 <ol class="steps">
  <li>החליטו מה אתם רוצים.</li>
  <li>כתבו פרומפט לפי תמה״פ.</li>
  <li>קראו, בקשו שיפורים.</li>
  <li>אמתו מה שחשוב.</li>
 </ol></div>
</div>
</section>

<!-- ===================== LLM ===================== -->
<section>
<div class="hero"><h2>איך מודל שפה (LLM) עובד</h2><p>ארבעה רעיונות שמסבירים את רוב ההתנהגויות של AI.</p></div>
<div class="grid">
 <div class="card"><span class="ic">🔮</span><h3>ניבוי המילה הבאה</h3>
 <p>מודל שפה גדול (LLM) למד מכמות עצומה של טקסט לנבא את ההמשך הסביר ביותר, מילה אחרי מילה. הוא מייצר טקסט שנשמע נכון, ולא שולף עובדות ממאגר.</p></div>

 <div class="card"><span class="ic">🪟</span><h3>טוקנים וחלון הקשר</h3>
 <p>המודל קורא טוקנים (חתיכות קטנות של טקסט). חלון ההקשר הוא כל מה שהוא רואה בשיחה, ומה שמחוצה לו לא קיים בשבילו. בשיחה ארוכה ומסובכת עדיף לפתוח שיחה חדשה.</p></div>

 <div class="card"><span class="ic">🏗️</span><h3>איך מאמנים מודל</h3>
 <p>קודם קריאת טקסט עצום (אימון מקדים), אחר כך תרגול על בקשות ותשובות טובות (כוונון), ולבסוף דירוג של בני אדם (RLHF). בזמן שיחה המודל לא לומד.</p></div>

 <div class="card"><span class="ic">🌫️</span><h3>הזיות</h3>
 <p>המטרה היא טקסט סביר ולא אמת, ולכן המודל עלול להמציא עובדות ומקורות.</p>
 <p><b>מה עושים:</b> מדביקים לו את החומר, מבקשים מקורות ובודקים עובדות חשובות.</p></div>

 <div class="card full"><div class="bar"><h2 style="margin:0">חידון אקראי</h2><button class="pri sm" id="qz_new" type="button">🔀 חידון חדש</button></div>
 <p class="mu" id="qz_sc"></p><div id="qz"></div></div>
</div>
</section>

<!-- ===================== 2. GOOD PROMPTS ===================== -->
<section>
<div class="card" style="margin-bottom:14px">
<h2>תמה״פ: ארבעת יסודות הפרומפט</h2>
<div class="ing">
 <div class="card"><span class="tag">ת</span><b>תפקיד</b><small>מי הבינה המלאכותית אמורה להיות?</small></div>
 <div class="card"><span class="tag">מ</span><b>משימה</b><small>מה בדיוק לעשות?</small></div>
 <div class="card"><span class="tag">ה</span><b>הקשר</b><small>מי אתם, למי זה מיועד, מה המצב?</small></div>
 <div class="card"><span class="tag">פ</span><b>פורמט</b><small>איך התשובה תיראה ובאיזה אורך?</small></div>
</div>
<div class="ex" style="margin-top:14px"><b>דוגמה</b>
<div class="tmf" style="margin-top:6px">
 <b>ת</b><span>אתה מורה פרטי למתמטיקה בחטיבת ביניים.</span>
 <b>מ</b><span>הסבר לי מהו אחוז.</span>
 <b>ה</b><span>אני תלמיד כיתה ז׳ ויש לי מבחן ביום חמישי.</span>
 <b>פ</b><span>שלושה צעדים ודוגמה אחת, עד 120 מילים.</span>
</div></div>
<p class="mu" style="font-size:14px">אפשר להוסיף גם טון ומגבלות.</p>
</div>

<div class="card" style="margin-bottom:14px">
<div class="bar"><h2 style="margin:0">רע מול טוב</h2><button class="pri sm" id="exmore" type="button">🔀 דוגמאות אחרות</button></div>
<div id="exlist"></div>
</div>

<div class="grid">
 <div class="card"><h3>טכניקות</h3>
 <ul><li><b>היו ספציפיים:</b> “עד 100 מילים” ולא “קצר”.</li><li><b>תנו דוגמה (Few-shot).</b></li><li><b>צעד אחר צעד:</b> “חשוב על זה צעד אחר צעד”.</li><li><b>אמרו מה לא רוצים.</b></li><li><b>בקשו שישאל אתכם</b> שאלות לפני שמתחיל.</li></ul></div>
 <div class="card"><h3>טעויות נפוצות</h3>
 <ul><li>כללי מדי (“תשפר את זה”)</li><li>כמה בקשות בפרומפט אחד</li><li>שוכחים להדביק את הטקסט</li><li>מפסיקים אחרי תשובה ראשונה</li></ul></div>
</div>
</section>

<!-- ===================== 3. TEMPLATES ===================== -->
<section>
<div class="card" style="margin-bottom:14px">
<h2>תבניות מוכנות</h2>
<p class="mu">בחרו תבנית, מלאו את מה שבסוגריים המרובעים [ ], ואז העתיקו אותה או שלחו אותה למאמן.</p>
<div id="tpls" class="chips"></div>
<textarea id="tpl" rows="9" dir="auto" style="margin-top:10px"></textarea>
<div class="row"><button id="tcopy">העתקה</button><button class="pri" id="tsend">שליחה למאמן</button></div>
</div>

<div class="card">
<div class="bar"><h2 style="margin:0">בונה פרומפטים</h2><button class="ghost sm" id="bclear" type="button">ניקוי</button></div>
<p class="mu">מלאו רק את מה שרלוונטי. הפרומפט נבנה לפני העיניים.</p>
<div class="grid" style="margin:0">
 <div><label class="f" for="b_role">תפקיד (ת)</label><input type="text" id="b_role" placeholder="למשל: מורה פרטי למתמטיקה"></div>
 <div><label class="f" for="b_task">משימה (מ)</label><input type="text" id="b_task" placeholder="למשל: הסבר לי מהו אחוז"></div>
 <div><label class="f" for="b_ctx">הקשר (ה)</label><input type="text" id="b_ctx" placeholder="למשל: אני בכיתה ז׳ ומתקשה בנושא"></div>
 <div><label class="f" for="b_fmt">פורמט (פ)</label><input type="text" id="b_fmt" placeholder="למשל: 3 צעדים ודוגמה אחת"></div>
 <div><label class="f" for="b_tone">טון (תוסף)</label><input type="text" id="b_tone" placeholder="למשל: ידידותי ופשוט"></div>
 <div><label class="f" for="b_con">מגבלות (תוסף)</label><input type="text" id="b_con" placeholder="למשל: עד 120 מילים, בלי נוסחאות"></div>
</div>
<label class="f" for="b_out">הפרומפט שלכם</label>
<textarea id="b_out" rows="6" dir="auto" readonly></textarea>
<div class="row"><button id="bcopy">העתקה</button><button class="pri" id="bsend">שליחה למאמן לשיפור</button></div>
<p class="mu" style="font-size:14px">ארבעת שדות תמה״פ מלאים? זה פרומפט טוב. הטון והמגבלות הופכים אותו למצוין.</p>
</div>
</section>

<!-- ===================== 5. COACH ===================== -->
<section>
<div class="card">
<div class="bar"><h2 style="margin:0">מאמן פרומפטים</h2>
<div class="row" style="margin:0"><label for="mode" class="mu" style="font-size:14px">מצב</label>
<select id="mode" style="width:auto"><option value="Improve my prompt">שיפור הפרומפט שלי</option><option value="Rate my prompt (score out of 10)">דירוג (ציון מתוך 10)</option><option value="Teach me (explain simply)">לימוד (הסבר פשוט)</option></select>
<button id="newc" class="sm">שיחה חדשה</button></div></div>
<div id="chat" aria-live="polite"></div>
<div class="chips" id="sugg" style="margin-bottom:10px"></div>
<textarea id="inp" rows="3" dir="auto" placeholder="הדביקו פרומפט או תארו מה אתם רוצים. Enter שולח, Shift+Enter מוסיף שורה."></textarea>
<div class="row"><button class="pri" id="send">שליחה</button><button class="ghost sm" id="shuf" type="button">🔀 רעיון אחר</button></div>
</div>
<div class="card" style="margin-top:14px">
<h2>הרצת ניסיון</h2>
<p class="mu">לחצו על “הרצת ניסיון” מתחת לפרומפט משופר כדי לראות מה הבינה המלאכותית עונה איתו.</p>
<div class="out" id="tout" dir="auto"></div>
</div>
</section>
</div>
<div id="toast" role="status"></div>

<script>
// Models are tried in this order. If one is overloaded/unavailable, the next one is used.
const MODELS = ["gemini-flash-latest", "gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-flash-lite-latest"];
let modelIdx = 0;

// When the server has a key, all requests go through it (/gemini/<model>) and the key never reaches the browser.
const USE_PROXY = __USE_PROXY__;
let API_KEY = "";
try{ API_KEY = localStorage.getItem("apa_gemini_key") || sessionStorage.getItem("apa_gemini_key") || "" }catch{}

const $ = s => document.querySelector(s);
const shuffle = a => { a = a.slice(); for(let i = a.length - 1; i > 0; i--){ const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]] } return a };
const sample = (a, n) => shuffle(a).slice(0, n);
let toastT;
function toast(t){ const e = $("#toast"); e.textContent = t; e.classList.add("on"); clearTimeout(toastT); toastT = setTimeout(() => e.classList.remove("on"), 1600) }
function copyText(t){
 const done = () => toast("הועתק ✓");
 if(navigator.clipboard && window.isSecureContext) return navigator.clipboard.writeText(t).then(done, done);
 const a = document.createElement("textarea"); a.value = t; a.style.position = "fixed"; a.style.opacity = "0";
 document.body.appendChild(a); a.select(); try{ document.execCommand("copy") }catch{} a.remove(); done();
 return Promise.resolve();
}
function store(k, v){ try{ localStorage.setItem(k, JSON.stringify(v)) }catch{} }
function load(k, d){ try{ const v = localStorage.getItem(k); return v ? JSON.parse(v) : d }catch{ return d } }

// ---------- Tabs ----------
const secs = document.querySelectorAll("section"), navb = document.querySelectorAll("#nav button");
function show(i){
 secs.forEach((s,j) => s.classList.toggle("on", i === j));
 navb.forEach((b,j) => { b.classList.toggle("on", i === j); b.setAttribute("aria-selected", i === j) });
 window.scrollTo({top: 0});
}
navb.forEach((b,i) => b.onclick = () => show(i)); show(0);

// ---------- API key ----------
let keyOpen = false;
function renderKey(){
 if(USE_PROXY){ $("#key").hidden = true; $("#keybox").hidden = true; return }
 const has = !!API_KEY;
 $("#key").textContent = has ? "מפתח API שמור ✓ (שינוי)" : "הוספת מפתח API";
 $("#key").style.color = has ? "var(--ok)" : "var(--bad)";
 $("#keybox").hidden = has && !keyOpen; $("#keyrm").hidden = !has;
}
function needKey(){ keyOpen = true; renderKey(); $("#keyin").focus() }
function saveKey(){
 const v = $("#keyin").value.trim(), m = $("#keymsg");
 if(!v) return;
 if((v.length < 20 || /\s/.test(v))){ m.style.color = "var(--bad)"; m.textContent = "המפתח נראה קצר מדי או מכיל רווחים. העתיקו אותו שוב במלואו."; return }
 API_KEY = v;
 try{ localStorage.removeItem("apa_gemini_key"); sessionStorage.removeItem("apa_gemini_key");
  ($("#keyrem").checked ? localStorage : sessionStorage).setItem("apa_gemini_key", v) }catch{ m.textContent = "לא ניתן לשמור בדפדפן הזה, ולכן המפתח יישאר עד שתסגרו את הלשונית." }
 $("#keyin").value = ""; m.textContent = ""; keyOpen = false; renderKey();
}
$("#key").onclick = () => { keyOpen = !keyOpen; renderKey(); if(keyOpen) $("#keyin").focus() };
$("#keysave").onclick = saveKey;
$("#keyin").addEventListener("keydown", e => { if(e.key === "Enter") saveKey() });
$("#keyrm").onclick = () => { API_KEY = ""; try{ localStorage.removeItem("apa_gemini_key"); sessionStorage.removeItem("apa_gemini_key") }catch{} $("#keymsg").textContent = "המפתח הוסר."; keyOpen = true; renderKey() };
renderKey();

// ---------- Prompts for the AI ----------
const COACH = `You are a friendly, practical prompt-writing coach inside a learning app. The user shows prompts they wrote or describes what they want from an AI.
- Write ALL replies in Hebrew (unless the user writes in another language). Be short, concrete, encouraging.
- Teach the Hebrew framework תמה״פ: תפקיד (role), משימה (task), הקשר (context), פורמט (format), plus optional tone (טון) and constraints (מגבלות). Name which letters are missing when you review a prompt.
- Good prompts also have: clear goal, audience, length, examples.
- If the request is too vague, ask ONE short clarifying question.
- When you give an improved prompt, end your reply with a block that starts with the exact English line "IMPROVED PROMPT:" followed by the improved prompt (in the user's language). Nothing after it, no quotes around it.
- If the user asks for a change, apply it and give the updated IMPROVED PROMPT block.
- Plain text, **bold** sparingly, "- " bullets. No tables or headers.`;
const MODES = {
 "Improve my prompt":"One line on what's good, a short list of what's missing, then the IMPROVED PROMPT block.",
 "Rate my prompt (score out of 10)":"Start with 'ציון: N/10', then 2 strengths and 2 weaknesses, then the IMPROVED PROMPT block.",
 "Teach me (explain simply)":"Teach the concept simply with one tiny example. Only add an IMPROVED PROMPT block if the user shared a prompt."};
// ---------- One attempt with one specific model ----------
async function streamWith(model, messages, system, onText, max){
 if(!API_KEY && !USE_PROXY){ needKey(); throw new Error("קודם צריך להוסיף מפתח API: הדביקו אותו בתיבה בראש הדף.") }
 const body = {contents: messages.map(m => ({role: m.role === "assistant" ? "model" : "user", parts: [{text: m.content}]})), generationConfig: {maxOutputTokens: max * 4}};
 if(system) body.system_instruction = {parts: [{text: system}]};
 let r;
 try{
  const url = USE_PROXY ? `/gemini/${model}` : `https://generativelanguage.googleapis.com/v1beta/models/${model}:streamGenerateContent?alt=sse`;
  const headers = {"content-type":"application/json"}; if(!USE_PROXY) headers["x-goog-api-key"] = API_KEY;
  r = await fetch(url, {method:"POST", headers, body:JSON.stringify(body)});
 }catch(e){ throw new Error("שגיאת רשת. בדקו את החיבור לאינטרנט.") }
 if(!r.ok){
  let m = String(r.status); try{ m = (await r.json()).error.message }catch{}
  const bad = r.status === 401 || r.status === 403 || /API key/i.test(m);
  if(bad) needKey();
  const err = new Error(bad ? "מפתח API לא תקין. הדביקו מפתח חדש בתיבה שבראש הדף." : r.status === 429 ? "הגעתם למגבלת הבקשות (429). חכו רגע ונסו שוב." : "שגיאת API: " + m);
  err.retry = !bad && (r.status === 503 || r.status === 429 || r.status === 500 || r.status === 404 || /high demand|overloaded|unavailable/i.test(m));
  throw err;
 }
 const rd = r.body.getReader(), dec = new TextDecoder(); let buf = "", full = "";
 for(;;){
  const {done, value} = await rd.read(); if(done) break;
  buf += dec.decode(value, {stream:true}); const lines = buf.split(/\r?\n/); buf = lines.pop();
  for(const l of lines){ if(!l.startsWith("data:")) continue; let e; try{ e = JSON.parse(l.slice(5)) }catch{ continue }
   if(e.error){ const er = new Error("שגיאת API: " + e.error.message); er.retry = !full; throw er }
   if(e.promptFeedback && e.promptFeedback.blockReason) throw new Error("הבקשה נחסמה (" + e.promptFeedback.blockReason + "). נסחו אותה מחדש.");
   const parts = (e.candidates && e.candidates[0] && e.candidates[0].content && e.candidates[0].content.parts) || [];
   const t = parts.filter(p => !p.thought).map(p => p.text || "").join("");
   if(t){ full += t; onText(full) } }
 }
 if(!full){ const er = new Error("לא התקבלה תשובה. נסו שוב."); er.retry = true; throw er }
 return full;
}

// ---------- Tries every model in order until one works ----------
async function stream(messages, system, onText, max = 1500){
 for(let k = 0; k < MODELS.length; k++){
  const idx = (modelIdx + k) % MODELS.length;
  try{
   const out = await streamWith(MODELS[idx], messages, system, onText, max);
   modelIdx = idx;
   $("#modelinfo").textContent = MODELS[idx];
   return out;
  }catch(e){
   if(!e.retry) throw e;
   if(k < MODELS.length - 1) onText("המודל עמוס, מחליף ל־" + MODELS[(idx + 1) % MODELS.length] + "…");
  }
 }
 throw new Error("כל המודלים עמוסים כרגע. נסו שוב בעוד רגע.");
}

function md(s){
 return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/```\w*\n?([\s\S]*?)```/g,"<pre>$1</pre>")
  .replace(/\*\*([^*\n]+)\*\*/g,"<b>$1</b>").replace(/`([^`\n]+)`/g,"<code>$1</code>").replace(/^[-*] /gm,"• ");
}
function enterSend(el, fn){ el.addEventListener("keydown", e => { if(e.key === "Enter" && !e.shiftKey && !e.isComposing){ e.preventDefault(); fn() } }) }

// ---------- Random good/bad examples ----------
const BG = [
 {b:"כתוב על כלבים.", g:"כתוב פסקה ידידותית של 150 מילים לבלוג של חנות חיות על החשיבות של חיברות גורים לפני גיל 16 שבועות. מילים פשוטות, ובסוף טיפ מעשי אחד."},
 {b:"עזור לי עם האימייל.", g:"אני סטודנט ומבקש מהמרצה דחייה של יומיים בהגשת העבודה כי הייתי חולה. כתוב אימייל מנומס עד 100 מילים."},
 {b:"תקן את הקוד שלי.", g:"הפונקציה הזו בפייתון אמורה לחשב ממוצע של רשימה אבל קורסת על רשימה ריקה. קוד: [הדבק]. הסבר את הבאג במשפט אחד ואז הראה את התיקון."},
 {b:"תן לי מתכון.", g:"אני צמחוני ויש לי בבית ביצים, תרד, בצל ופסטה. הצע ארוחת ערב ל־2 אנשים שמוכנת בפחות מ־25 דקות. רשימת מצרכים וארבעה צעדי הכנה."},
 {b:"תכתוב לי קורות חיים.", g:"אתה יועץ קריירה. אני בוגר שנה ראשונה בהנדסת תוכנה ומחפש משרת סטודנט. כתוב סיכום מקצועי של 3 שורות לראש קורות החיים, בלי קלישאות כמו “עובד קשה”."},
 {b:"מה דעתך על הרעיון שלי?", g:"יש לי רעיון לאפליקציה שמזכירה לשתות מים. תן ביקורת כמו משקיע ספקן: 3 חולשות עיקריות ו־2 דרכים לחזק את הרעיון. בלי מחמאות ריקות."},
 {b:"הסבר לי היסטוריה.", g:"הסבר לתלמיד כיתה י׳ את הסיבות למלחמת העולם הראשונה בארבע נקודות, כל אחת במשפט או שניים, ובסוף שאלה אחת לחשיבה."},
 {b:"עשה לי תוכנית אימונים.", g:"אני מתחיל, בן 30, יש לי רק משקולות של 10 ק״ג בבית ו־30 דקות, שלוש פעמים בשבוע. בנה תוכנית ל־4 שבועות בטבלה: יום, תרגילים, סטים וחזרות."},
 {b:"תרגם את זה.", g:"תרגם לאנגלית עסקית מנומסת את ההודעה שלמטה ללקוח שמתעכב בתשלום. שמור על טון ענייני ולא מאיים. תן גרסה אחת קצרה. [הדבק הודעה]"},
 {b:"סכם לי את המאמר.", g:"סכם את המאמר שלמטה בחמש נקודות למנהל עסוק, החשוב ביותר קודם, ובסוף שורה תחתונה אחת. אל תוסיף מידע שלא כתוב במאמר. [הדבק מאמר]"},
 {b:"תן לי רעיון למתנה.", g:"אני מחפש מתנה לאחות בת 28 שאוהבת קפה וטיולים, בתקציב עד 150 ש״ח. הצע 5 רעיונות, כל אחד עם משפט שמסביר למה הוא מתאים."},
 {b:"שפר את הנאום.", g:"הנאום שלמטה לחתונה של חבר. קצר אותו ל־2 דקות הקראה, שמור על הבדיחה על הטיול לאילת, והוסף סיום מרגש. טון חם עם קצת הומור. [הדבק נאום]"}
];
const exBox = $("#exlist");
function renderEx(){
 exBox.innerHTML = "";
 sample(BG, 2).forEach(x => {
  const d = document.createElement("div"); d.className = "pair";
  d.innerHTML = '<div><span class="bad">רע:</span> <span class="b"></span></div><div><span class="good">טוב:</span> <span class="g"></span></div>';
  d.querySelector(".b").textContent = x.b; d.querySelector(".g").textContent = x.g;
  exBox.appendChild(d);
 });
}
$("#exmore").onclick = renderEx; renderEx();

// ---------- Templates ----------
const TPL = {
 "כתיבת אימייל":"אתה עוזר כתיבה מקצועי.\nמשימה: כתוב אימייל אל [נמען] בנושא [נושא].\nהקשר: [מי אני והמצב]\nטון: [מנומס / ידידותי / רשמי]\nמגבלות: עד [100] מילים, שורת נושא ברורה, ובקשה ברורה במשפט האחרון.",
 "הסבר פשוט":"הסבר את [נושא] למי ש[רמה, למשל: מתחיל לגמרי].\nהשתמש בדימוי אחד מהחיים, עד [150] מילים, בלי ז׳רגון.\nבסוף שאל אותי שאלה אחת כדי לבדוק שהבנתי.",
 "סיכום טקסט":"סכם את הטקסט שלמטה עבור [קהל יעד].\nפורמט: [5] נקודות, החשוב ביותר קודם, ואז משפט אחד “שורה תחתונה”.\nהתמקד ב[מה חשוב]. אל תוסיף דבר שלא כתוב בטקסט.\n\nטקסט:\n[הדבק טקסט]",
 "תיקון קוד":"אתה מפתח [שפה] בכיר.\nהקוד שלי אמור [התנהגות רצויה] אבל במקום זה [מה קורה / הודעת שגיאה].\nקוד:\n[הדבק קוד]\n\nהסבר את הסיבה ב־1-2 משפטים, הראה את הקוד המתוקן, ורשום בעיות נוספות שאתה מזהה.",
 "תחקר אותי":"אני לומד [נושא] ברמה של [רמה].\nתחקר אותי עם [5] שאלות, אחת בכל פעם. חכה לתשובה שלי לפני השאלה הבאה.\nאחרי כל תשובה אמור אם צדקתי והסבר בקצרה. בסוף הצג את הציון שלי ומה כדאי לחזור עליו."};
const tb = $("#tpls");
Object.keys(TPL).forEach((k,i) => { const b = document.createElement("button"); b.textContent = k;
 b.onclick = () => { [...tb.children].forEach(x => x.classList.remove("on")); b.classList.add("on"); $("#tpl").value = TPL[k] };
 tb.appendChild(b); if(i === 0) b.click(); });
$("#tcopy").onclick = () => copyText($("#tpl").value);
$("#tsend").onclick = () => sendToCoach("עזור לי למלא ולשפר את תבנית הפרומפט הזו:\n\n" + $("#tpl").value);
function sendToCoach(t){ $("#inp").value = t; show(4); $("#inp").focus() }

// ---------- Prompt builder ----------
const BF = [["b_role","אתה "],["b_task","משימה: "],["b_ctx","הקשר: "],["b_fmt","פורמט: "],["b_tone","טון: "],["b_con","מגבלות: "]];
function build(){
 const lines = BF.map(([id, pre]) => { const v = $("#" + id).value.trim(); return v ? pre + v + (id === "b_role" ? "." : "") : "" }).filter(Boolean);
 $("#b_out").value = lines.join("\n");
}
BF.forEach(([id]) => $("#" + id).addEventListener("input", build));
$("#bclear").onclick = () => { BF.forEach(([id]) => $("#" + id).value = ""); build() };
$("#bcopy").onclick = () => { if($("#b_out").value) copyText($("#b_out").value); else toast("מלאו לפחות שדה אחד") };
$("#bsend").onclick = () => { if($("#b_out").value) sendToCoach("שפר לי את הפרומפט הזה:\n\n" + $("#b_out").value); else toast("מלאו לפחות שדה אחד") };

// ---------- LLM quiz (5 random questions out of the pool) ----------
const QZ = [
 {q:"מה עושה מודל שפה גדול (LLM) בבסיסו?", o:["מנבא את ההמשך הסביר של הטקסט","שולף עובדות ממאגר מאומת","מבין כוונות כמו אדם","מבצע חישובים מדויקים תמיד"], a:0, e:"המודל לומד דפוסים בטקסט ומייצר המשך סביר, ולכן הוא יכול להישמע בטוח גם כשהוא טועה."},
 {q:"מהו טוקן?", o:["חתיכת טקסט קטנה, לעיתים חצי מילה, שהמודל קורא וכותב","סיסמת גישה לשירות","תשובה נכונה אחת","משפט שלם"], a:0, e:"המודל עובד בטוקנים. לכן יש תקרה לאורך הקלט והפלט."},
 {q:"מהי “הזיה” (Hallucination)?", o:["מידע שגוי שנשמע בטוח ואמין","תקלת חיבור לאינטרנט","תשובה ארוכה מדי","סירוב לענות"], a:0, e:"המודל מייצר טקסט סביר, ולכן עלול להמציא עובדות, שמות ומקורות. בודקים מול מקור אמין."},
 {q:"מה משפיעה טמפרטורה גבוהה על התשובות?", o:["הן מגוונות ופחות צפויות","הן תמיד זהות","המודל מדייק יותר בעובדות","המודל נהיה מהיר יותר"], a:0, e:"טמפרטורה גבוהה נותנת סיכוי גבוה יותר להמשכים פחות סבירים, וזה טוב ליצירתיות ופחות לעובדות וקוד."},
 {q:"מהו חלון ההקשר?", o:["כמות הטקסט שהמודל רואה בבת אחת בשיחה","מספר המשתמשים בשירות","גודל המסך באפליקציה","זמן התגובה של המודל"], a:0, e:"מה שמחוץ לחלון לא קיים בשביל המודל. בשיחה ארוכה פרטים מוקדמים עלולים להתפספס."},
 {q:"למה מודל עלול לטעות בנוגע לאירוע חדש?", o:["הידע שלו נעצר בתאריך מסוים, אלא אם הוא מחובר לחיפוש","הוא מתעצל","הוא לא מכיר עברית","המשתמש תמיד שואל לא נכון"], a:0, e:"האימון מסתיים בנקודת זמן מסוימת. לנושאים עדכניים צריך חיפוש או להדביק את החומר."},
 {q:"מה מייצגת האות ת בתמה״פ?", o:["תפקיד","תוכן","תשובה","תאריך"], a:0, e:"ת = תפקיד: מי הבינה המלאכותית אמורה להיות, למשל מורה פרטי או עורך לשוני."},
 {q:"מה מייצגת האות מ בתמה״פ?", o:["משימה","מקור","מגבלה","מודל"], a:0, e:"מ = משימה: הפעולה הברורה שרוצים שהמודל יעשה."},
 {q:"מה מייצגת האות ה בתמה״פ?", o:["הקשר","הוראה","המלצה","הסבר"], a:0, e:"ה = הקשר: הרקע שהמודל לא יכול לנחש, כמו מי אתם, למי זה מיועד ומה המצב."},
 {q:"מה מייצגת האות פ בתמה״פ?", o:["פורמט","פירוט","פתרון","פעולה"], a:0, e:"פ = פורמט: איך התשובה תיראה, למשל טבלה, 3 נקודות או עד 100 מילים."},
 {q:"איזה פרומפט טוב יותר?", o:["אני מנהל חנות פרחים קטנה. כתוב פוסט של 60 מילים לאינסטגרם על מבצע ליום האם, בטון חם ועם אימוג׳י אחד.","כתוב פוסט.","תכתוב משהו יפה.","עזור לי."], a:0, e:"יש בו הקשר, משימה, אורך, טון ומגבלה. פרומפט כללי נותן תשובה כללית."},
 {q:"מה מטרת השלב של למידה ממשוב אנושי (RLHF)?", o:["לכוון את המודל לתשובות מועילות, מנומסות ובטוחות","למחוק את הידע הקודם","להגדיל את חלון ההקשר","לתרגם את המודל לשפות אחרות"], a:0, e:"בני אדם מדרגים תשובות והמודל מתכוונן לאלה שנחשבות טובות יותר."},
 {q:"מה כדאי לעשות כששיחה ארוכה הסתבכה?", o:["לפתוח שיחה חדשה ולהדביק רק את הפרטים החשובים","להוסיף עוד הוראות סותרות","להמשיך עד שיצליח","לכתוב באותיות גדולות"], a:0, e:"שיחה חדשה מנקה רעש ומחזירה את חלון ההקשר למה שחשוב."},
 {q:"מתי חשוב במיוחד לבדוק תשובה של AI מול מקור אמין?", o:["כשמדובר בעובדות, מספרים, רפואה, משפט וכסף","לעולם לא צריך לבדוק","רק כשהתשובה קצרה","רק בעברית"], a:0, e:"טעויות בתחומים האלה עלולות לעלות ביוקר, והמודל לא מחליף איש מקצוע."},
 {q:"מה מקור עיקרי להטיות של מודלי שפה?", o:["הטקסטים שעליהם אומנו, שמשקפים הטיות של בני אדם","תקלת חשמל","גודל המקלדת","מהירות האינטרנט"], a:0, e:"המודל משקף דפוסים מהנתונים, כולל סטריאוטיפים. כדאי לבקש נקודות מבט שונות ולבדוק מה חסר."},
 {q:"איזו טכניקה עוזרת בבעיות מורכבות?", o:["לבקש מהמודל לחשוב צעד אחר צעד","לבקש תשובה במילה אחת","להסתיר את ההקשר","לשאול בלי פרטים"], a:0, e:"פירוק לצעדים (Chain-of-thought) מקטין טעויות בלוגיקה ובחישובים."},
 {q:"מהו Few-shot prompting?", o:["מתן אחת עד שלוש דוגמאות בפרומפט להראות את התוצאה הרצויה","פרומפט קצר מאוד","שאלה אחת בלבד","מחיקת היסטוריית השיחה"], a:0, e:"דוגמאות הן דרך חזקה להעביר סגנון ופורמט בלי להסביר אותם בהרחבה."},
 {q:"מה לא כדאי להדביק לשירות AI חיצוני?", o:["סיסמאות, מפתחות API ומידע אישי של אחרים","שאלה כללית על היסטוריה","נושא ללימוד","מתכון"], a:0, e:"מה שנשלח לשירות חיצוני יוצא מהמחשב שלכם. מסירים מידע רגיש לפני ההדבקה."}
];
function qzRender(){
 const box = $("#qz"); box.innerHTML = "";
 const qs = sample(QZ, 5); let answered = 0, right = 0;
 const upd = () => { $("#qz_sc").textContent = answered === qs.length
  ? "סיימתם: " + right + "/" + qs.length + (right === qs.length ? " 🎉" : right >= 3 ? " 👏" : ". כדאי לחזור על החומר ולנסות חידון חדש.")
  : "ענו על " + answered + "/" + qs.length + " · נכון: " + right };
 qs.forEach((x, n) => {
  const card = document.createElement("div"); card.className = "qq";
  const h = document.createElement("div"); h.className = "qh"; h.textContent = (n + 1) + ". " + x.q; card.appendChild(h);
  const exp = document.createElement("div"); exp.className = "qexp"; exp.hidden = true; let done = false;
  shuffle(x.o.map((t, i) => [t, i === x.a])).forEach(([t, ok]) => {
   const b = document.createElement("button"); b.className = "qo"; b.textContent = t; if(ok) b.dataset.ok = "1";
   b.onclick = () => {
    if(done) return; done = true; answered++; if(ok) right++;
    b.classList.add(ok ? "ok" : "no");
    card.querySelectorAll(".qo").forEach(z => { z.disabled = true; if(z.dataset.ok) z.classList.add("ok") });
    exp.hidden = false; exp.textContent = (ok ? "נכון! " : "לא בדיוק. ") + x.e; upd();
   };
   card.appendChild(b);
  });
  card.appendChild(exp); box.appendChild(card);
 });
 upd();
}
$("#qz_new").onclick = qzRender; qzRender();

// ---------- Coach ----------
const SUGG = [
 "כתוב לי קורות חיים.", "תן לי רעיון למתנה לחבר.", "הסבר לי איך עובדת בורסה.", "עזור לי לכתוב הודעה למנהל שלי.",
 "תכנן לי שבוע ארוחות.", "תקן את הקוד שלי.", "אני רוצה ללמוד גיטרה.", "כתוב פוסט לאינסטגרם על העסק שלי.",
 "סכם לי את הספר שקראתי.", "איך מתכוננים למבחן בשבוע?", "תן לי רעיון לפרויקט גמר.", "תרגם לי את המכתב."];
const chat = $("#chat"), hist = []; let busy = false;
function renderSugg(){
 const box = $("#sugg"); box.innerHTML = "";
 sample(SUGG, 4).forEach(s => { const b = document.createElement("button"); b.textContent = s; b.onclick = () => { $("#inp").value = s; $("#inp").focus() }; box.appendChild(b) });
}
$("#shuf").onclick = renderSugg;
function add(cls, text){ const d = document.createElement("div"); d.className = "m " + cls; d.dir = "auto"; d.textContent = text; chat.appendChild(d); chat.scrollTop = chat.scrollHeight; return d }
function greet(){ add("ai","היי! הדביקו פרומפט שכתבתם, או ספרו לי מה אתם רוצים שבינה מלאכותית תעשה, ואעזור לכם לשפר אותו. אפשר גם ללחוץ על אחד הרעיונות שמתחת לחלון. אחר כך אפשר לבקש שינויים (קצר יותר, רשמי יותר, להוסיף דוגמאות…).") }
function finish(d, full){
 const m = full.match(/IMPROVED PROMPT:?\s*([\s\S]*)$/i); if(!m){ d.innerHTML = md(full); return }
 const prompt = m[1].trim().replace(/^["“]|["”]$/g, "");
 d.innerHTML = md(full.slice(0, m.index)) + '<div class="box"><b>הפרומפט המשופר</b><pre dir="auto"></pre><button class="cp sm">העתקה</button> <button class="tr pri sm">הרצת ניסיון ◀</button></div>';
 d.querySelector("pre").textContent = prompt;
 d.querySelector(".cp").onclick = () => copyText(prompt);
 d.querySelector(".tr").onclick = async e => { e.target.disabled = true; $("#tout").textContent = "מריץ…";
  try{ await stream([{role:"user",content:prompt}], null, x => $("#tout").innerHTML = md(x), 1000) }catch(err){ $("#tout").textContent = err.message }
  e.target.disabled = false; $("#tout").scrollIntoView({behavior:"smooth",block:"nearest"}) };
}
async function send(){
 const t = $("#inp").value.trim(); if(!t || busy) return;
 busy = true; $("#send").disabled = true; $("#inp").value = ""; add("user", t); hist.push({role:"user",content:t});
 const d = add("ai", ""); d.innerHTML = '<span class="dots"><i></i><i></i><i></i></span>';
 try{
  const mode = $("#mode").value, full = await stream(hist, COACH + "\nCURRENT MODE: " + mode + ". " + MODES[mode], x => { d.innerHTML = md(x); chat.scrollTop = chat.scrollHeight });
  hist.push({role:"assistant",content:full}); finish(d, full);
 }catch(e){ hist.pop(); d.className = "m err"; d.textContent = e.message }
 busy = false; $("#send").disabled = false; chat.scrollTop = chat.scrollHeight;
}
$("#send").onclick = send; enterSend($("#inp"), send);
$("#newc").onclick = () => { if(busy) return; hist.length = 0; chat.innerHTML = ""; $("#tout").textContent = ""; greet(); renderSugg() };
greet(); renderSugg();
</script>
</body>
</html>
'''

PAGE = HTML.replace("__USE_PROXY__", "true" if KEY else "false")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/%s:streamGenerateContent?alt=sse"


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/healthz":
            self.send_response(200)
            self.send_header("Content-Length", "2")
            self.end_headers()
            self.wfile.write(b"ok")
            return
        if self.path.split("?")[0] in ("/", "/index.html"):
            body = PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_error(404)

    def do_POST(self):
        # Proxy: /gemini/<model>  ->  Gemini streaming API, using the key stored on the server.
        model = self.path.split("?")[0][len("/gemini/"):] if self.path.startswith("/gemini/") else ""
        if not KEY or not model or not all(c.isalnum() or c in "-._" for c in model):
            self.send_error(404)
            return
        data = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        req = urllib.request.Request(
            GEMINI_URL % model, data=data, method="POST",
            headers={"Content-Type": "application/json", "x-goog-api-key": KEY})
        try:
            resp = urllib.request.urlopen(req, timeout=120)
        except urllib.error.HTTPError as e:
            body = e.read()
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        except Exception as e:
            body = json.dumps({"error": {"message": "Server could not reach Gemini: %s" % e}}).encode("utf-8")
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()  # no Content-Length: the connection closing ends the stream
        try:
            while True:
                chunk = resp.readline()
                if not chunk:
                    break
                self.wfile.write(chunk)
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            resp.close()

    def log_message(self, *args):
        pass  # keep the console quiet


def lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))  # no data is sent; this just picks the right network interface
        return s.getsockname()[0]
    except OSError:
        return "YOUR-COMPUTER-IP"
    finally:
        s.close()


def main():
    if HOSTED:
        port = int(os.environ["PORT"])
        server = http.server.ThreadingHTTPServer(("0.0.0.0", port), Handler)
        print("AI Prompt Academy is live on port %d" % port)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
        return

    share = "--share" in sys.argv
    host = "0.0.0.0" if share else "127.0.0.1"
    server = None
    for port in range(8765, 8785):  # first free port
        try:
            server = http.server.ThreadingHTTPServer((host, port), Handler)
            break
        except OSError:
            continue
    if server is None:
        raise SystemExit("Could not find a free port (8765-8784).")

    url = "http://localhost:%d/" % port
    print("AI Prompt Academy is running at " + url)
    if share:
        print("On other devices (same Wi-Fi) open:  http://%s:%d/" % (lan_ip(), port))
        print("Only do this on a network you trust. If it does not load, allow Python through your firewall.")
    else:
        print("Only this computer can open it. To use it from other devices, run with:  --share")
    print("API key: " + ("set (kept on the server)" if KEY else "NOT set (paste it in the box on the page, or use GEMINI_API_KEY / a .env file)"))
    print("Press Ctrl+C to stop.")
    threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
