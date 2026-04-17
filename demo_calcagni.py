import streamlit as st
import pandas as pd
import os
import smtplib
import re
import json
from email.mime.text import MIMEText
from datetime import datetime

st.set_page_config(page_title="Fuel SaaS", layout="wide")

# =========================
# 🏢 AZIENDA
# =========================
azienda = st.query_params.get("azienda", "demo")
if isinstance(azienda, list):
    azienda = azienda[0]

FILE = f"clienti_{azienda}.csv"
CONFIG_FILE = f"config_{azienda}.json"

st.markdown(f"## 🏢 Azienda: {azienda.upper()}")

# =========================
# 📧 EMAIL
# =========================
EMAIL_MITTENTE = "webolcompany@gmail.com"
PASSWORD_APP = "neqr ewtb bdkr lmca"

def invia_email(destinatario, prezzo, cc=None):
    try:
        data = datetime.now().strftime("%d/%m/%Y")

        prezzo_txt = f"{prezzo:.3f}".replace(".", ",")

        testo = st.session_state.email_template.replace("{prezzo}", prezzo_txt)

        msg = MIMEText(testo)

        msg["Subject"] = f"OFFERTA CARBURANTE - {data}"
        msg["From"] = EMAIL_MITTENTE
        msg["To"] = destinatario

        if cc:
            msg["Cc"] = cc

        destinatari = [destinatario]
        if cc:
            destinatari.append(cc)

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_MITTENTE, PASSWORD_APP)
        server.send_message(msg, to_addrs=destinatari)
        server.quit()

    except Exception as e:
        st.error(f"Errore email: {e}")

# =========================
# 🔒 UTIL
# =========================
def format_euro(x):
    if x is None or pd.isna(x):
        return "0,000"
    return f"{round(float(x), 3):.3f}".replace(".", ",")

def calc_price(base, margine, trasporto):
    return round(float(base) + float(margine) + float(trasporto), 3)

def filtra_clienti(df, search):
    if not search:
        return df
    return df[
        df["Nome"].astype(str).str.contains(search, case=False, na=False) |
        df["PIVA"].astype(str).str.contains(search, case=False, na=False) |
        df["Telefono"].astype(str).str.contains(search, case=False, na=False)
    ]

# =========================
# 💾 CONFIG
# =========================
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

# =========================
# 💾 DATA
# =========================
def load_data():
    if os.path.exists(FILE):
        df = pd.read_csv(FILE)

        for col in ["Nome","PIVA","Telefono","Email"]:
            df[col] = df[col].astype(str)

        for col in ["Margine","Trasporto"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

        if "UltimoPrezzo" not in df.columns:
            df["UltimoPrezzo"] = None

        return df

    return pd.DataFrame(columns=[
        "ID","Nome","PIVA","Telefono","Email",
        "Margine","Trasporto","UltimoPrezzo"
    ])

def save_data(df):
    df.to_csv(FILE, index=False)

# =========================
# INIT
# =========================
config = load_config()

if "clienti" not in st.session_state:
    st.session_state.clienti = load_data()

if "page" not in st.session_state:
    st.session_state.page = "dashboard"

if "edit_id" not in st.session_state:
    st.session_state.edit_id = None

if "prezzo_base" not in st.session_state:
    st.session_state.prezzo_base = 1.000

if "email_template" not in st.session_state:
    st.session_state.email_template = config.get("email_template", """Gentile cliente,

con la presente le formuliamo la nostra migliore offerta sui prodotti utilizzati dalla Vostra azienda ''ipotizzando'' un presunto scarico per la giornata in oggetto.

Gasolio per autotrazione = {prezzo}/litro + Iva

Per via delle attuali fluttuazioni di mercato i prezzi in elenco avranno una validità giornaliera.
Le consegne dei prodotti avverranno entro il giorno dopo alla data di effettuazione dell’ordine.

ATTENZIONE!!! GLI ORDINI DOVRANNO PERVENIRE ENTRO LE ORE 14:00 RISPONDENDO ALLA PRESENTE OPPURE CHIAMANDO AL NUMERO DI TELEFONO.

La presente comunicazione, con le informazioni in essa contenute e ogni documento o file allegato, e' strettamente riservata e soggetta alle garanzie che legano i rapporti tra le parti interessate...

Long Life Consulting.
""")

df = st.session_state.clienti

# =========================
# NAV
# =========================
c1, c2, c3 = st.columns(3)

with c1:
    if st.button("📊 Dashboard", use_container_width=True):
        st.session_state.page = "dashboard"

with c2:
    if st.button("👤 Clienti", use_container_width=True):
        st.session_state.page = "clienti"

with c3:
    if st.button("➕ Nuovo", use_container_width=True):
        st.session_state.page = "cliente"

st.divider()

# =========================================================
# 📊 DASHBOARD
# =========================================================
if st.session_state.page == "dashboard":

    st.markdown("## ⛽ Dashboard operativa")

    prezzo_base = st.number_input("⛽ Prezzo base", value=float(st.session_state.prezzo_base), step=0.001, format="%.3f")
    st.session_state.prezzo_base = prezzo_base

    # =========================
    # TEMPLATE EMAIL
    # =========================
    st.markdown("### ✉️ Testo email")

    email_template = st.text_area(
        "Scrivi il testo della mail (usa {prezzo})",
        value=st.session_state.email_template,
        height=300
    )

    st.session_state.email_template = email_template
    config["email_template"] = email_template
    save_config(config)

    st.info("💡 Usa {prezzo} per inserire automaticamente il prezzo")

    # VALIDAZIONE
    template = st.session_state.email_template
    manca_prezzo = "{prezzo}" not in template

    pattern_numero = r"\b\d+[.,]\d+\b"
    template_senza_placeholder = template.replace("{prezzo}", "")
    numeri_presenti = re.findall(pattern_numero, template_senza_placeholder)

    if manca_prezzo:
        st.error("❌ Devi inserire {prezzo}")

    if numeri_presenti:
        st.error(f"❌ Non inserire prezzi manuali: {', '.join(numeri_presenti)}")

    blocca_invio = manca_prezzo or len(numeri_presenti) > 0

    cc_email = st.text_input("📧 Email CC (opzionale)")

    # =========================
    # INVIO MASSIVO
    # =========================
    if st.button("📧 Invia email a tutti", disabled=blocca_invio):

        count = 0

        for _, c in df.iterrows():
            if c["Email"] and pd.notna(c["Email"]):

                prezzo = calc_price(prezzo_base, c["Margine"], c["Trasporto"])

                invia_email(c["Email"], prezzo, cc=cc_email)

                st.session_state.clienti.loc[
                    st.session_state.clienti["ID"] == c["ID"],
                    "UltimoPrezzo"
                ] = prezzo

                count += 1

        save_data(st.session_state.clienti)
        st.success(f"Email inviate: {count}")