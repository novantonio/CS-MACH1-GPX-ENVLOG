# 📍 GPS Tracker — Streamlit App

Registra la tua posizione GPS nel tempo direttamente dal browser del telefono, e scarica tutto come CSV.

---

## 🚀 Come usarla

### 1. Avvia in locale

```bash
# Clona il repo
git clone https://github.com/TUO_USERNAME/gps-tracker.git
cd gps-tracker

# Installa le dipendenze
pip install -r requirements.txt

# Avvia l'app
streamlit run app.py
```

> **⚠️ Nota:** La Geolocation API del browser funziona **solo su HTTPS** o `localhost`.  
> In locale su `http://localhost:8501` funziona normalmente.  
> Per usarla da telefono tramite rete locale, usa **Streamlit Cloud** (vedi sotto).

---

### 2. Deploy su Streamlit Cloud (consigliato per uso da mobile)

1. Fai push del repo su GitHub
2. Vai su [share.streamlit.io](https://share.streamlit.io)
3. Collega il tuo account GitHub
4. Seleziona il repo e imposta:
   - **Main file:** `app.py`
   - **Branch:** `main`
5. Clicca **Deploy** — in pochi minuti hai un URL HTTPS pubblico

---

## 📱 Come usarla dal telefono

1. Apri l'URL dell'app nel browser del telefono (Safari su iPhone, Chrome su Android)
2. Premi **🛰 Abilita GPS** → il browser chiede il permesso di accedere alla posizione → accetta
3. Imposta l'intervallo con lo slider (es. ogni 5 secondi)
4. Premi **▶ Avvia** per iniziare la registrazione
5. Premi **⏹ Stop** quando vuoi fermarti
6. Clicca **⬇️ Scarica CSV** per salvare il file

---

## 📂 Struttura del progetto

```
gps-tracker/
├── app.py            # App Streamlit principale
├── requirements.txt  # Dipendenze Python
└── README.md         # Questa guida
```

---

## 📄 Formato CSV di output

| Timestamp              | Latitudine | Longitudine | Accuratezza (m) |
|------------------------|------------|-------------|-----------------|
| 2025-05-18T10:23:01Z   | 45.464664  | 9.188540    | 12              |
| 2025-05-18T10:23:06Z   | 45.464701  | 9.188512    | 10              |

---

## 🔒 Privacy

L'app **non salva nulla su server**. Tutte le posizioni restano nella sessione del browser e vengono eliminate alla chiusura. Il CSV viene generato lato client.

---

## 🛠 Tecnologie

- [Streamlit](https://streamlit.io) — interfaccia web Python
- [Geolocation API](https://developer.mozilla.org/en-US/docs/Web/API/Geolocation_API) — lettura GPS dal browser
- [pandas](https://pandas.pydata.org) — generazione CSV
