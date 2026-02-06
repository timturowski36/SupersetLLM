# Superset + Mistral NL-to-SQL für SGB 8 Jugendhilfe

Ein vollständiges Data-Analytics-Setup mit Natural Language to SQL für Jugendhilfe-Daten nach SGB 8. Nutzt Apache Superset für Dashboards und SQL Lab, Mistral 7B über Ollama für lokale LLM-gestützte SQL-Generierung, und PostgreSQL für die Datenhaltung.

## 📋 Überblick

Dieses Projekt kombiniert:

- **Apache Superset** – Open-Source Business Intelligence und Datenvisualisierung
- **PostgreSQL** – Relationale Datenbank mit SGB 8 Testdaten (Sachbearbeiter, Klienten, Kindeswohlgefährdungen, Beistandschaften, Maßnahmen)
- **Ollama + Mistral 7B** – Lokales Large Language Model für SQL-Generierung
- **NL-to-SQL Service** – Eigenentwickelter Flask-Service mit Chat-Interface

### Warum dieser Aufbau?

Apache Superset hat **keine native NL-to-SQL Funktion** in der Open-Source-Version (nur in der kommerziellen Preset-Variante). Dieser Stack bietet eine vollständig Open-Source-Alternative mit lokalem LLM – keine externen APIs, keine Cloud-Abhängigkeiten, volle Datenkontrolle.

## 🏗 Architektur

```
┌─────────────────────────────────────────────────────────┐
│                       Browser                            │
│  ┌──────────────────┐       ┌──────────────────────┐   │
│  │ Superset UI      │       │ NL→SQL Chat          │   │
│  │ localhost:8088   │       │ localhost:5000       │   │
│  └──────────────────┘       └──────────────────────┘   │
└───────────┬──────────────────────────┬──────────────────┘
            │                          │
            ▼                          ▼
   ┌────────────────┐         ┌─────────────────┐
   │   Superset     │         │  NL-to-SQL      │
   │   Container    │         │  Flask Service  │
   └────────┬───────┘         └────────┬────────┘
            │                          │
            │ SQL-Abfragen             │ API-Calls
            ▼                          ▼
   ┌────────────────┐         ┌─────────────────┐
   │  PostgreSQL    │         │     Ollama      │
   │  Port 5432     │         │  Mistral 7B     │
   │                │         │  Port 11434     │
   │  • superset DB │         └─────────────────┘
   │  • sgb8 DB     │
   └────────────────┘
```

**Workflow:**
1. Nutzer stellt Frage auf Deutsch im Chat (localhost:5000)
2. Flask-Service sendet Frage + DB-Schema an Ollama/Mistral
3. Mistral generiert PostgreSQL-SQL
4. Nutzer kopiert SQL und führt es in Superset SQL Lab aus

## 🔧 Voraussetzungen

### Hardware
- **Minimum:** 16 GB RAM (ohne GPU läuft Mistral auf CPU, langsam aber funktional)
- **Empfohlen:** 32 GB RAM + NVIDIA GPU (8+ GB VRAM) für schnelle Inference
- **Speicher:** ~20 GB freier Festplattenspeicher

### Software
- Ubuntu 20.04+ (oder andere Linux-Distribution)
- Docker Engine (nicht Docker Desktop mit Snap!)
- Docker Compose Plugin
- (Optional) NVIDIA Container Toolkit für GPU-Support

### Wichtig: Docker Installation

**Snap-Docker funktioniert nicht** mit GPU-Support. Installiere native Docker Engine:

```bash
# Snap Docker entfernen (falls vorhanden)
sudo snap remove --purge docker

# Native Docker Engine installieren
curl -fsSL https://get.docker.com | sudo bash

# User-Zugriff
sudo usermod -aG docker $USER
newgrp docker

# (Optional) NVIDIA Container Toolkit für GPU
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

## 🚀 Installation

### 1. Repository-Struktur

```
superset-mistral-sgb8/
├── docker-compose.yml
├── Dockerfile              # Superset mit psycopg2
├── superset_config.py      # Superset-Konfiguration
├── init.sql                # PostgreSQL-Testdaten
├── setup.sh                # Automatisches Setup-Script
└── nl-to-sql/              # NL-to-SQL Service
    ├── Dockerfile
    ├── requirements.txt
    ├── app.py
    └── static/
        └── index.html
```

### 2. Container starten

```bash
# Alle Dateien in einen Ordner kopieren
cd superset-mistral-sgb8

# Setup ausführen (startet Container, lädt Mistral herunter)
chmod +x setup.sh
bash setup.sh
```

Das Script führt automatisch aus:
- Container-Start (PostgreSQL, Ollama, Superset, NL-to-SQL)
- Mistral 7B Download (~4 GB, 2-5 Minuten)
- Superset-Initialisierung (Admin-User, Datenbank-Setup)

### 3. Manuelle Installation (falls setup.sh nicht funktioniert)

```bash
# 1. Container starten
docker compose up -d

# 2. Auf Ollama warten
until curl -s http://localhost:11434/api/tags > /dev/null 2>&1; do
    sleep 2
done

# 3. Mistral herunterladen
docker exec ollama ollama pull mistral:7b-instruct-q4_k_m

