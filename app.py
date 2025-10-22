"""
╔══════════════════════════════════════════════════════════════╗
║          🚀 KAZANCKAPISI - BIST TARAMA SİSTEMİ              ║
║      Streamlit Arayüz + Colab Stratejileri + Telegram       ║
╚══════════════════════════════════════════════════════════════╝

NASIL YENİ STRATEJİ EKLERSİN?
1. st.session_state.strategies dictionary'sine yeni bir key-value ekle
2. Format:
   "KAZANCKAPISI_XX": {
       "code": "def analyze(df): ...",
       "desc": "Açıklama",
       "best_timeframe": "1 Saat, Günlük"  # Opsiyonel
   }
3. Kaydet ve çalıştır!
"""

import sys
required = {'streamlit': 'streamlit', 'pandas': 'pandas', 'numpy': 'numpy', 
           'yfinance': 'yfinance', 'plotly': 'plotly', 'scipy': 'scipy'}
missing = [m for d, m in required.items() if not __import__(m)]
if missing:
    print(f"❌ Eksik: {' '.join(missing)}\npip install {' '.join(missing)}")
    sys.exit(1)

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import plotly.graph_objects as go
import time
from scipy.signal import argrelextrema

try:
    import telebot
    TELEGRAM_OK = True
except:
    TELEGRAM_OK = False

# ═══════════════════════════════════════════════════════════════
# AYARLAR
# ═══════════════════════════════════════════════════════════════

TELEGRAM_TOKEN = "8310745808:AAGpnfSna6-6AJ5I2FNKyES2Rdj_Xqu4b7o"
TELEGRAM_CHAT_ID = "1801093830"

st.set_page_config(page_title="KAZANCKAPISI v1.0", page_icon="🚀", layout="wide")

