-- ─────────────────────────────────────
-- Separate Datenbank für SGB 8 Daten
-- ─────────────────────────────────────
CREATE DATABASE sgb8;

\c sgb8

-- ── Sachbearbeiter ──
CREATE TABLE sachbearbeiter (
    id        SERIAL PRIMARY KEY,
    vorname   VARCHAR(50)  NOT NULL,
    nachname  VARCHAR(50)  NOT NULL,
    abteilung VARCHAR(80),
    telefon   VARCHAR(20),
    email     VARCHAR(100)
);

-- ── Klienten (Familien / Jugendliche) ──
CREATE TABLE klienten (
    id           SERIAL PRIMARY KEY,
    vorname      VARCHAR(50) NOT NULL,
    nachname     VARCHAR(50) NOT NULL,
    geburtsdatum DATE,
    adresse      TEXT,
    telefon      VARCHAR(20),
    status       VARCHAR(30) DEFAULT 'aktiv'
);

-- ── Kindeswohlgefährdungen ──
CREATE TABLE kindeswohlgefaehrdungen (
    id                SERIAL PRIMARY KEY,
    klient_id         INT  REFERENCES klienten(id),
    sachbearbeiter_id INT  REFERENCES sachbearbeiter(id),
    meldungsdatum     DATE NOT NULL,
    beschreibung      TEXT,
    status            VARCHAR(40) DEFAULT 'gemeldet',
    prioritaet        VARCHAR(20) DEFAULT 'mittel',
    abschluss_datum   DATE
);

-- ── Beistandschaften ──
CREATE TABLE beistandschaften (
    id                SERIAL PRIMARY KEY,
    klient_id         INT  REFERENCES klienten(id),
    sachbearbeiter_id INT  REFERENCES sachbearbeiter(id),
    art               VARCHAR(80),
    beginn_datum      DATE,
    ende_datum        DATE,
    status            VARCHAR(30) DEFAULT 'beantragt'
);

-- ── Maßnahmen (an eine KWG gebunden) ──
CREATE TABLE massnahmen (
    id           SERIAL PRIMARY KEY,
    kwg_id       INT  REFERENCES kindeswohlgefaehrdungen(id),
    art          VARCHAR(80),
    beginn_datum DATE,
    ende_datum   DATE,
    status       VARCHAR(30) DEFAULT 'geplant'
);


-- ═══════════════════════════════════════
-- TESTDATEN
-- ═══════════════════════════════════════

-- ── Sachbearbeiter ──
INSERT INTO sachbearbeiter (vorname, nachname, abteilung, telefon, email) VALUES
  ('Maria',  'Steinberg', 'Kindeswohlschutz', '0521 1234-101', 'steinberg@jugendhilfe.de'),
  ('Thomas', 'Bauer',     'Kindeswohlschutz', '0521 1234-102', 'bauer@jugendhilfe.de'),
  ('Sandra', 'Klein',     'Beistandschaft',   '0521 1234-201', 'klein@jugendhilfe.de'),
  ('Markus', 'Hofmann',   'Beistandschaft',   '0521 1234-202', 'hofmann@jugendhilfe.de'),
  ('Julia',  'Engel',     'Familienberatung', '0521 1234-301', 'engel@jugendhilfe.de');

-- ── Klienten ──
INSERT INTO klienten (vorname, nachname, geburtsdatum, adresse, telefon, status) VALUES
  ('Sabine',    'Lange',    '1985-03-12', 'Bahnstraße 14, 33607 Bielefeld',   '0521 987654', 'aktiv'),
  ('Peter',     'Müller',   '1980-07-24', 'Hauptstraße 8, 33602 Bielefeld',   '0521 112233', 'aktiv'),
  ('Franziska', 'Braun',    '1990-11-05', 'Kirchstraße 22, 33613 Bielefeld',  '0521 445566', 'aktiv'),
  ('Daniel',    'Kramer',   '1978-02-18', 'Gartenstraße 31, 33605 Bielefeld', '0521 778899', 'aktiv'),
  ('Nicole',    'Weber',    '1992-09-30', 'Ringstraße 7, 33607 Bielefeld',    '0521 112244', 'abgeschlossen'),
  ('Stefan',    'Richter',  '1983-06-15', 'Schulstraße 19, 33602 Bielefeld',  '0521 335566', 'aktiv'),
  ('Andrea',    'Vogt',     '1988-01-22', 'Lauterstraße 5, 33613 Bielefeld',  '0521 447788', 'aktiv'),
  ('Carsten',   'Huber',    '1975-12-08', 'Parkstraße 28, 33605 Bielefeld',   '0521 990011', 'abgeschlossen');

