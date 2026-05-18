import streamlit as st
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components

# ── CS-MACH1 brand constants ──────────────────────────────────────────────────
BRAND_BLUE  = "#00A6D6"
BRAND_HOVER = "#007EA3"
TEXT_MUTED  = "#555555"

st.set_page_config(
    page_title="CS-MACH1 · GPS Tracker",
    page_icon="📍",
    layout="centered",
)

st.markdown(f"""
<style>
.stButton>button {{
    background-color: {BRAND_BLUE};
    color: white;
    border-radius: 8px;
    border: none;
    font-weight: 600;
    padding: 10px 24px;
    transition: background 0.2s;
}}
.stButton>button:hover {{
    background-color: {BRAND_HOVER};
    color: white;
}}
div[data-testid="stDownloadButton"] > button {{
    background-color: {BRAND_BLUE};
    color: white;
    border-radius: 8px;
    border: none;
    font-weight: 600;
}}
div[data-testid="stDownloadButton"] > button:hover {{
    background-color: {BRAND_HOVER};
    color: white;
}}
.cs-main-header {{
    font-size: 34px;
    font-weight: 700;
    color: {BRAND_BLUE};
    margin-bottom: 0px;
}}
.cs-sub-header {{
    font-size: 16px;
    color: {TEXT_MUTED};
    margin-bottom: 20px;
}}
.cs-status-badge {{
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 600;
    margin: 4px 0;
}}
.cs-badge-active   {{ background: #e6f7fb; color: {BRAND_BLUE}; border: 1px solid {BRAND_BLUE}; }}
.cs-badge-inactive {{ background: #f2f2f2; color: #888;          border: 1px solid #ccc; }}
.cs-badge-rec      {{ background: #fff0f0; color: #e53e3e;       border: 1px solid #e53e3e; }}
.cs-info-card {{
    background: #f0fafd;
    border-left: 4px solid {BRAND_BLUE};
    border-radius: 6px;
    padding: 14px 18px;
    font-size: 14px;
    color: {TEXT_MUTED};
    margin: 10px 0;
}}
.cs-footer {{
    text-align: center;
    color: grey;
    font-size: 13px;
    margin-top: 2rem;
}}
</style>
""", unsafe_allow_html=True)

