"""AItrader — live market intelligence terminal. Real market feeds; orders disabled by design."""
import os, hmac, html, time
from datetime import datetime, timezone
from urllib.parse import quote
import ccxt
import feedparser
import pandas as pd
import requests
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="AItrader | Pro Terminal", page_icon="⚡", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html,body,[data-testid="stApp"]{font-family:Inter,sans-serif;background:#080e18;color:#e9f2ff}
.block-container{max-width:1500px;padding-top:1.1rem}
[data-testid="stHeader"]{background:transparent}
h1,h2,h3{letter-spacing:-.04em}
[data-testid="stMetric"]{background:#111d2c;border:1px solid #24344b;padding:15px;border-radius:14px}
[data-testid="stMetricLabel"]{color:#94a9c3}
[data-testid="stTabs"] button{font-weight:700}
div.stButton>button{border-radius:9px;border-color:#29435a}
div.stButton>button[kind="primary"]{background:#00c7a4;color:#06111b;border:0}
.terminal{background:linear-gradient(105deg,#11283a,#101a2b);border:1px solid #29435b;padding:23px;border-radius:18px;margin-bottom:15px}
.kicker{color:#52e3c1;font-size:.72rem;font-weight:800;letter-spacing:.2em}
.sub{color:#9fb1c6}
.pill{display:inline-block;background:#12372e;color:#70f2c9;padding:5px 10px;border-radius:30px;font-size:.75rem;font-weight:700}
</style>""",unsafe_allow_html=True)

def secret(key):
    try: return str(st.secrets.get(key,os.environ.get(key,""))).strip()
    except Exception: return str(os.environ.get(key,"")).strip()

password=secret("APP_PASSWORD")
if not password:
    st.error("Beveiliging vereist: stel APP_PASSWORD in bij je hosting-omgeving (Render: Environment).")
    st.stop()
if not st.session_state.get("signed_in"):
    st.markdown('<div class="terminal"><div class="kicker">AITRADER / SECURE TERMINAL</div><h1>Professional market intelligence.</h1><p class="sub">Echte beursdata. Controleerbare signalen. Geen fictieve winstcijfers.</p></div>',unsafe_allow_html=True)
    with st.form("signin"):
        attempt=st.text_input("Dashboardwachtwoord",type="password")
        if st.form_submit_button("Open terminal",type="primary"):
            if hmac.compare_digest(attempt,password):
                st.session_state.signed_in=True
                st.rerun()
            else: st.error("Onjuist wachtwoord.")
    st.stop()

EXCHANGES=["kraken","bitvavo","coinbase","binance","okx","bybit"]
PAIRS=["BTC/EUR","ETH/EUR","SOL/EUR","BTC/USD","ETH/USD","BTC/USDT","ETH/USDT","SOL/USDT"]
with st.sidebar:
    st.title("⚡ AItrader")
    st.caption("MARKET INTELLIGENCE TERMINAL")
    st.success("LIVE DATA • ORDERS UIT")
    exchange_name=st.selectbox("Exchange",EXCHANGES)
    symbol=st.selectbox("Handelspaar",PAIRS)
    timeframe=st.selectbox("Candleperiode",["1m","5m","15m","1h","4h","1d"],index=2)
    st.caption("Niet ieder handelspaar bestaat op iedere beurs.")
    if st.button("Uitloggen"):
        st.session_state.signed_in=False
        st.rerun()
    st.divider()
    st.warning("Geen live orderuitvoering. Geen bankkoppeling. Geen winstgarantie.")

@st.cache_data(ttl=20,show_spinner=False)
def market(exchange_name,symbol,timeframe):
    exchange=getattr(ccxt,exchange_name)({"enableRateLimit":True,"timeout":12000})
    exchange.load_markets()
    if symbol not in exchange.markets: raise ValueError("Dit handelspaar is niet beschikbaar bij "+exchange_name)
    raw=exchange.fetch_ohlcv(symbol,timeframe=timeframe,limit=160)
    if not raw: raise ValueError("Geen candles ontvangen")
    df=pd.DataFrame(raw,columns=["timestamp","open","high","low","close","volume"])
    df["date"]=pd.to_datetime(df.timestamp,unit="ms",utc=True)
    return df

@st.cache_data(ttl=120,show_spinner=False)
def news(topic):
    url="https://news.google.com/rss/search?q="+quote(topic)+"&hl=en-US&gl=US&ceid=US:en"
    r=requests.get(url,timeout=12,headers={"User-Agent":"AItrader-terminal/1.0"})
    r.raise_for_status()
    feed=feedparser.parse(r.content)
    return [{"title":x.get("title",""),"link":x.get("link",""),"published":x.get("published","")} for x in feed.entries[:15]]

def indicators(df):
    close=df.close
    ema20=close.ewm(span=20,adjust=False).mean()
    ema50=close.ewm(span=50,adjust=False).mean()
    delta=close.diff()
    up=delta.clip(lower=0).ewm(alpha=1/14,adjust=False).mean()
    down=(-delta.clip(upper=0)).ewm(alpha=1/14,adjust=False).mean()
    rsi=100-100/(1+up/down.replace(0,float("nan")))
    return ema20,ema50,rsi

st.markdown('<div class="terminal"><div class="kicker">⚡ AITRADER / PRO MARKET TERMINAL</div><h1>Markets. Intelligence. Control.</h1><p class="sub">Live publieke beursdata · Technische analyse · Actuele nieuwsfeeds · Mobiel en desktop</p><span class="pill">● READ-ONLY • NO REAL ORDERS</span></div>',unsafe_allow_html=True)
bar1,bar2,bar3,bar4=st.columns([2,2,2,1])
with bar1: exchange_name=st.selectbox("Beurs",EXCHANGES,index=EXCHANGES.index(exchange_name),key="top_exchange")
with bar2: symbol=st.selectbox("Markt",PAIRS,index=PAIRS.index(symbol),key="top_symbol")
with bar3: timeframe=st.selectbox("Interval",["1m","5m","15m","1h","4h","1d"],index=["1m","5m","15m","1h","4h","1d"].index(timeframe),key="top_timeframe")
with bar4:
    st.write("")
    if st.button("↻ Vernieuw",use_container_width=True):
        market.clear()
        news.clear()
        st.rerun()

try:
    df=market(exchange_name,symbol,timeframe)
    ema20,ema50,rsi=indicators(df)
    last=float(df.close.iloc[-1])
    prev=float(df.close.iloc[-2])
    change=(last/prev-1)*100
    trend="Stijgend" if ema20.iloc[-1]>ema50.iloc[-1] else "Dalend"
    cols=st.columns(4)
    cols[0].metric("Marktprijs",f"{last:,.2f} {symbol.split('/')[1]}",f"{change:+.2f}% laatste candle")
    cols[1].metric("Trend EMA 20/50",trend)
    cols[2].metric("RSI (14)",f"{rsi.iloc[-1]:.1f}" if pd.notna(rsi.iloc[-1]) else "N.v.t.")
    cols[3].metric("24/7 trading", "UIT", "Geen orderverbinding",delta_color="off")
    st.caption(f"Bron: {exchange_name.upper()} publieke API · laatste candle {df.date.iloc[-1].strftime('%Y-%m-%d %H:%M UTC')} · data kan vertraagd zijn.")
    tabs=st.tabs(["📈 Trading terminal","📰 Nieuws & AI","💼 Portefeuille","🛡️ Risico & orders","⚙️ Koppelingen"])
    with tabs[0]:
        left,right=st.columns([3,1],gap="large")
        with left:
            fig=make_subplots(rows=2,cols=1,shared_xaxes=True,vertical_spacing=.03,row_heights=[.78,.22])
            fig.add_trace(go.Candlestick(x=df.date,open=df.open,high=df.high,low=df.low,close=df.close,name="OHLC",increasing_line_color="#20d9aa",decreasing_line_color="#fa667a"),row=1,col=1)
            fig.add_trace(go.Scatter(x=df.date,y=ema20,name="EMA 20",line=dict(color="#ffc166",width=1.5)),row=1,col=1)
            fig.add_trace(go.Scatter(x=df.date,y=ema50,name="EMA 50",line=dict(color="#6c9dff",width=1.5)),row=1,col=1)
            fig.add_trace(go.Bar(x=df.date,y=df.volume,name="Volume",marker_color="#537eaa"),row=2,col=1)
            fig.update_layout(height=570,paper_bgcolor="#0d1725",plot_bgcolor="#0d1725",font_color="#b9cee5",margin=dict(l=10,r=10,t=15,b=15),xaxis_rangeslider_visible=False,legend=dict(orientation="h",y=1.08),dragmode="pan")
            fig.update_xaxes(showgrid=True,gridcolor="#213044")
            fig.update_yaxes(showgrid=True,gridcolor="#213044")
            st.plotly_chart(fig,width="stretch",config={"scrollZoom":False,"displaylogo":False})
        with right:
            st.subheader("Marktindicatoren")
            st.metric("EMA 20",f"{ema20.iloc[-1]:,.2f}")
            st.metric("EMA 50",f"{ema50.iloc[-1]:,.2f}")
            st.metric("Candlevolume",f"{df.volume.iloc[-1]:,.3f}")
            st.divider()
            st.subheader("Handelspaneel")
            st.selectbox("Richting",["Kopen","Verkopen"],key="order_side")
            st.number_input("Bedrag (indicatief)",min_value=0.0,value=100.0,step=25.0)
            st.button("Echte order plaatsen — uitgeschakeld",disabled=True,use_container_width=True)
            st.caption("Dit paneel verzendt geen orders en bewaart geen geld.")
    with tabs[1]:
        topic=st.selectbox("Nieuwsfeed",["Bitcoin cryptocurrency ETF markets","Ethereum blockchain regulation","Federal Reserve inflation rates","ECB Europe financial markets","Global geopolitics energy oil"])
        try:
            items=news(topic)
            st.caption("RSS-updates worden maximaal elke 2 minuten opgehaald. Geen milliseconde-nieuwsmonitoring.")
            if not items: st.info("Geen berichten gevonden.")
            for item in items:
                st.markdown("**["+item["title"].replace("[","").replace("]","")+"]("+item["link"]+")**")
                st.caption(item["published"])
            if st.button("AI-samenvatting aanvragen",type="primary"):
                key=secret("OPENAI_API_KEY")
                if not key: st.warning("Voeg OPENAI_API_KEY toe als serversecret om echte AI-analyse te activeren.")
                else:
                    from openai import OpenAI
                    prompt="Analyseer voorzichtig het volgende nieuws. Maak geen winstclaims of autonome kooporders. Geef scenario's, risico's, ontbrekende informatie en onzekerheden.\n"+ "\n".join(x["title"] for x in items[:12])
                    try:
                        result=OpenAI(api_key=key,timeout=20).responses.create(model=secret("OPENAI_MODEL") or "gpt-4.1-mini",input=prompt,max_output_tokens=550)
                        st.write(result.output_text)
                    except Exception as e: st.error("AI-aanroep mislukt. Controleer sleutel/model en serverlogs.")
        except Exception as e: st.warning("Nieuwsfeed niet beschikbaar: "+str(e))
    with tabs[2]:
        st.subheader("Echte portefeuille")
        st.info("Er is nog geen beursaccount gekoppeld. We tonen geen verzonnen saldo, transacties of rendement.")
        st.markdown("Een toekomstige read-only exchange-koppeling kan saldo en posities ophalen. Voeg nooit API-sleutels toe aan de browser, GitHub of chat.")
        st.metric("Gekoppelde accounts",0)
    with tabs[3]:
        st.error("Echte orders en autonome handel staan UIT. Dit is nog geen productiesysteem voor echt geld.")
        max_loss=st.slider("Voorbeeld: maximaal dagverlies (%)",0.1,5.0,1.0,0.1)
        risk=st.slider("Voorbeeld: maximaal risico per positie (%)",0.1,3.0,0.5,0.1)
        st.caption(f"Ontwerpwaarden: dagverlies {max_loss:.1f}%, positierisico {risk:.1f}%. Deze instellingen sturen geen echte bot aan.")
        st.button("Noodstop: orders zijn al uit",disabled=True)
        st.markdown("Voor live trading zijn exchange-authenticatie, auditlogs, persistente opslag, risicocontroles, sandbox-tests, onafhankelijke monitoring en expliciete toestemming vereist.")
    with tabs[4]:
        st.subheader("Beschikbare integraties")
        st.success("Publieke exchange-marktdata: actief als de API bereikbaar is.")
        st.write("Nieuws: Google News RSS, periodiek vernieuwd.")
        st.write("AI: optioneel, via serversecret OPENAI_API_KEY.")
        st.warning("Bankkoppeling: niet beschikbaar. Gebruik uitsluitend een erkende open-banking provider met toestemming en veilige OAuth-flow; geen bankwachtwoorden verzamelen.")
        st.warning("Exchange trading: niet verbonden; API-handelsrechten en geldstromen zijn niet geïmplementeerd.")
except Exception as exc:
    st.error("Live beursdata momenteel niet beschikbaar: "+str(exc))
    st.info("Kies eventueel een andere beurs of markt; niet ieder paar wordt overal aangeboden.")
st.divider()
st.caption("AItrader • Real market data, no simulated account balances • Geen financieel advies • Geen rendementsgarantie")