-- ── Kindeswohlgefährdungen ──
-- Klient 1 (Sabine Lange) hat zwei Meldungen – realistisch bei eskalierende Situationen
INSERT INTO kindeswohlgefaehrdungen (klient_id, sachbearbeiter_id, meldungsdatum, beschreibung, status, prioritaet, abschluss_datum) VALUES
  (1, 1, '2024-01-10', 'Meldung durch Nachbarn: Kind wird regelmäßig allein gelassen, Wohnung in schlechtem Zustand.',                                          'in Bearbeitung', 'sehr hoch', NULL),
  (2, 2, '2024-01-22', 'Schule meldete Auffälligkeiten: Kind kommt regelmäßig ungewaschen und ohne Essen in die Schule.',                                       'abgeschlossen',  'hoch',      '2024-03-15'),
  (3, 1, '2024-02-05', 'Kinderarzt meldete nicht erklärbare Verletzungen beim Kind bei Routineuntersuchung.',                                                    'in Überprüfung', 'mittel',    NULL),
  (1, 2, '2024-03-18', 'Erneute Meldung durch Sozialarbeiter: Situation nicht verbessert, Kind zeigt Verhaltensauffälligkeiten.',                               'in Bearbeitung', 'hoch',      NULL),
  (4, 1, '2024-04-02', 'Meldung durch Erzieher: Kind äußert Angst vor dem Elternteil.',                                                                         'abgeschlossen',  'niedrig',   '2024-05-10'),
  (5, 2, '2024-02-28', 'Polizei meldete häuslichen Konflikt, bei dem sich ein Kind im Zimmer befindet. Verletzungen auf dem Kind sichtbar.',                    'abgeschlossen',  'sehr hoch', '2024-04-01'),
  (6, 1, '2024-05-15', 'Meldung durch Nachbarn: Laute Streitigkeiten, Kind wird in den Konflikt mitgezogen.',                                                   'gemeldet',       'hoch',      NULL),
  (7, 2, '2024-06-03', 'Kinderarzt meldete Unterernährung beim Kind.',                                                                                           'in Überprüfung', 'mittel',    NULL),
  (3, 2, '2024-07-12', 'Schule meldete, dass Kind regelmäßig fehlt und keine Entschuldigung vorlegt.',                                                           'abgeschlossen',  'niedrig',   '2024-08-20'),
  (8, 1, '2024-08-01', 'Meldung durch Arzt: Kind zeigt Zeichen von körperlicher Misshandlung.',                                                                 'abgeschlossen',  'hoch',      '2024-09-30');

-- ── Beistandschaften ──
INSERT INTO beistandschaften (klient_id, sachbearbeiter_id, art, beginn_datum, ende_datum, status) VALUES
  (1, 3, 'Umgangsbeistandschaft',    '2024-02-01', NULL,         'aktiv'),
  (2, 3, 'Betreuungsbeistandschaft', '2024-01-15', '2024-06-30', 'abgeschlossen'),
  (3, 4, 'Umgangsbeistandschaft',    '2024-03-10', NULL,         'aktiv'),
  (5, 3, 'Beratung im Familienrecht','2023-11-01', '2024-03-31', 'abgeschlossen'),
  (6, 4, 'Rechtliche Vertretung',    '2024-06-01', NULL,         'aktiv'),
  (7, 3, 'Betreuungsbeistandschaft', '2024-07-15', NULL,         'beantragt'),
  (4, 4, 'Umgangsbeistandschaft',    '2024-05-01', NULL,         'aktiv');

-- ── Maßnahmen ──
INSERT INTO massnahmen (kwg_id, art, beginn_datum, ende_datum, status) VALUES
  (1,  'Krisenintervention',          '2024-01-12', '2024-01-20', 'abgeschlossen'),
  (1,  'Familienintervention',        '2024-01-25', NULL,         'aktiv'),
  (2,  'Beratung',                    '2024-02-01', '2024-03-10', 'abgeschlossen'),
  (2,  'Inobhutnahme',               '2024-02-05', '2024-02-28', 'abgeschlossen'),
  (3,  'Beratung',                    '2024-02-15', NULL,         'aktiv'),
  (4,  'Krisenintervention',          '2024-03-20', '2024-03-25', 'abgeschlossen'),
  (4,  'Familienintervention',        '2024-04-01', NULL,         'aktiv'),
  (6,  'Inobhutnahme',               '2024-03-02', '2024-03-20', 'abgeschlossen'),
  (6,  'Pflegefamilienunterbringung', '2024-03-21', '2024-04-01', 'abgeschlossen'),
  (7,  'Beratung',                    '2024-05-20', NULL,         'geplant'),
  (8,  'Soziale Begleitung',          '2024-06-10', NULL,         'aktiv'),
  (10, 'Krisenintervention',          '2024-08-03', '2024-08-10', 'abgeschlossen'),
  (10, 'Inobhutnahme',               '2024-08-05', '2024-08-31', 'abgeschlossen');