# ── Patch iframe per geolocation ─────────────────────────────────────────────
# Streamlit monta i componenti HTML in iframe senza allow="geolocation".
# Questo script sulla pagina principale osserva il DOM e aggiunge l'attributo
# non appena l'iframe compare, prima che il browser blocchi la richiesta GPS.
st.markdown("""
<script>
(function patchGeoIframes() {
  function allow(iframe) {
    if (!iframe.allow || !iframe.allow.includes('geolocation')) {
      iframe.allow = (iframe.allow ? iframe.allow + '; ' : '') + 'geolocation';
    }
  }
  document.querySelectorAll('iframe').forEach(allow);
  const observer = new MutationObserver(mutations => {
    mutations.forEach(m => m.addedNodes.forEach(node => {
      if (node.tagName === 'IFRAME') allow(node);
      if (node.querySelectorAll) node.querySelectorAll('iframe').forEach(allow);
    }));
  });
  observer.observe(document.body, { childList: true, subtree: true });
})();
</script>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
try:
    st.image("logo.png", width=220)
except Exception:
    pass

st.markdown("<div class='cs-main-header'>📍 CS-MACH1 GPS Tracker</div>", unsafe_allow_html=True)
st.markdown("<div class='cs-sub-header'>Registra la tua posizione nel tempo ed esporta il tracciato in CSV.</div>", unsafe_allow_html=True)
st.divider()

# ── Session state ─────────────────────────────────────────────────────────────
if "positions"   not in st.session_state: st.session_state.positions   = []
if "recording"   not in st.session_state: st.session_state.recording   = False
if "gps_enabled" not in st.session_state: st.session_state.gps_enabled = False

# ── Controls ──────────────────────────────────────────────────────────────────
col1, col2 = st.columns([1, 1])

with col1:
    interval = st.slider("Intervallo acquisizione (secondi)", min_value=1, max_value=60, value=5, step=1)

with col2:
    st.markdown("&nbsp;", unsafe_allow_html=True)
    badge_rec = (
        "<div class='cs-status-badge cs-badge-rec'>🔴 Registrazione attiva</div>"
        if st.session_state.recording
        else "<div class='cs-status-badge cs-badge-inactive'>⚪ In attesa</div>"
    )
    badge_gps = (
        "<div class='cs-status-badge cs-badge-active'>🛰 GPS abilitato</div>"
        if st.session_state.gps_enabled
        else "<div class='cs-status-badge cs-badge-inactive'>⚫ GPS non attivo</div>"
    )
    st.markdown(badge_rec + badge_gps, unsafe_allow_html=True)

st.divider()

# ── GPS component ─────────────────────────────────────────────────────────────
gps_html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:transparent;color:#333;padding:12px 4px;font-size:13px}}
.btn-row{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px}}
button{{font-family:inherit;font-weight:600;border:none;border-radius:8px;padding:9px 18px;cursor:pointer;transition:background 0.2s,opacity 0.2s;font-size:13px}}
#btnGps{{background:{BRAND_BLUE};color:#fff}}
#btnGps:hover{{background:{BRAND_HOVER}}}
#btnStart{{background:#38a169;color:#fff}}
#btnStart:hover{{background:#276749}}
#btnStop{{background:#e53e3e;color:#fff}}
#btnStop:hover{{background:#c53030}}
button:disabled{{opacity:.35;cursor:not-allowed}}
#status{{padding:7px 12px;background:#f0fafd;border-left:3px solid {BRAND_BLUE};border-radius:4px;color:#2c5282;font-size:12px;min-height:28px;margin-bottom:6px}}
#coords{{padding:7px 12px;background:#f7f7f7;border-radius:4px;font-size:12px;color:#444;display:none;font-family:'Courier New',monospace}}
</style></head><body>
<div class="btn-row">
  <button id="btnGps">🛰 Abilita GPS</button>
  <button id="btnStart" disabled>▶ Avvia</button>
  <button id="btnStop" disabled>⏹ Stop</button>
</div>
<div id="status">In attesa di abilitare il GPS...</div>
<div id="coords">—</div>
<script>
const INTERVAL_MS={interval * 1000};
let timer=null,recording=false,positions=[];
const btnGps=document.getElementById('btnGps');
const btnStart=document.getElementById('btnStart');
const btnStop=document.getElementById('btnStop');
const status=document.getElementById('status');
const coordsDiv=document.getElementById('coords');
function setStatus(m){{status.textContent=m;}}
btnGps.addEventListener('click',()=>{{
  if(!navigator.geolocation){{setStatus('❌ Geolocation non supportata.');return;}}
  setStatus('📡 Richiesta permesso GPS...');
  navigator.geolocation.getCurrentPosition(
    (pos)=>{{setStatus('✅ GPS abilitato — premi Avvia per iniziare.');coordsDiv.style.display='block';showCoords(pos);btnStart.disabled=false;btnGps.textContent='✅ GPS attivo';btnGps.disabled=true;send({{type:'gps_enabled'}});}},
    (err)=>{{setStatus('❌ Errore: '+err.message);}},
    {{enableHighAccuracy:true}}
  );
}});
function showCoords(pos){{
  const ts=new Date().toLocaleTimeString('it-IT');
  coordsDiv.textContent='🕐 '+ts+'   Lat: '+pos.coords.latitude.toFixed(6)+'   Lon: '+pos.coords.longitude.toFixed(6)+'   ±'+Math.round(pos.coords.accuracy)+'m';
}}
btnStart.addEventListener('click',()=>{{
  if(recording)return;
  recording=true;positions=[];btnStart.disabled=true;btnStop.disabled=false;
  setStatus('🔴 Registrazione in corso...');send({{type:'start'}});
  function acquire(){{
    navigator.geolocation.getCurrentPosition(
      (pos)=>{{showCoords(pos);const e={{timestamp:new Date().toISOString(),lat:pos.coords.latitude,lon:pos.coords.longitude,accuracy_m:Math.round(pos.coords.accuracy)}};positions.push(e);send({{type:'position',data:e}});}},
      (err)=>{{setStatus('⚠️ Errore GPS: '+err.message);}},
      {{enableHighAccuracy:true,timeout:10000}}
    );
  }}
  acquire();timer=setInterval(acquire,INTERVAL_MS);
}});
btnStop.addEventListener('click',()=>{{
  if(!recording)return;
  recording=false;clearInterval(timer);timer=null;btnStop.disabled=true;btnStart.disabled=false;
  setStatus('✅ Stop — '+positions.length+' posizioni acquisite.');send({{type:'stop',positions:positions}});
}});
function send(payload){{window.parent.postMessage({{isStreamlitMessage:true,type:'streamlit:setComponentValue',value:payload}},'*');}}
</script></body></html>"""

result = components.html(gps_html, height=155, scrolling=False)

# ── Handle component messages ─────────────────────────────────────────────────
if result is not None and isinstance(result, dict):
    msg_type = result.get("type")
    if msg_type == "gps_enabled":
        st.session_state.gps_enabled = True
    elif msg_type == "start":
        st.session_state.recording = True
        st.session_state.positions = []
    elif msg_type == "position":
        entry = result.get("data", {})
        if entry:
            st.session_state.positions.append(entry)
    elif msg_type == "stop":
        st.session_state.recording = False
        raw = result.get("positions", [])
        if raw:
            st.session_state.positions = raw

# ── Live table (FIFO, ultimi 5) ───────────────────────────────────────────────
st.divider()

n_total = len(st.session_state.positions)
label = f"### 📋 Ultime posizioni acquisite"
if n_total > 0:
    label += f"  <span style='font-size:14px;color:{TEXT_MUTED};font-weight:400'>— totale: {n_total}</span>"
st.markdown(label, unsafe_allow_html=True)

if st.session_state.positions:
    # Mostra le ultime 5 righe, la più recente in cima (FIFO)
    last5 = st.session_state.positions[-5:][::-1]
    df_live = pd.DataFrame(last5)
    df_live.columns = ["Timestamp", "Latitudine", "Longitudine", "Accuratezza (m)"]
    # Formatta timestamp in ora locale leggibile
    df_live["Timestamp"] = pd.to_datetime(df_live["Timestamp"]).dt.strftime("%H:%M:%S")
    st.dataframe(df_live, use_container_width=True, hide_index=True)

    # Download sempre disponibile (CSV completo, non solo le 5 righe)
    df_full = pd.DataFrame(st.session_state.positions)
    df_full.columns = ["Timestamp", "Latitudine", "Longitudine", "Accuratezza (m)"]
    csv_bytes = df_full.to_csv(index=False).encode("utf-8")
    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.download_button(
        label="⬇️ Scarica CSV completo",
        data=csv_bytes,
        file_name=f"cs_mach1_gps_{now_str}.csv",
        mime="text/csv",
    )
else:
    st.markdown(
        "<div class='cs-info-card'>Nessuna posizione ancora acquisita.<br>"
        "Abilita il GPS, imposta l'intervallo e premi <strong>Avvia</strong>.</div>",
        unsafe_allow_html=True,
    )

# ── Clear ─────────────────────────────────────────────────────────────────────
if st.session_state.positions:
    st.divider()
    if st.button("🗑 Cancella sessione"):
        st.session_state.positions = []
        st.session_state.recording = False
        st.session_state.gps_enabled = False
        st.rerun()

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("<div class='cs-footer'>CS-MACH1 Project · GPS Tracker</div>", unsafe_allow_html=True)
