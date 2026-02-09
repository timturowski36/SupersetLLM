from flask import Flask, request, jsonify, send_from_directory
import requests
import re
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__, static_folder="static")

OLLAMA_URL      = os.environ.get("OLLAMA_URL", "http://ollama:11434/api/chat")
MODEL           = os.environ.get("MODEL",      "mistral:7b-instruct-q4_k_m")
PG_HOST         = os.environ.get("PG_HOST",    "pg")
PG_PORT         = os.environ.get("PG_PORT",    "5432")
PG_DATABASE     = os.environ.get("PG_DATABASE","sgb8")
PG_USER         = os.environ.get("PG_USER",    "superset")
PG_PASSWORD     = os.environ.get("PG_PASSWORD","superset")
SUPERSET_URL    = os.environ.get("SUPERSET_URL", "http://superset:8088")
SUPERSET_USER   = os.environ.get("SUPERSET_USER", "admin")
SUPERSET_PASS   = os.environ.get("SUPERSET_PASS", "admin")

# ─────────────────────────────────────
# Datenbank-Schema als Kontext für Mistral
# ─────────────────────────────────────
# ─────────────────────────────────────
# User-Context für Markus (Analytics Basiszugang)
# ─────────────────────────────────────
Hier ist die angepasste Version:
bash

cat > nl-to-sql/app.py << 'EOF'
# [Kopiere hier den Anfang deiner app.py bis zum USER_CONTEXT]

USER_CONTEXT = """

"""


