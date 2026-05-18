import streamlit as st
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components

st.set_page_config(
    page_title="CS-MACH1 · GPS Tracker",
    page_icon="📍",
    layout="centered",
)

# ── Session state ─────────────────────────────────────────────────────────────
for key, default in [
    ("positions",   []),
    ("recording",   False),
    ("gps_enabled", False),
    ("stopped",     False),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Header ────────────────────────────────────────────────────────────────────
try:
    st.image("logo.png", width=220)
except Exception:
    pass

st.title("📍 CS-MACH1 GPS Tracker")
st.caption("Registra la tua posizione nel tempo ed esporta il tracciato in CSV.")
st.divider()

# ── Stato GPS / registrazione ─────────────────────────────────────────────────
col_s1, col_s2 = st.columns(2)
with col_s1:
    if st.session_state.recording:
        st.success("🔴 Registrazione attiva")
    elif st.session_state.stopped:
        st.info("✅ Registrazione terminata")
    else:
        st.warning("⚪ In attesa")
with col_s2:
    if st.session_state.gps_enabled:
        st.success("🛰 GPS abilitato")
    else:
        st.warning("⚫ GPS non attivo")

# ── Slider intervallo ─────────────────────────────────────────────────────────
interval = st.slider("Intervallo acquisizione (secondi)", min_value=1, max_value=60, value=5, step=1)
st.divider()

# ── GPS component HTML/JS ─────────────────────────────────────────────────────
# Il patch MutationObserver aggiunge allow="geolocation" agli iframe di Streamlit
# (tecnica 4: DOM patch sulla pagina host).
# Lo script è embeddato direttamente nell'HTML del componente stesso,
# e viene eseguito nel contesto dell'iframe — usa postMessage per comunicare.
gps_html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
      background:transparent;color:#333;padding:10px 2px;font-size:13px}}
.btn-row{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px}}
button{{font-family:inherit;font-weight:600;border:none;border-radius:8px;
        padding:9px 18px;cursor:pointer;transition:background .2s,opacity .2s;font-size:13px}}
#btnGps  {{background:#00A6D6;color:#fff}} #btnGps:hover  {{background:#007EA3}}
#btnStart{{background:#38a169;color:#fff}} #btnStart:hover{{background:#276749}}
#btnStop {{background:#e53e3e;color:#fff}} #btnStop:hover {{background:#c53030}}
button:disabled{{opacity:.35;cursor:not-allowed}}
#status{{padding:7px 12px;background:#f0fafd;border-left:3px solid #00A6D6;
         border-radius:4px;color:#2c5282;font-size:12px;min-height:28px;margin-bottom:6px}}
#coords{{padding:7px 12px;background:#f7f7f7;border-radius:4px;font-size:12px;
         color:#444;display:none;font-family:'Courier New',monospace}}
</style>
</head><body>
<div class="btn-row">
  <button id="btnGps">🛰 Abilita GPS</button>
  <button id="btnStart" disabled>▶ Avvia</button>
  <button id="btnStop"  disabled>⏹ Stop</button>
