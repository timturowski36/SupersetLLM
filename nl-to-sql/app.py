from flask import Flask, request, jsonify, send_from_directory
import requests
import os

app = Flask(__name__, static_folder="static")

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://ollama:11434/api/chat")
MODEL     = os.environ.get("MODEL",      "mistral:7b-instruct-q4_k_m")

# ─────────────────────────────────────
# Datenbank-Schema als Kontext für Mistral
# ─────────────────────────────────────
DB_SCHEMA = """
Du bist ein SQL-Experte. Generiere NUR SQL-Abfragen für eine PostgreSQL-Datenbank.
Antworte NUR mit dem SQL-Code – keine Erklärungen, keine Backticks, kein anderer Text.

Verfügbare Tabellen und Spalten:

TABLE sachbearbeiter (
    id        SERIAL PRIMARY KEY,
    vorname   VARCHAR(50),
    nachname  VARCHAR(50),
    abteilung VARCHAR(80),   -- z.B. 'Kindeswohlschutz', 'Beistandschaft', 'Familienberatung'
    telefon   VARCHAR(20),
    email     VARCHAR(100)
);

TABLE klienten (
    id           SERIAL PRIMARY KEY,
    vorname      VARCHAR(50),
    nachname     VARCHAR(50),
    geburtsdatum DATE,
    adresse      TEXT,
    telefon      VARCHAR(20),
    status       VARCHAR(30)  -- 'aktiv' oder 'abgeschlossen'
);

TABLE kindeswohlgefaehrdungen (
    id                SERIAL PRIMARY KEY,
    klient_id         INT  REFERENCES klienten(id),
    sachbearbeiter_id INT  REFERENCES sachbearbeiter(id),
    meldungsdatum     DATE,
    beschreibung      TEXT,
    status            VARCHAR(40), -- 'gemeldet', 'in Überprüfung', 'in Bearbeitung', 'abgeschlossen'
    prioritaet        VARCHAR(20), -- 'niedrig', 'mittel', 'hoch', 'sehr hoch'
    abschluss_datum   DATE
);

TABLE beistandschaften (
    id                SERIAL PRIMARY KEY,
    klient_id         INT  REFERENCES klienten(id),
    sachbearbeiter_id INT  REFERENCES sachbearbeiter(id),
    art               VARCHAR(80), -- z.B. 'Umgangsbeistandschaft', 'Betreuungsbeistandschaft'
    beginn_datum      DATE,
    ende_datum        DATE,
    status            VARCHAR(30)  -- 'beantragt', 'aktiv', 'abgeschlossen'
);

TABLE massnahmen (
    id           SERIAL PRIMARY KEY,
    kwg_id       INT  REFERENCES kindeswohlgefaehrdungen(id),
    art          VARCHAR(80), -- z.B. 'Krisenintervention', 'Inobhutnahme', 'Familienintervention'
    beginn_datum DATE,
    ende_datum   DATE,
    status       VARCHAR(30)  -- 'geplant', 'aktiv', 'abgeschlossen'
);
"""


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/nl-to-sql", methods=["POST"])
def nl_to_sql():
    data = request.get_json()
    user_question = data.get("question", "")

    if not user_question:
        return jsonify({"error": "Keine Frage gesendet."}), 400

    prompt = f"{DB_SCHEMA}\n\nFrage: {user_question}\n\nSQL:"

    try:
        response = requests.post(OLLAMA_URL, json={
            "model":  MODEL,
            "stream": False,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }, timeout=120)

        response.raise_for_status()
        sql = response.json()["message"]["content"].strip()

        # Backticks entfernen falls Mistral sie trotzdem einfügt
        sql = sql.replace("```sql", "").replace("```", "").strip()

        return jsonify({"sql": sql})

    except requests.exceptions.Timeout:
        return jsonify({"error": "Timeout – Mistral hat zu lange gebraucht. Versuche nochmal."}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