st.markdown("""<style>
.big-font {font-size:28px !important; font-weight:bold; color:#00ff87;}
</style>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# SESSION STATE + TARAMA GEÇMİŞİ
# ═══════════════════════════════════════════════════════════════

if 'results' not in st.session_state:
    st.session_state.results = []

if 'tarama_gecmisi' not in st.session_state:
    st.session_state.tarama_gecmisi = []

if 'strategies' not in st.session_state:
    st.session_state.strategies = {
        
        # ═══════════════════════════════════════════════════════════════
        # COLAB STRATEJİLERİ - TAM ENTEGRE
        # ═══════════════════════════════════════════════════════════════
        
        "KAZANCKAPISI_1": {
            "code": """def analyze(df):
    '''Quantum Fibonacci Extension - Colab Stratejisi'''
    if len(df) < 20:
        return None
    recent = df.tail(20)
    high, low = recent['High'].max(), recent['Low'].min()
    current = df['Close'].iloc[-1]
    diff = high - low
    fib_1272 = low + 1.272 * diff
    fib_1618 = low + 1.618 * diff
    target = fib_1272 if current < fib_1272 else (fib_1618 if current < fib_1618 else None)
    if target:
        pot = ((target - current) / current) * 100
        if pot > 3:
            return {'score': 60 + min(30, pot * 3), 'target': target, 'reason': f'Fib Ext %{pot:.1f}'}
    return None""",
            "desc": "📐 Fibonacci Extension (1.272, 1.618 seviyeleri) | En İyi: Günlük, Haftalık",
            "best_timeframe": "Günlük, Haftalık"
        },
        
        "KAZANCKAPISI_2": {
            "code": """def analyze(df):
    '''Harmonic Pattern (ABCD, Gartley, Butterfly)'''
    if len(df) < 50:
        return None
    closes, highs, lows = df['Close'].values, df['High'].values, df['Low'].values
    high_peaks = argrelextrema(highs, np.greater, order=5)[0]
    low_peaks = argrelextrema(lows, np.less, order=5)[0]
    current = closes[-1]
    
    if len(high_peaks) >= 2 and len(low_peaks) >= 2:
        last_high, last_low = highs[high_peaks[-1]], lows[low_peaks[-1]]
        if last_low < current < last_high * 1.1:
            ab_ratio = (last_high - last_low) / max(last_low, 0.01)
            if 0.05 < ab_ratio < 0.20:
                return {'score': 65 + min(20, ab_ratio * 100), 'target': last_high * 1.05, 'reason': 'ABCD Bullish'}
    
    if len(high_peaks) >= 3:
        return {'score': 70, 'target': current * 1.08, 'reason': 'Gartley Pattern'}
    return None""",
            "desc": "📊 Harmonik Formasyonlar (ABCD, Gartley, Butterfly) | En İyi: Günlük, 4 Saat",
            "best_timeframe": "Günlük, 4 Saat"
        },
        
        "KAZANCKAPISI_3": {
            "code": """def analyze(df):
    '''Volume Explosion + Clustering'''
    if len(df) < 20:
        return None
    vol_ma = df['Volume'].rolling(20).mean().iloc[-1]
    current_vol = df['Volume'].iloc[-1]
    if pd.isna(vol_ma) or vol_ma == 0:
        return None
    volume_ratio = current_vol / vol_ma
    if volume_ratio > 2.0:
        recent_vol = df['Volume'].tail(5).mean()
        clustering = recent_vol / vol_ma
        if clustering > 1.3:
            return {'score': 70 + min(25, (volume_ratio - 2) * 10), 'target': df['Close'].iloc[-1] * 1.08, 'reason': f'Hacim {volume_ratio:.1f}x'}
    return None""",
            "desc": "🔥 Anormal Hacim Patlaması + Clustering | En İyi: 5dk, 15dk, 1 Saat",
            "best_timeframe": "5dk, 15dk, 1 Saat"
        },
        
        "KAZANCKAPISI_4": {
            "code": """def analyze(df):
    '''RSI Divergence Pro'''
    if len(df) < 30:
        return None
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean().fillna(0)
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean().fillna(0.0001).replace(0, 0.0001)
    rsi = 100 - (100 / (1 + gain / loss))
    closes, rsi_vals = df['Close'].values, rsi.values
    price_peaks = argrelextrema(closes[-20:], np.greater, order=3)[0]
    rsi_peaks = argrelextrema(rsi_vals[-20:], np.greater, order=3)[0]
    if len(price_peaks) >= 2 and len(rsi_peaks) >= 2:
        if closes[-20:][price_peaks[-1]] < closes[-20:][price_peaks[-2]]:
            if rsi_vals[-20:][rsi_peaks[-1]] > rsi_vals[-20:][rsi_peaks[-2]]:
                return {'score': 80, 'target': df['Close'].iloc[-1] * 1.10, 'reason': 'Bullish RSI Divergence'}
    return None""",
            "desc": "⚡ RSI Divergence (Bullish Sinyal) | En İyi: 1 Saat, 4 Saat, Günlük",
            "best_timeframe": "1 Saat, 4 Saat, Günlük"
        },
        
        "KAZANCKAPISI_5": {
            "code": """def analyze(df):
    '''Float Squeeze + Institutional Flow'''
    if len(df) < 20:
        return None
    volumes, closes = df['Volume'].values, df['Close'].values
    recent_vol = volumes[-10:].mean() / volumes[-20:-10].mean()
    recent_price = (closes[-1] - closes[-10]) / closes[-10]
    if recent_vol > 1.5 and recent_price > 0.05:
        obv = [volumes[0]]
        for i in range(1, len(closes)):
            obv.append(obv[-1] + volumes[i] if closes[i] > closes[i-1] else obv[-1] - volumes[i] if closes[i] < closes[i-1] else obv[-1])
        obv_trend = (obv[-1] - obv[-10]) / obv[-10] if obv[-10] != 0 else 0
        if obv_trend > 0.1:
            return {'score': 75 + min(20, recent_vol * 10), 'target': closes[-1] * 1.12, 'reason': 'Float Squeeze + Kurumsal'}
    return None""",
            "desc": "🔒 Float Squeeze + OBV Birikim | En İyi: Günlük, Haftalık",
            "best_timeframe": "Günlük, Haftalık"
        },
        
        "KAZANCKAPISI_6": {
            "code": """def analyze(df):
    '''Psychological Barrier (Round Numbers)'''
    if len(df) < 50:
        return None
    current = df['Close'].iloc[-1]
    nearest_five = round(current / 5) * 5
    nearest_ten = round(current / 10) * 10
    distance_five = abs(current - nearest_five) / current
    distance_ten = abs(current - nearest_ten) / current
    resistance = np.percentile(df['High'].values[-50:], 95)
    if (distance_five < 0.02 or distance_ten < 0.03) and current < resistance * 0.95:
        target = max(nearest_five, nearest_ten, resistance)
        return {'score': 60 + (1 - min(distance_five, distance_ten)) * 30, 'target': target, 'reason': f'Psikolojik: ₺{target:.1f}'}
    return None""",
            "desc": "🧠 Yuvarlak Sayı Psikolojisi (5, 10 katları) | En İyi: Tüm Periyotlar",
            "best_timeframe": "Tüm Periyotlar"
        },
        
        "KAZANCKAPISI_7": {
            "code": """def analyze(df):
    '''Yükselen Üçgen'''
    if len(df) < 30:
        return None
    son_30 = df.tail(30)
    ust_var = son_30['High'].nlargest(5).std() / son_30['High'].nlargest(5).mean()
    alt_noktalar = son_30['Low'].nsmallest(5).sort_index()
    alt_egim = (alt_noktalar.iloc[-1] - alt_noktalar.iloc[0]) / len(alt_noktalar)
    if ust_var < 0.02 and alt_egim > 0:
        return {'score': 75, 'target': son_30['High'].max() * 1.05, 'reason': 'Yükselen Üçgen'}
    return None""",
            "desc": "🔺 Yükselen Üçgen Formasyonu | En İyi: Günlük, 4 Saat",
            "best_timeframe": "Günlük, 4 Saat"
        },
        
        "KAZANCKAPISI_8": {
            "code": """def analyze(df):
    '''Çift Dip (W)'''
    if len(df) < 60:
        return None
    son_60 = df.tail(60).reset_index(drop=True)
    dipler = []
    for i in range(5, len(son_60)-5):
        if son_60['Low'].iloc[i] == son_60['Low'].iloc[i-5:i+6].min():
            dipler.append((i, son_60['Low'].iloc[i]))
    if len(dipler) >= 2:
        d1_idx, d1_val = dipler[-2]
        d2_idx, d2_val = dipler[-1]
        if abs(d1_val - d2_val) / d1_val < 0.03 and (d2_idx - d1_idx) > 10:
            boyun = son_60['High'].iloc[d1_idx:d2_idx].max()
            return {'score': 80, 'target': boyun + (boyun - d1_val), 'reason': 'Çift Dip (W)'}
    return None""",
            "desc": "📈 Çift Dip (W) Formasyonu | En İyi: Günlük, Haftalık",
            "best_timeframe": "Günlük, Haftalık"
        },
        
        "KAZANCKAPISI_9": {
            "code": """def analyze(df):
    '''EMA Dizilimi (20>50>200) + RSI'''
    if len(df) < 200:
        return None
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    df['EMA200'] = df['Close'].ewm(span=200).mean()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean().fillna(0)
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean().fillna(0.0001).replace(0, 0.0001)
    rsi = 100 - (100 / (1 + gain / loss))
    son = df.iloc[-1]
    if son['EMA20'] > son['EMA50'] > son['EMA200'] and son['Close'] > son['EMA20'] and 50 <= rsi.iloc[-1] <= 70:
        return {'score': 70 + (rsi.iloc[-1] - 50) / 2, 'target': son['Close'] * 1.05, 'reason': f'Güçlü Trend RSI:{rsi.iloc[-1]:.0f}'}
    return None""",
            "desc": "📊 EMA Dizilimi + RSI Sağlıklı | En İyi: 1 Saat, 4 Saat, Günlük",
            "best_timeframe": "1 Saat, 4 Saat, Günlük"
        },
        
        "KAZANCKAPISI_10": {
            "code": """def analyze(df):
    '''Bollinger Bands Squeeze'''
    if len(df) < 20:
        return None
    df['BB_Mid'] = df['Close'].rolling(20).mean()
    std = df['Close'].rolling(20).std()
    df['BB_Upper'] = df['BB_Mid'] + (std * 2)
    df['BB_Lower'] = df['BB_Mid'] - (std * 2)
    son = df.iloc[-1]
    bw = (son['BB_Upper'] - son['BB_Lower']) / son['BB_Mid']
    avg_bw = ((df['BB_Upper'] - df['BB_Lower']) / df['BB_Mid']).tail(20).mean()
    if bw < avg_bw * 0.6:
        return {'score': 65 + (1 - bw / avg_bw) * 30, 'target': son['Close'] * 1.08, 'reason': 'BB Squeeze'}
    return None""",
            "desc": "🎯 Bollinger Bands Daralması (Patlama Hazırlığı) | En İyi: 15dk, 1 Saat",
            "best_timeframe": "15dk, 1 Saat"
        },
        
        # SEN BURAYA YENİ STRATEJİLER EKLEYEBİLİRSİN!
        # Örnek:
        # "KAZANCKAPISI_11": {
        #     "code": """def analyze(df):
        #         # Kodun buraya
        #         return {'score': 70, 'target': df['Close'].iloc[-1] * 1.05, 'reason': 'Sebep'}""",
        #     "desc": "Açıklama | En İyi: Zaman Dilimi",
        #     "best_timeframe": "1 Saat"
        # },
    }