</div>
<div id="status">In attesa di abilitare il GPS...</div>
<div id="coords">—</div>
<script>
// Patch geolocation permission sul parent (tecnica 4)
(function(){{
  function patch(iframe){{
    if(!iframe.allow||!iframe.allow.includes('geolocation'))
      iframe.allow=(iframe.allow?iframe.allow+'; ':')+'geolocation';
  }}
  try{{
    var frames=window.parent.document.querySelectorAll('iframe');
    frames.forEach(patch);
    new MutationObserver(function(ms){{
      ms.forEach(function(m){{m.addedNodes.forEach(function(n){{
        if(n.tagName==='IFRAME') patch(n);
        if(n.querySelectorAll) n.querySelectorAll('iframe').forEach(patch);
      }});}});
    }}).observe(window.parent.document.body,{{childList:true,subtree:true}});
  }}catch(e){{}}
}})();

const INTERVAL_MS={interval * 1000};
let timer=null,recording=false,positions=[];
const btnGps=document.getElementById('btnGps');
const btnStart=document.getElementById('btnStart');
const btnStop=document.getElementById('btnStop');
const statusEl=document.getElementById('status');
const coordsEl=document.getElementById('coords');
function setStatus(m){{statusEl.textContent=m;}}

btnGps.addEventListener('click',function(){{
  if(!navigator.geolocation){{setStatus('❌ Geolocation non supportata.');return;}}
  setStatus('📡 Richiesta permesso GPS...');
  navigator.geolocation.getCurrentPosition(
    function(pos){{
      setStatus('✅ GPS abilitato — premi Avvia per iniziare.');
      coordsEl.style.display='block'; showCoords(pos);
      btnStart.disabled=false; btnGps.textContent='✅ GPS attivo'; btnGps.disabled=true;
      send({{type:'gps_enabled'}});
    }},
    function(err){{setStatus('❌ Errore: '+err.message);}},
    {{enableHighAccuracy:true}}
  );
}});

function showCoords(pos){{
  var ts=new Date().toLocaleTimeString('it-IT');
  coordsEl.textContent='🕐 '+ts+'   Lat: '+pos.coords.latitude.toFixed(6)
    +'   Lon: '+pos.coords.longitude.toFixed(6)+'   ±'+Math.round(pos.coords.accuracy)+'m';
}}

btnStart.addEventListener('click',function(){{
  if(recording) return;
  recording=true; positions=[];
  btnStart.disabled=true; btnStop.disabled=false;
  setStatus('🔴 Registrazione in corso...'); send({{type:'start'}});
  function acquire(){{
    navigator.geolocation.getCurrentPosition(
      function(pos){{
        showCoords(pos);
        var e={{timestamp:new Date().toISOString(),
               lat:pos.coords.latitude,
               lon:pos.coords.longitude,
               accuracy_m:Math.round(pos.coords.accuracy)}};
        positions.push(e); send({{type:'position',data:e}});
      }},
      function(err){{setStatus('⚠️ Errore GPS: '+err.message);}},
      {{enableHighAccuracy:true,timeout:10000}}
    );
  }}
  acquire(); timer=setInterval(acquire,INTERVAL_MS);
}});

btnStop.addEventListener('click',function(){{
  if(!recording) return;
  recording=false; clearInterval(timer); timer=null;
  btnStop.disabled=true; btnStart.disabled=false;
  setStatus('✅ Stop — '+positions.length+' posizioni acquisite.');
  send({{type:'stop',positions:positions}});
}});

function send(payload){{
  window.parent.postMessage({{
    isStreamlitMessage:true,
    type:'streamlit:setComponentValue',
    value:payload
  }},'*');
}}
</script></body></html>"""

result = components.html(gps_html, height=155, scrolling=False)

# ── Gestione messaggi dal componente ─────────────────────────────────────────
if result is not None and isinstance(result, dict):
    msg = result.get("type")
    if msg == "gps_enabled":
        st.session_state.gps_enabled = True
    elif msg == "start":
        st.session_state.recording   = True
        st.session_state.stopped     = False
        st.session_state.positions   = []
    elif msg == "position":
        entry = result.get("data", {})
        if entry:
            st.session_state.positions.append(entry)
    elif msg == "stop":
        st.session_state.recording   = False
        st.session_state.stopped     = True
        raw = result.get("positions", [])
        if raw:
            st.session_state.positions = raw

# ── Sezione dati ──────────────────────────────────────────────────────────────
st.divider()

def make_df(rows, ts_fmt="%H:%M:%S"):
    df = pd.DataFrame(rows)
    df.columns = ["Timestamp", "Latitudine", "Longitudine", "Accuratezza (m)"]
    df["Timestamp"] = pd.to_datetime(df["Timestamp"]).dt.strftime(ts_fmt)
    return df

if not st.session_state.positions:
    st.info("Nessuna posizione ancora acquisita. Abilita il GPS, imposta l'intervallo e premi **Avvia**.")

elif st.session_state.recording:
    n = len(st.session_state.positions)
    st.subheader(f"📡 Live — {n} punt{'o' if n==1 else 'i'} acquisit{'o' if n==1 else 'i'}")
    last5 = st.session_state.positions[-5:][::-1]
    st.dataframe(make_df(last5), use_container_width=True, hide_index=True)

elif st.session_state.stopped:
    n = len(st.session_state.positions)
    preview_n = min(5, n)
    st.subheader(f"✅ Registrazione completata — {n} punti totali")

    preview = st.session_state.positions[-preview_n:][::-1]
    st.caption(f"Anteprima ultime {preview_n} posizioni (più recente in cima):")
    st.dataframe(make_df(preview), use_container_width=True, hide_index=True)

    st.info(f"💾 Vuoi scaricare il tracciato completo? Il CSV contiene tutti i **{n} punti** della sessione.")

    col_dl, col_clear = st.columns([2, 1])
    with col_dl:
        df_full = make_df(st.session_state.positions, ts_fmt="%Y-%m-%dT%H:%M:%S")
        csv_bytes = df_full.to_csv(index=False).encode("utf-8")
        now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.download_button(
            label="⬇️ Sì, scarica CSV completo",
            data=csv_bytes,
            file_name=f"cs_mach1_gps_{now_str}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with col_clear:
        if st.button("🗑 Nuova sessione", use_container_width=True):
            for k in ("positions", "recording", "stopped", "gps_enabled"):
                st.session_state[k] = [] if k == "positions" else False
            st.rerun()

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption("CS-MACH1 Project · GPS Tracker")
