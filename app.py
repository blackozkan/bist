# ═══════════════════════════════════════════════════════════════
# BIST PRO TRADING DASHBOARD v6.1
# ═══════════════════════════════════════════════════════════════

import sys
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import plotly.graph_objects as go
import time
from scipy.signal import argrelextrema

# ═══════════════════════════════════════════════════════════════
# SAYFA AYARLARI
# ═══════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="BIST Pro Trading v6.1",
    page_icon="🚀",
    layout="wide"
)

st.markdown("""
<style>
    .big-font {font-size:28px !important; font-weight:bold; color:#00ff87;}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════════

if 'results' not in st.session_state:
    st.session_state.results = []

if 'strategies' not in st.session_state:
    st.session_state.strategies = {
        "✅ Test Stratejisi": {
            "code": """def analyze(df):
    if len(df) < 1:
        return None
    current = df['Close'].iloc[-1]
    return {'score': 60, 'target': current * 1.05, 'reason': 'Test sinyali'}""",
            "desc": "Her zaman sinyal üretir"
        },
        
        "⚡ Kısa Vadeli Momentum": {
            "code": """def analyze(df):
    if len(df) < 10:
        return None
    change = ((df['Close'].iloc[-1] - df['Close'].iloc[-10]) / df['Close'].iloc[-10]) * 100
    last_3_up = all(df['Close'].iloc[i] > df['Close'].iloc[i-1] for i in range(-3, 0))
    if change > 1 and last_3_up:
        score = 55 + min(35, change * 10)
        return {'score': score, 'target': df['Close'].iloc[-1] * 1.02, 'reason': f'%{change:.1f} yükseliş'}
    return None""",
            "desc": "Kısa vadeli için (5-30dk)"
        },
        
        "⚡ İntraday Hacim": {
            "code": """def analyze(df):
    if len(df) < 20:
        return None
    vol_ma = df['Volume'].rolling(10).mean().iloc[-1]
    current_vol = df['Volume'].iloc[-1]
    if pd.isna(vol_ma) or vol_ma == 0:
        return None
    vol_ratio = current_vol / vol_ma
    price_change = ((df['Close'].iloc[-1] - df['Open'].iloc[-1]) / df['Open'].iloc[-1]) * 100
    if vol_ratio > 1.5 and price_change > 0.5:
        score = 60 + min(30, vol_ratio * 10)
        return {'score': score, 'target': df['Close'].iloc[-1] * 1.02, 'reason': f'Hacim {vol_ratio:.1f}x'}
    return None""",
            "desc": "Gün içi hacim patlaması"
        },
        
        "💹 2 Haftalık Güçlü Trend": {
            "code": """def analyze(df):
    if len(df) < 14:
        return None
    old_price = df['Close'].iloc[-14]
    current = df['Close'].iloc[-1]
    change = ((current - old_price) / old_price) * 100
    if change > 7:
        last_3_change = ((df['Close'].iloc[-1] - df['Close'].iloc[-3]) / df['Close'].iloc[-3]) * 100
        if last_3_change > 0:
            score = 60 + min(30, change * 2)
            return {'score': score, 'target': current * 1.06, 'reason': f'14 günde %{change:.1f}'}
    return None""",
            "desc": "2 haftada güçlü yükseliş"
        },
        
        "🎣 Dip Avı": {
            "code": """def analyze(df):
    if len(df) < 30:
        return None
    low_30 = df['Low'].tail(30).min()
    current = df['Close'].iloc[-1]
    rise_from_low = ((current - low_30) / low_30) * 100
    if 2 < rise_from_low < 8:
        if df['Close'].iloc[-1] > df['Close'].iloc[-2]:
            score = 65 + min(25, (8 - rise_from_low) * 3)
            return {'score': score, 'target': current * 1.12, 'reason': f'Dipten %{rise_from_low:.1f}'}
    return None""",
            "desc": "30 günlük dipten çıkanlar"
        },
        
        "📈 Yükseliş Trendi": {
            "code": """def analyze(df):
    if len(df) < 10:
        return None
    ma5 = df['Close'].rolling(5).mean().iloc[-1]
    ma10 = df['Close'].rolling(10).mean().iloc[-1]
    current = df['Close'].iloc[-1]
    if pd.isna(ma5) or pd.isna(ma10):
        return None
    if ma5 > ma10 and current >= ma5 * 0.98:
        score = 50 + min(40, (ma5/ma10 - 1) * 1000)
        return {'score': score, 'target': current * 1.04, 'reason': 'MA5 > MA10'}
    return None""",
            "desc": "MA kesişimi"
        },
        
        "💪 Momentum": {
            "code": """def analyze(df):
    if len(df) < 5:
        return None
    change = (df['Close'].iloc[-1] - df['Close'].iloc[-5]) / df['Close'].iloc[-5]
    if change > 0.01:
        score = 50 + min(40, change * 1000)
        return {'score': score, 'target': df['Close'].iloc[-1] * 1.05, 'reason': f'{change*100:.1f}% artış'}
    return None""",
            "desc": "5 günlük momentum"
        },
        
        "🎯 Basit Alım": {
            "code": """def analyze(df):
    if len(df) < 3:
        return None
    if df['Close'].iloc[-1] > df['Close'].iloc[-2]:
        return {'score': 55, 'target': df['Close'].iloc[-1] * 1.03, 'reason': 'Pozitif momentum'}
    return None""",
            "desc": "En basit sinyal"
        }
    }

# ═══════════════════════════════════════════════════════════════
# HİSSE LİSTESİ
# ═══════════════════════════════════════════════════════════════

BIST_STOCKS = {
    "BIST 30": [
        'THYAO', 'GARAN', 'AKBNK', 'ISCTR', 'YKBNK', 'SAHOL', 'KCHOL', 'EREGL',
        'TUPRS', 'PETKM', 'ASELS', 'SISE', 'TCELL', 'KOZAL', 'FROTO', 'BIMAS'
    ],
    "Popüler": [
        'THYAO', 'GARAN', 'AKBNK', 'TUPRS', 'PETKM', 'SISE', 'EREGL', 'ASELS'
    ],
    "Test Grubu": [
        'THYAO', 'GARAN', 'AKBNK', 'TUPRS', 'PETKM'
    ]
}

# ═══════════════════════════════════════════════════════════════
# FONKSİYONLAR
# ═══════════════════════════════════════════════════════════════

@st.cache_data(ttl=300)
def get_stock_data(symbol, period='3mo', interval='1d'):
    try:
        ticker = symbol.strip().upper()
        if not ticker.endswith('.IS'):
            ticker = f"{ticker}.IS"
        
        data = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
        
        if data.empty:
            return None
        
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        
        required = ['Open', 'High', 'Low', 'Close', 'Volume']
        data = data[required].dropna()
        
        if len(data) < 5:
            return None
        
        return data
    except:
        return None

def run_strategy(df, strategy_code):
    try:
        if df is None or len(df) < 1:
            return None
        
        namespace = {
            'df': df, 'pd': pd, 'np': np, 'len': len, 'min': min, 
            'max': max, 'abs': abs, 'all': all, 'argrelextrema': argrelextrema
        }
        
        exec(strategy_code, namespace)
        
        if 'analyze' not in namespace:
            return None
        
        result = namespace['analyze'](df)
        
        if result and isinstance(result, dict):
            if 'score' in result and 'target' in result:
                return result
        
        return None
    except:
        return None

def analyze_stock(symbol, period, interval, selected_strategies, min_score):
    df = get_stock_data(symbol, period, interval)
    
    if df is None:
        return None
    
    current_price = df['Close'].iloc[-1]
    signals = []
    
    for strategy_name in selected_strategies:
        if strategy_name not in st.session_state.strategies:
            continue
        
        code = st.session_state.strategies[strategy_name]['code']
        result = run_strategy(df, code)
        
        if result:
            signals.append({
                'name': strategy_name,
                'score': result['score'],
                'target': result['target'],
                'reason': result.get('reason', '')
            })
    
    if not signals:
        return None
    
    avg_score = sum(s['score'] for s in signals) / len(signals)
    
    if avg_score < min_score:
        return None
    
    max_target = max(s['target'] for s in signals)
    potential = ((max_target - current_price) / current_price) * 100
    
    return {
        'symbol': symbol,
        'price': current_price,
        'target': max_target,
        'potential': potential,
        'score': avg_score,
        'signals': signals,
        'signal_count': len(signals)
    }

# ═══════════════════════════════════════════════════════════════
# ANA ARAYÜZ
# ═══════════════════════════════════════════════════════════════

st.markdown('<p class="big-font">🚀 BIST PRO TRADING v6.1</p>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🔍 Tarama", "⚙️ Stratejiler", "📊 Sonuçlar"])

# ═══════════════════════════════════════════════════════════════
# TAB 1: TARAMA
# ═══════════════════════════════════════════════════════════════

with tab1:
    st.markdown("## 🎯 Hisse Tarama")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        time_preset = st.selectbox("Zaman", [
            "⚡ 5dk (1 gün)",
            "⚡ 15dk (5 gün)", 
            "⚡ 30dk (7 gün)",
            "📊 Günlük (3 ay)",
            "📅 Haftalık (1 yıl)"
        ])
        
        time_map = {
            "⚡ 5dk (1 gün)": ("1d", "5m"),
            "⚡ 15dk (5 gün)": ("5d", "15m"),
            "⚡ 30dk (7 gün)": ("7d", "30m"),
            "📊 Günlük (3 ay)": ("3mo", "1d"),
            "📅 Haftalık (1 yıl)": ("1y", "1wk")
        }
        
        period, interval = time_map[time_preset]
    
    with col2:
        min_score = st.slider("Min Skor", 0, 100, 50, 5)
    
    with col3:
        stock_group = st.selectbox("Grup", list(BIST_STOCKS.keys()))
        stocks_to_scan = BIST_STOCKS[stock_group]
    
    st.markdown("---")
    st.markdown("### 🎨 Strateji Seçimi")
    
    cols = st.columns(3)
    selected_strategies = []
    
    strategy_list = list(st.session_state.strategies.keys())
    
    if interval in ["5m", "15m", "30m"]:
        defaults = ["⚡ Kısa Vadeli Momentum", "⚡ İntraday Hacim", "🎯 Basit Alım"]
    else:
        defaults = ["💹 2 Haftalık Güçlü Trend", "🎣 Dip Avı", "📈 Yükseliş Trendi"]
    
    for idx, name in enumerate(strategy_list):
        with cols[idx % 3]:
            if st.checkbox(name, value=(name in defaults), key=f"s_{idx}"):
                selected_strategies.append(name)
    
    st.markdown("---")
    
    if st.button("🚀 TARAMAYI BAŞLAT", type="primary", use_container_width=True):
        if not selected_strategies:
            st.error("❌ En az 1 strateji seçin!")
        else:
            progress = st.progress(0)
            status = st.empty()
            
            results = []
            
            for idx, symbol in enumerate(stocks_to_scan):
                status.text(f"🔍 {symbol} ({idx+1}/{len(stocks_to_scan)})")
                
                result = analyze_stock(symbol, period, interval, selected_strategies, min_score)
                
                if result:
                    results.append(result)
                
                progress.progress((idx + 1) / len(stocks_to_scan))
                time.sleep(0.05)
            
            progress.empty()
            status.empty()
            
            if results:
                st.session_state.results = sorted(results, key=lambda x: x['score'], reverse=True)
                st.success(f"🎉 {len(results)} fırsat bulundu!")
                
                table_data = []
                for i, r in enumerate(st.session_state.results[:20], 1):
                    table_data.append({
                        '#': i,
                        'Hisse': r['symbol'],
                        'Skor': f"{r['score']:.0f}",
                        'Fiyat': f"₺{r['price']:.2f}",
                        'Hedef': f"₺{r['target']:.2f}",
                        'Potansiyel': f"%{r['potential']:.1f}"
                    })
                
                st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)
            else:
                st.warning("⚠️ Sinyal bulunamadı!")

# ═══════════════════════════════════════════════════════════════
# TAB 2: STRATEJİLER
# ═══════════════════════════════════════════════════════════════

with tab2:
    st.markdown("## ⚙️ Strateji Yönetimi")
    
    new_name = st.text_input("Strateji Adı")
    new_desc = st.text_input("Açıklama")
    
    template = st.selectbox("Şablon", ["Boş", "Basit Yükseliş", "MA Kesişimi"])
    
    templates = {
        "Boş": """def analyze(df):
    if len(df) < 5:
        return None
    return {'score': 60, 'target': df['Close'].iloc[-1] * 1.05, 'reason': 'Test'}""",
        
        "Basit Yükseliş": """def analyze(df):
    if len(df) < 3:
        return None
    if df['Close'].iloc[-1] > df['Close'].iloc[-2]:
        return {'score': 55, 'target': df['Close'].iloc[-1] * 1.03, 'reason': 'Yükseliş'}
    return None""",
        
        "MA Kesişimi": """def analyze(df):
    if len(df) < 20:
        return None
    ma10 = df['Close'].rolling(10).mean().iloc[-1]
    ma20 = df['Close'].rolling(20).mean().iloc[-1]
    if pd.isna(ma10) or pd.isna(ma20):
        return None
    if ma10 > ma20:
        return {'score': 65, 'target': df['Close'].iloc[-1] * 1.05, 'reason': 'MA10>MA20'}
    return None"""
    }
    
    new_code = st.text_area("Kod", value=templates[template], height=300)
    
    if st.button("💾 Kaydet", type="primary"):
        if new_name and new_code and new_desc:
            st.session_state.strategies[new_name] = {'code': new_code, 'desc': new_desc}
            st.success(f"✅ '{new_name}' kaydedildi!")
        else:
            st.error("❌ Tüm alanları doldurun!")
    
    st.markdown("---")
    st.markdown("### 📋 Kayıtlı Stratejiler")
    
    for name, data in st.session_state.strategies.items():
        with st.expander(name):
            st.caption(data['desc'])
            st.code(data['code'], language='python')

# ═══════════════════════════════════════════════════════════════
# TAB 3: SONUÇLAR
# ═══════════════════════════════════════════════════════════════

with tab3:
    st.markdown("## 📊 Tarama Sonuçları")
    
    if st.session_state.results:
        st.success(f"🎯 Toplam {len(st.session_state.results)} fırsat")
        
        result_table = []
        for i, r in enumerate(st.session_state.results, 1):
            result_table.append({
                '#': i,
                'Hisse': r['symbol'],
                'Skor': f"{r['score']:.0f}",
                'Fiyat': f"₺{r['price']:.2f}",
                'Hedef': f"₺{r['target']:.2f}",
                'Potansiyel': f"%{r['potential']:.1f}"
            })
        
        st.dataframe(pd.DataFrame(result_table), use_container_width=True, hide_index=True)
        
        # Grafik
        top_15 = st.session_state.results[:15]
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=[r['symbol'] for r in top_15],
            y=[r['potential'] for r in top_15],
            marker_color='lightgreen'
        ))
        fig.update_layout(title="En İyi 15 Fırsat", template="plotly_dark", height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📊 Henüz tarama yapılmadı")

# ═══════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("## 📊 Durum")
    st.metric("Stratejiler", len(st.session_state.strategies))
    st.metric("Fırsatlar", len(st.session_state.results))
    
    st.markdown("---")
    st.markdown("### 🚀 v6.1")
    st.markdown("✅ Kısa vadeli düzeltildi")
    st.markdown("✅ Syntax hataları giderildi")
    
    st.markdown("---")
    st.warning("⚠️ Eğitim amaçlıdır")

st.markdown("---")
st.markdown("<div style='text-align:center'>BIST Pro Trading v6.1</div>", unsafe_allow_html=True)
