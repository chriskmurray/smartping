from datetime import datetime, timedelta
from flask import Flask, request, jsonify
import sqlite3, time, threading
from ping3 import ping

app = Flask(__name__)
DB = "db/pings.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS hosts (
                   id INTEGER PRIMARY KEY,
                   ip TEXT UNIQUE
                )""")
    c.execute("""CREATE TABLE IF NOT EXISTS results (
                   id INTEGER PRIMARY KEY,
                   host_id INTEGER,
                   timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                   latency REAL,
                   success INTEGER,
                   FOREIGN KEY(host_id) REFERENCES hosts(id)
                )""")
    conn.commit()
    conn.close()

def worker():
    while True:
        print("🔄 Worker cycle starting...")
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("SELECT id, ip FROM hosts")
        hosts = c.fetchall()

        for host_id, ip in hosts:
            print(f"   Pinging host {ip} (id {host_id})...")
            latencies = []
            for i in range(20):
                result = ping(ip, timeout=2)
                if result is not None:
                    ms = result * 1000   # ✅ convert to ms here
                    latencies.append(ms)
                    print(f"      Ping {i+1}/20 → {ms:.2f} ms")
                else:
                    print(f"      Ping {i+1}/20 → timeout")
                time.sleep(1)

            if latencies:
                latencies.sort()
                median_latency = latencies[len(latencies) // 2]
                success = 1
                print(f"   ✅ Median latency for {ip}: {median_latency:.2f} ms")
            else:
                median_latency = None
                success = 0
                print(f"   ❌ All pings failed for {ip}")

            c.execute(
                "INSERT INTO results (host_id, latency, success) VALUES (?, ?, ?)",
                (host_id, median_latency, success),
            )

        conn.commit()
        conn.close()
        print("✅ Worker cycle complete. Sleeping 5 minutes...\n")
        time.sleep(300)

@app.route("/hosts", methods=["GET", "POST", "DELETE"])
def hosts():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    if request.method == "POST":
        ip = request.json["ip"]
        c.execute("INSERT OR IGNORE INTO hosts (ip) VALUES (?)", (ip,))
        conn.commit()
    elif request.method == "DELETE":
        host_id = request.json.get("id")
        if host_id:
            c.execute("DELETE FROM hosts WHERE id=?", (host_id,))
            c.execute("DELETE FROM results WHERE host_id=?", (host_id,))
            conn.commit()
    c.execute("SELECT * FROM hosts")
    data = c.fetchall()
    conn.close()
    return jsonify(data)

@app.route("/results/<int:host_id>")
def results(host_id):
    time_range = request.args.get("range")
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    query = "SELECT timestamp, latency, success FROM results WHERE host_id=?"
    params = [host_id]

    if time_range:
        now = datetime.utcnow()
        if time_range == "1h":
            cutoff = now - timedelta(hours=1)
        elif time_range == "24h":
            cutoff = now - timedelta(hours=24)
        elif time_range == "7d":
            cutoff = now - timedelta(days=7)
        else:
            cutoff = None

        if cutoff:
            query += " AND timestamp >= ?"
            params.append(cutoff)

    query += " ORDER BY timestamp DESC LIMIT 1000"
    c.execute(query, params)
    data = c.fetchall()
    conn.close()

    # ✅ wrap in dict so frontend gets `results` + stats
    latencies = [d[1] for d in data if d[1] is not None]
    avg_latency = sum(latencies) / len(latencies) if latencies else None
    success_rate = sum(d[2] for d in data) / len(data) if data else None

    return jsonify({
        "results": data,
        "avg_latency": avg_latency,
        "success_rate": success_rate
    })

if __name__ == "__main__":
    init_db()
    threading.Thread(target=worker, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)