def clean_sql(sql):
    """Bereinigt das SQL von Mistral-Artefakten."""
    # Markdown-Code-Fences entfernen
    sql = re.sub(r'```sql\s*', '', sql)
    sql = re.sub(r'```', '', sql)
    # ALLE Backslashes entfernen (Mistral escaped fälschlicherweise manchmal)
    sql = sql.replace('\\', '')
    # Führendes/nachgelagertes Leerzeichen entfernen
    sql = sql.strip()
    return sql


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/nl-to-sql", methods=["POST"])
def nl_to_sql():
    data     = request.get_json()
    question = data.get("question", "")
    history  = data.get("history", [])   # [{question, sql, error?}, ...]

    if not question:
        return jsonify({"error": "Keine Frage gesendet."}), 400

    # ── Nachichten-Array zusammenbauen ──
    # Erste Nachricht: Kontext + erste Frage aus dem Verlauf (oder aktuelle Frage)
    messages = []

    if history:
        # Erstes Objekt: Kontext + erste Frage
        first = history[0]
        messages.append({
            "role": "user",
            "content": f"{USER_CONTEXT}\n\nFrage: {first['question']}"
        })
        messages.append({
            "role": "assistant",
            "content": first["sql"]  # Hier steht jetzt die Antwort, nicht SQL
        })

        # Restliche Verlaufseinträge
        for entry in history[1:]:
            if entry.get("error"):
                messages.append({
                    "role": "user",
                    "content": f"Das war nicht korrekt:\n{entry['error']}\n\nBitte korrigiere deine Antwort."
                })
                messages.append({
                    "role": "assistant",
                    "content": entry["sql"]  # Die vorherige Antwort
                })
            else:
                messages.append({
                    "role": "user",
                    "content": f"Neue Frage: {entry['question']}"
                })
                messages.append({
                    "role": "assistant",
                    "content": entry["sql"]  # Die Antwort
                })

        # Aktuelle Anfrage (Korrektur oder neue Frage)
        last_history = history[-1]
        if last_history.get("error"):
            # Korrektur-Modus: Fehler wurde gemeldet
            messages.append({
                "role": "user",
                "content": f"Das war nicht korrekt:\n{last_history['error']}\n\nBitte korrigiere deine Antwort."
            })
        else:
            # Neue Frage mit Verlaufskontext
            messages.append({
                "role": "user",
                "content": f"Neue Frage: {question}"
            })
    else:
        # Kein Verlauf – normale Anfrage
        messages.append({
            "role": "user",
            "content": f"{USER_CONTEXT}\n\nFrage: {question}"
        })

    try:
        response = requests.post(OLLAMA_URL, json={
            "model":   MODEL,
            "stream":  False,
            "messages": messages
        }, timeout=120)

        response.raise_for_status()
        raw_sql = response.json()["message"]["content"].strip()
        sql     = clean_sql(raw_sql)

        return jsonify({"sql": sql})

    except requests.exceptions.Timeout:
        return jsonify({"error": "Timeout – Mistral hat zu lange gebraucht. Versuche nochmal."}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/execute-sql", methods=["POST"])
def execute_sql():
    """Führt SQL gegen PostgreSQL aus und gibt Ergebnisse zurück."""
    data = request.get_json()
    sql  = data.get("sql", "").strip()

    if not sql:
        return jsonify({"error": "Kein SQL gesendet."}), 400

    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            database=PG_DATABASE,
            user=PG_USER,
            password=PG_PASSWORD
        )
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(sql)

        # Wenn SELECT: Ergebnisse holen
        if sql.strip().upper().startswith("SELECT"):
            rows    = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            result  = {
                "columns": columns,
                "rows":    [dict(row) for row in rows],
                "count":   len(rows)
            }
        else:
            # INSERT/UPDATE/DELETE: Nur Anzahl betroffener Zeilen
            conn.commit()
            result = {
                "columns": [],
                "rows":    [],
                "count":   cursor.rowcount,
                "message": f"{cursor.rowcount} Zeile(n) betroffen"
            }

        cursor.close()
        conn.close()
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/create-dataset", methods=["POST"])
def create_dataset():
    """Erstellt ein virtuelles Dataset in Superset über die REST API."""
    data = request.get_json()
    sql  = data.get("sql", "").strip()
    name = data.get("name", f"NL_Dataset_{int(os.times().elapsed * 1000)}")

    if not sql:
        return jsonify({"error": "Kein SQL gesendet."}), 400

    try:
        # 1. Superset Login (JWT Token holen)
        login_res = requests.post(
            f"{SUPERSET_URL}/api/v1/security/login",
            json={"username": SUPERSET_USER, "password": SUPERSET_PASS},
            timeout=10
        )
        if not login_res.ok:
            return jsonify({"error": "Superset Login fehlgeschlagen"}), 500

        access_token = login_res.json().get("access_token")
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        # 2. Database-ID holen (sgb8)
        db_res = requests.get(
            f"{SUPERSET_URL}/api/v1/database/?q=(filters:!((col:database_name,opr:eq,value:sgb8)))",
            headers=headers,
            timeout=10
        )
        if not db_res.ok or not db_res.json().get("result"):
            return jsonify({"error": "Datenbank 'sgb8' in Superset nicht gefunden"}), 404

        database_id = db_res.json()["result"][0]["id"]

        # 3. Virtuelles Dataset erstellen
        dataset_payload = {
            "database": database_id,
            "schema": "public",
            "table_name": name,
            "sql": sql
        }

        dataset_res = requests.post(
            f"{SUPERSET_URL}/api/v1/dataset/",
            headers=headers,
            json=dataset_payload,
            timeout=10
        )

        if not dataset_res.ok:
            error_msg = dataset_res.json().get("message", "Unbekannter Fehler")
            return jsonify({"error": f"Dataset-Erstellung fehlgeschlagen: {error_msg}"}), 500

        dataset_id = dataset_res.json().get("id")
        return jsonify({
            "success": True,
            "dataset_id": dataset_id,
            "name": name,
            "url": f"{SUPERSET_URL}/superset/explore/?dataset_type=table&dataset_id={dataset_id}"
        })

    except requests.exceptions.Timeout:
        return jsonify({"error": "Superset-Anfrage Timeout"}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