# ═══════════════════════════════════════════════════════════════
# HİSSE LİSTESİ (SEN TAM LİSTEYİ BURAYA EKLE)
# ═══════════════════════════════════════════════════════════════

BIST_STOCKS = {
    "Test Grubu": ['THYAO', 'GARAN', 'AKBNK', 'EREGL', 'TUPRS', 'PETKM', 'SISE', 'ASELS', 'TCELL', 'SAHOL'],
    # Tam listeyi buraya ekle
}

# ═══════════════════════════════════════════════════════════════
# VERİ ÇEKME
# ═══════════════════════════════════════════════════════════════

@st.cache_data(ttl=300)
def get_stock_data(symbol, period='3mo', interval='1d'):
    try:
        ticker = symbol.strip().upper() + ('.IS' if not symbol.endswith('.IS') else '')
        data = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
        if data.empty or len(data) < 5:
            return None
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        return data[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
    except:
        return None

def run_strategy(df, code):
    try:
        if df is None or len(df) < 1:
            return None
        namespace = {'df': df, 'pd': pd, 'np': np, 'len': len, 'min': min, 'max': max, 'abs': abs, 'argrelextrema': argrelextrema}
        exec(code, namespace)
        result = namespace.get('analyze', lambda x: None)(df)
        return result if result and isinstance(result, dict) and 'score' in result and 'target' in result else None
    except:
        return None

def analyze_stock(symbol, period, interval, selected_strategies, min_score):
    df = get_stock_data(symbol, period, interval)
    if df is None:
        return None
    current_price = df['Close'].iloc[-1]
    signals = []
    for strat_name in selected_strategies:
        if strat_name in st.session_state.strategies:
            result = run_strategy(df, st.session_state.strategies[strat_name]['code'])
            if result:
                signals.append({'name': strat_name, 'score': result['score'], 'target': result['target'], 'reason': result.get('reason', '')})
    if not signals:
        return None
    avg_score = sum(s['score'] for s in signals) / len(signals)
    if avg_score < min_score:
        return None
    max_target = max(s['target'] for s in signals)
    return {
        'symbol': symbol,
        'price': current_price,
        'target': max_target,
        'potential': ((max_target - current_price) / current_price) * 100,
        'score': avg_score,
        'signals': signals,
        'signal_count': len(signals)
    }

# ═══════════════════════════════════════════════════════════════
# TELEGRAM
# ═══════════════════════════════════════════════════════════════

def telegram_gonder(sonuclar):
    if not TELEGRAM_OK:
        return False
    try:
        bot = telebot.TeleBot(TELEGRAM_TOKEN)
        now = datetime.now().strftime("%d.%m.%Y %H:%M")
        if not sonuclar:
            mesaj = f"⚠️ <b>KAZANCKAPISI</b>\n{now}\n\nSinyal yok"
        else:
            mesaj = f"🚀 <b>KAZANCKAPISI</b>\n{now}\n\n"
            for idx, s in enumerate(sonuclar[:10], 1):
                mesaj += f"<b>{idx}. {s['symbol']}</b>\n💰 {s['price']:.2f}₺ → 🎯{s['target']:.2f}₺ (%{s['potential']:.1f})\n📊 Skor:{s['score']:.0f} | {s['signal_count']} sinyal\n\n"
            mesaj += f"✅ {len(sonuclar)} fırsat"
        bot.send_message(TELEGRAM_CHAT_ID, mesaj, parse_mode='HTML')
        return True
    except:
        return False

# ═══════════════════════════════════════════════════════════════
# ANA ARAYÜZ
# ═══════════════════════════════════════════════════════════════

st.markdown('<p class="big-font">🚀 KAZANCKAPISI - BIST Tarama v1.0</p>', unsafe_allow_html=True)
st.markdown("**✨ Colab Stratejileri Entegre | 📱 Telegram | 💾 Kayıt Sistemi**")

tab1, tab2, tab3 = st.tabs(["🔍 Tarama", "⚙️ Stratejiler", "📊 Sonuçlar"])

# TAB 1: TARAMA
with tab1:
    col1, col2, col3 = st.columns(3)
    with col1:
        period = st.selectbox("Period", ["1d", "5d", "1mo", "3mo", "6mo", "1y"], index=3)
        interval = st.selectbox("Interval", ["5m", "15m", "1h", "1d"], index=3)
    with col2:
        min_score = st.slider("Min Skor", 0, 100, 60, 5)
    with col3:
        stock_group = st.selectbox("Grup", list(BIST_STOCKS.keys()))
    
    selected_strategies = []
    st.markdown("### Stratejiler")
    for strat in st.session_state.strategies.keys():
        if st.checkbox(strat, key=f"sel_{strat}"):
            selected_strategies.append(strat)
        st.caption(st.session_state.strategies[strat]['desc'])
    
    if st.button("🚀 TARA", type="primary"):
        if not selected_strategies:
            st.error("❌ En az 1 strateji seç!")
        else:
            stocks = BIST_STOCKS[stock_group]
            progress = st.progress(0)
            results = []
            for idx, sym in enumerate(stocks):
                result = analyze_stock(sym, period, interval, selected_strategies, min_score)
                if result:
                    results.append(result)
                progress.progress((idx + 1) / len(stocks))
            progress.empty()
            st.session_state.results = sorted(results, key=lambda x: x['score'], reverse=True)
            st.session_state.tarama_gecmisi.append({'tarih': datetime.now(), 'sonuc_sayisi': len(results), 'stratejiler': selected_strategies})
            if results:
                st.success(f"🎉 {len(results)} fırsat!")
                telegram_gonder(results)
                df = pd.DataFrame([{'#': i, 'Hisse': r['symbol'], 'Skor': f"{r['score']:.0f}", 'Fiyat': f"₺{r['price']:.2f}", 
                                   'Hedef': f"₺{r['target']:.2f}", 'Pot%': f"%{r['potential']:.1f}"} 
                                  for i, r in enumerate(results, 1)])
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.warning("⚠️ Sinyal yok!")

# TAB 2: STRATEJİLER
with tab2:
    st.markdown("## Stratejiler")
    for name, data in st.session_state.strategies.items():
        with st.expander(name):
            st.markdown(f"**{data['desc']}**")
            st.code(data['code'], language='python')

# TAB 3: SONUÇLAR + GEÇMİŞ
with tab3:
    st.markdown("## 📊 Sonuçlar")
    if st.session_state.results:
        df = pd.DataFrame([{' #': i, 'Hisse': r['symbol'], 'Skor': f"{r['score']:.0f}", 'Fiyat': f"₺{r['price']:.2f}", 
                           'Hedef': f"₺{r['target']:.2f}", 'Potansiyel': f"%{r['potential']:.1f}"}
                          for i, r in enumerate(st.session_state.results, 1)])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Henüz tarama yapılmadı")
    
    st.markdown("### 📜 Tarama Geçmişi")
    if st.session_state.tarama_gecmisi:
        for idx, t in enumerate(reversed(st.session_state.tarama_gecmisi[-10:]), 1):
            st.markdown(f"{idx}. **{t['tarih'].strftime('%d.%m.%Y %H:%M')}** - {t['sonuc_sayisi']} sonuç - {len(t['stratejiler'])} strateji")
    else:
        st.info("Geçmiş yok")

with st.sidebar:
    st.metric("Stratejiler", len(st.session_state.strategies))
    st.metric("Son Tarama", len(st.session_state.results))
    st.markdown("---")
    st.success("✅ Colab Stratejileri Entegre!")