# 4. Auf Superset warten
until curl -s http://localhost:8088 > /dev/null 2>&1; do
    sleep 5
done
```

## 📊 Verwendung

### Superset (Business Intelligence)

1. Öffne `http://localhost:8088`
2. Login: `admin` / `admin`
3. **Datenbank verbinden:**
   - Settings → Data Connections → + Database
   - PostgreSQL auswählen
   - Host: `pg`, Port: `5432`, Database: `sgb8`, User: `superset`, Password: `superset`
4. **SQL Lab nutzen:**
   - Menü → SQL Lab
   - Database: `sgb8` auswählen
   - SQL-Abfragen direkt ausführen oder aus dem NL-to-SQL Service kopieren

### NL-to-SQL Chat

1. Öffne `http://localhost:5000`
2. Stelle Fragen auf Deutsch, z.B.:
   - "Wie viele Kindeswohlgefährdungen sind aktuell in Bearbeitung?"
   - "Welcher Sachbearbeiter hat die meisten Fälle?"
   - "Zeige alle aktiven Beistandschaften mit Klient und Sachbearbeiter"
3. **SQL kopieren** → in Superset SQL Lab einfügen → ausführen
4. **Bei Fehlern:** Button "⚠ Fehler melden" klicken, PostgreSQL-Fehlermeldung einfügen → Mistral korrigiert das SQL automatisch

### Datenbank-Schema (sgb8)

**Tabellen:**
- `sachbearbeiter` – Mitarbeiter im Jugendamt
- `klienten` – Familien/Jugendliche unter Betreuung
- `kindeswohlgefaehrdungen` – Gemeldete Gefährdungsfälle
- `beistandschaften` – Rechtliche Beistandschaften
- `massnahmen` – Maßnahmen zu Kindeswohlgefährdungen

## 🐛 Troubleshooting

### Mistral generiert kein SQL / NL-to-SQL antwortet nicht

```bash
# Prüfen ob Mistral heruntergeladen wurde
docker exec ollama ollama list

# Falls leer: Manuell herunterladen
docker exec ollama ollama pull mistral:7b-instruct-q4_k_m

# NL-to-SQL Service neu starten
docker restart nl-to-sql
```

### Superset kann nicht auf PostgreSQL zugreifen

```bash
# PostgreSQL läuft?
docker ps | grep pg

# Logs prüfen
docker logs pg

# Neu starten
docker restart pg
```

### GPU wird nicht erkannt

```bash
# NVIDIA Container Toolkit installiert?
docker run --rm --gpus all nvidia/cuda:11.0.3-base-ubuntu20.04 nvidia-smi

# Wenn Fehler: Toolkit installieren
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker

# docker-compose.yml: GPU-Block einkommentieren (Zeilen 36-42)
```

### Superset zeigt "No data" in SQL Lab

- Stelle sicher, dass die Datenbank-Verbindung auf `sgb8` zeigt (nicht `superset`)
- Schema: `public` auswählen
- Tabellen sollten sichtbar sein: `sachbearbeiter`, `klienten`, etc.

### "Permission denied" bei Docker-Befehlen

```bash
# User zur Docker-Gruppe hinzufügen
sudo usermod -aG docker $USER
newgrp docker
```

## 🔐 Produktions-Hinweise

**Dieses Setup ist für Entwicklung/POC gedacht.** Für Produktionsumgebungen:

1. **Passwörter ändern** (PostgreSQL, Superset Admin, `SUPERSET_SECRET_KEY`)
2. **HTTPS einrichten** (Reverse Proxy mit nginx/Caddy)
3. **Persistente Volumes** in docker-compose konfigurieren
4. **Backup-Strategie** für PostgreSQL einrichten
5. **Resource Limits** in Docker setzen
6. **Monitoring** einrichten (Prometheus + Grafana)
7. **GPU-Variante nutzen** für Produktions-Performance

## 📝 Datenschutz

- **Alle Daten bleiben lokal** – kein Cloud-LLM, keine externen APIs
- Mistral läuft vollständig on-premise über Ollama
- Testdaten sind synthetisch generiert (keine echten Personendaten)
- Für echte SGB 8 Daten: Datenschutzkonzept nach DSGVO erforderlich

## 🛠 Technologie-Stack

| Komponente | Version | Lizenz |
|------------|---------|--------|
| Apache Superset | 6.x | Apache 2.0 |
| PostgreSQL | 16 | PostgreSQL License |
| Ollama | Latest | MIT |
| Mistral 7B Instruct | Q4_K_M | Apache 2.0 |
| Flask | 3.0 | BSD |
| Docker | Latest | Apache 2.0 |

## 🤝 Credits

- Apache Superset Team
- Mistral AI für das Open-Source-Modell
- Ollama für die lokale LLM-Infrastruktur

## 📄 Lizenz

Dieses Projekt nutzt ausschließlich Open-Source-Komponenten mit permissiven Lizenzen (Apache 2.0, MIT, BSD, PostgreSQL License). Alle Teile können kommerziell genutzt werden.

---

**Fragen? Probleme?** Öffne ein Issue oder kontaktiere das Entwicklerteam.
