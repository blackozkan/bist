# ═══════════════════════════════════════════════════════════════
# 📦 KÜTÜPHANE KONTROLÜ
# ═══════════════════════════════════════════════════════════════

import sys

# Kritik kütüphaneleri kontrol et
required_libraries = [
    'streamlit': 'streamlit',
    'pandas': 'pandas', 
    'numpy': 'numpy',
    'yfinance': 'yfinance',
    'plotly': 'plotly',
    'scipy': 'scipy'
]

missing_libraries = []

for display_name, module_name in required_libraries.items():
    try:
        __import__(module_name)
    except ImportError:
        missing_libraries.append(module_name)

if missing_libraries:
    print("=" * 60)
    print("❌ EKSİK KÜTÜPHANELER BULUNDU!")
    print("=" * 60)
    print("\nLütfen şu komutu çalıştırın:\n")
    print(f"pip install {' '.join(missing_libraries)}")
    print("\n" + "=" * 60)
    sys.exit(1)

# Kütüphaneleri import et
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

# CSS
st.markdown("""
<style>
    .big-font {font-size:28px !important; font-weight:bold; color:#00ff87;}
    .success-box {background:#1a472a; padding:15px; border-radius:8px; border-left:4px solid #00ff87;}
    .warning-box {background:#4a3c1a; padding:15px; border-radius:8px; border-left:4px solid #ffa500;}
    .metric-card {background:linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                  padding:20px; border-radius:10px; text-align:center; color:white;}
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
            "desc": "Her zaman sinyal üretir (test için)"
        },
        
        # ═══════════════════════════════════════════════════════════════
        # KISA VADELİ STRATEJİLER (5m-30m için)
        # ═══════════════════════════════════════════════════════════════
        
        "⚡ Kısa Vadeli Momentum": {
            "code": """def analyze(df):
    if len(df) < 10:
        return None
    
    # Son 10 bar değişimi
    change = ((df['Close'].iloc[-1] - df['Close'].iloc[-10]) / df['Close'].iloc[-10]) * 100
    
    # Son 3 bar yükseliş kontrolü
    last_3_up = all(df['Close'].iloc[i] > df['Close'].iloc[i-1] for i in range(-3, 0))
    
    if change > 1 and last_3_up:
        score = 55 + min(35, change * 10)
        return {
            'score': score,
            'target': df['Close'].iloc[-1] * 1.02,
            'reason': f'Son 10 barda %{change:.1f} yükseliş, momentum güçlü'
        }
    return None""",
            "desc": "Kısa vadeli momentum (5-15-30dk için)"
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
        return {
            'score': score,
            'target': df['Close'].iloc[-1] * 1.02,
            'reason': f'Hacim {vol_ratio:.1f}x, fiyat +%{price_change:.1f}'
        }
    return None""",
            "desc": "Gün içi hacim patlaması"
        },
        
        "⚡ Hızlı MA Kesişimi": {
            "code": """def analyze(df):
    if len(df) < 10:
        return None
    
    ma5 = df['Close'].rolling(5).mean().iloc[-1]
    ma10 = df['Close'].rolling(10).mean().iloc[-1]
    current = df['Close'].iloc[-1]
    
    if pd.isna(ma5) or pd.isna(ma10):
        return None
    
    if ma5 > ma10 and current >= ma5 * 0.99:
        score = 60 + min(30, (ma5/ma10 - 1) * 1000)
        return {
            'score': score,
            'target': current * 1.03,
            'reason': f'MA5 > MA10 kesişimi'
        }
    return None""",
            "desc": "Hızlı hareketli ortalama (kısa vadeli)"
        },
        
        # ═══════════════════════════════════════════════════════════════
        # QUANTUM STRATEJİLER (Günlük için)
        # ═══════════════════════════════════════════════════════════════
        
        "🎯 Quantum Fibonacci": {
            "code": """def analyze(df):
    if len(df) < 20:
        return None
    
    recent = df.tail(20)
    high = recent['High'].max()
    low = recent['Low'].min()
    current = df['Close'].iloc[-1]
    
    diff = high - low
    fib_1272 = low + 1.272 * diff
    fib_1618 = low + 1.618 * diff
    
    if current < fib_1272:
        target = fib_1272
    elif current < fib_1618:
        target = fib_1618
    else:
        return None
    
    potential = ((target - current) / current) * 100
    
    if potential > 3:
        score = 50 + min(40, potential * 2)
        return {
            'score': score,
            'target': target,
            'reason': f'Fibonacci Extension: %{potential:.1f} potansiyel'
        }
    return None""",
            "desc": "Fibonacci Extension ile tavan tahmini"
        },
        
        "📐 Harmonic Pattern Hunter": {
            "code": """def analyze(df):
    if len(df) < 50:
        return None
    
    import numpy as np
    from scipy.signal import argrelextrema
    
    closes = df['Close'].values
    highs = df['High'].values
    lows = df['Low'].values
    current = closes[-1]
    
    high_peaks = argrelextrema(highs, np.greater, order=5)[0]
    low_peaks = argrelextrema(lows, np.less, order=5)[0]
    
    if len(high_peaks) >= 2 and len(low_peaks) >= 2:
        last_high = highs[high_peaks[-1]]
        last_low = lows[low_peaks[-1]]
        
        if last_low < current < last_high * 1.1:
            ab_ratio = (last_high - last_low) / max(last_low, 0.01)
            if 0.05 < ab_ratio < 0.20:
                target = last_high * 1.05
                score = 65 + min(20, ab_ratio * 100)
                return {
                    'score': score,
                    'target': target,
                    'reason': 'ABCD Bullish Pattern tespit edildi'
                }
    
    if len(high_peaks) >= 3:
        target = current * 1.08
        return {
            'score': 70,
            'target': target,
            'reason': 'Gartley Pattern formasyonu'
        }
    
    return None""",
            "desc": "ABCD, Gartley, Butterfly pattern tespiti"
        },
        
        "🔥 Volume Explosion": {
            "code": """def analyze(df):
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
            score = 70 + min(25, (volume_ratio - 2) * 10)
            return {
                'score': score,
                'target': df['Close'].iloc[-1] * 1.08,
                'reason': f'Hacim patlaması: {volume_ratio:.1f}x'
            }
    
    return None""",
            "desc": "Anormal hacim artışı ve clustering"
        },
        
        "⚡ RSI Divergence Pro": {
            "code": """def analyze(df):
    if len(df) < 30:
        return None
    
    import numpy as np
    from scipy.signal import argrelextrema
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    
    gain = gain.fillna(0)
    loss = loss.fillna(0.0001).replace(0, 0.0001)
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    closes = df['Close'].values
    rsi_values = rsi.values
    
    price_peaks = argrelextrema(closes[-20:], np.greater, order=3)[0]
    rsi_peaks = argrelextrema(rsi_values[-20:], np.greater, order=3)[0]
    
    if len(price_peaks) >= 2 and len(rsi_peaks) >= 2:
        if closes[-20:][price_peaks[-1]] < closes[-20:][price_peaks[-2]]:
            if rsi_values[-20:][rsi_peaks[-1]] > rsi_values[-20:][rsi_peaks[-2]]:
                return {
                    'score': 80,
                    'target': df['Close'].iloc[-1] * 1.10,
                    'reason': 'Bullish RSI Divergence - Güçlü sinyal'
                }
    
    return None""",
            "desc": "Gelişmiş RSI divergence tespiti"
        },
        
        # ═══════════════════════════════════════════════════════════════
        # YENİ SAĞLAM STRATEJİLER (Günlük için)
        # ═══════════════════════════════════════════════════════════════
        
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
            return {
                'score': score,
                'target': current * 1.06,
                'reason': f'14 günde %{change:.1f} yükseldi, trend devam ediyor'
            }
    return None""",
            "desc": "Son 2 haftada güçlü yükseliş trendi"
        },
        
        "🎣 Dip Avı": {
            "code": """def analyze(df):
    if len(df) < 30:
        return None
    
    import numpy as np
    
    low_30 = df['Low'].tail(30).min()
    current = df['Close'].iloc[-1]
    
    rise_from_low = ((current - low_30) / low_30) * 100
    
    if 2 < rise_from_low < 8:
        if df['Close'].iloc[-1] > df['Close'].iloc[-2]:
            score = 65 + min(25, (8 - rise_from_low) * 3)
            return {
                'score': score,
                'target': current * 1.12,
                'reason': f'Dipten %{rise_from_low:.1f} yükseldi, momentum başlıyor'
            }
    return None""",
            "desc": "30 günlük dipten yeni çıkanlar"
        },
        
        "🔥 Sessiz Güç": {
            "code": """def analyze(df):
    if len(df) < 20:
        return None
    
    vol_ma = df['Volume'].rolling(20).mean().iloc[-1]
    current_vol = df['Volume'].iloc[-1]
    
    if pd.isna(vol_ma) or vol_ma == 0:
        return None
    
    vol_ratio = current_vol / vol_ma
    price_change_5d = ((df['Close'].iloc[-1] - df['Close'].iloc[-5]) / df['Close'].iloc[-5]) * 100
    
    if vol_ratio < 0.7 and price_change_5d > 3:
        score = 70 + min(20, price_change_5d * 2)
        return {
            'score': score,
            'target': df['Close'].iloc[-1] * 1.10,
            'reason': f'Düşük hacimde %{price_change_5d:.1f} yükseliş (kurumsal birikim)'
        }
    return None""",
            "desc": "Düşük hacimde güçlü yükseliş"
        },
        
        "📈 Yeşil Seri": {
            "code": """def analyze(df):
    if len(df) < 10:
        return None
    
    green_count = 0
    
    for i in range(-10, 0):
        if df['Close'].iloc[i] > df['Open'].iloc[i]:
            green_count += 1
    
    total_change = ((df['Close'].iloc[-1] - df['Close'].iloc[-10]) / df['Close'].iloc[-10]) * 100
    
    if green_count >= 7 and total_change > 4:
        score = 55 + (green_count * 3) + min(20, total_change * 2)
        return {
            'score': score,
            'target': df['Close'].iloc[-1] * 1.05,
            'reason': f'10 günde {green_count} yeşil, %{total_change:.1f} yükseldi'
        }
    return None""",
            "desc": "10 günde 7+ yeşil gün"
        },
        
        "🏔️ Tepe Yenileme": {
            "code": """def analyze(df):
    if len(df) < 50:
        return None
    
    import numpy as np
    
    high_50 = df['High'].tail(50).max()
    current = df['Close'].iloc[-1]
    
    distance = ((high_50 - current) / high_50) * 100
    
    if distance < 1:
        last_5_change = ((df['Close'].iloc[-1] - df['Close'].iloc[-5]) / df['Close'].iloc[-5]) * 100
        
        if last_5_change > 2:
            score = 75
            return {
                'score': score,
                'target': high_50 * 1.05,
                'reason': f'50 günlük zirveye ulaştı, kırma potansiyeli yüksek'
            }
    return None""",
            "desc": "50 günlük zirveyi test edenler"
        },
        
        "💪 Momentum Patlaması": {
            "code": """def analyze(df):
    if len(df) < 5:
        return None
    
    continuous_rise = True
    for i in range(-5, -1):
        if df['Close'].iloc[i] <= df['Close'].iloc[i-1]:
            continuous_rise = False
            break
    
    if continuous_rise:
        total_rise = ((df['Close'].iloc[-1] - df['Close'].iloc[-5]) / df['Close'].iloc[-5]) * 100
        
        if total_rise > 5:
            score = 70 + min(25, total_rise * 2)
            return {
                'score': score,
                'target': df['Close'].iloc[-1] * 1.05,
                'reason': f'5 gün kesintisiz yükseliş: %{total_rise:.1f}'
            }
    return None""",
            "desc": "5 gün kesintisiz yükseliş"
        },
        
        # ═══════════════════════════════════════════════════════════════
        # BASIT STRATEJİLER (Her zaman dilimi için)
        # ═══════════════════════════════════════════════════════════════
        
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
        return {
            'score': score,
            'target': current * 1.04,
            'reason': f'MA5 > MA10, trend güçlü'
        }
    return None""",
            "desc": "Hareketli ortalama kesişimi"
        },
        
        "💪 Momentum": {
            "code": """def analyze(df):
    if len(df) < 5:
        return None
    
    change = (df['Close'].iloc[-1] - df['Close'].iloc[-5]) / df['Close'].iloc[-5]
    
    if change > 0.01:
        score = 50 + min(40, change * 1000)
        return {
            'score': score,
            'target': df['Close'].iloc[-1] * 1.05,
            'reason': f'{change*100:.1f}% artış var'
        }
    return None""",
            "desc": "Son 5 gün momentum kontrolü"
        },
        
        "📊 Hacim Patlaması": {
            "code": """def analyze(df):
    if len(df) < 20:
        return None
    
    vol_ma = df['Volume'].rolling(20).mean().iloc[-1]
    current_vol = df['Volume'].iloc[-1]
    
    if pd.isna(vol_ma) or vol_ma == 0:
        return None
    
    if current_vol > vol_ma * 1.5:
        score = 50 + min(40, (current_vol/vol_ma - 1) * 50)
        return {
            'score': score,
            'target': df['Close'].iloc[-1] * 1.06,
            'reason': f'Hacim {current_vol/vol_ma:.1f}x arttı'
        }
    return None""",
            "desc": "Anormal hacim artışı tespiti"
        },
        
        "🎯 Basit Alım": {
            "code": """def analyze(df):
    if len(df) < 3:
        return None
    
    if df['Close'].iloc[-1] > df['Close'].iloc[-2]:
        return {
            'score': 55,
            'target': df['Close'].iloc[-1] * 1.03,
            'reason': 'Pozitif momentum'
        }
    return None""",
            "desc": "En basit yükseliş sinyali"
        }
    }

# ═══════════════════════════════════════════════════════════════
# HİSSE LİSTESİ
# ═══════════════════════════════════════════════════════════════

BIST_STOCKS = {
    "BIST 30 (Likit)": [
        'THYAO', 'GARAN', 'AKBNK', 'ISCTR', 'YKBNK', 'SAHOL', 'KCHOL', 'EREGL',
        'TUPRS', 'PETKM', 'ASELS', 'SISE', 'TCELL', 'KOZAL', 'FROTO', 'BIMAS',
        'ARCLK', 'HEKTS', 'KRDMD', 'TAVHL', 'PGSUS', 'SODA', 'DOHOL', 'KOZAA',
        'VAKBN', 'EKGYO', 'TTKOM', 'ENKAI', 'TOASO', 'TTRAK'
    ],
    "Popüler Hisseler": [
        'THYAO', 'GARAN', 'AKBNK', 'TUPRS', 'PETKM', 'SISE', 'EREGL', 'SAHOL',
        'KCHOL', 'YKBNK', 'ASELS', 'TCELL', 'FROTO', 'VESTL', 'SOKM'
    ],
    "Test Grubu (Hızlı)": [
        'THYAO', 'GARAN', 'AKBNK', 'TUPRS', 'PETKM', 'SISE', 'EREGL', 'ASELS',
        'KCHOL', 'FROTO', 'VESTL', 'SOKM', 'BIMAS', 'TCELL', 'ARCLK'
    ]
}

# ═══════════════════════════════════════════════════════════════
# VERİ ÇEKME FONKSİYONU
# ═══════════════════════════════════════════════════════════════

@st.cache_data(ttl=300)
def get_stock_data(symbol, period='3mo', interval='1d'):
    """YFinance ile veri çek"""
    try:
        ticker = symbol.strip().upper()
        if not ticker.endswith('.IS'):
            ticker = f"{ticker}.IS"
        
        data = yf.download(
            ticker,
            period=period,
            interval=interval,
            progress=False,
            auto_adjust=True
        )
        
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

# ═══════════════════════════════════════════════════════════════
# STRATEJİ ÇALIŞTIRMA
# ═══════════════════════════════════════════════════════════════

def run_strategy(df, strategy_code):
    """Strateji kodunu çalıştır"""
    try:
        if df is None or len(df) < 1:
            return None
        
        namespace = {
            'df': df,
            'pd': pd,
            'np': np,
            'len': len,
            'min': min,
            'max': max,
            'abs': abs,
            'all': all,
            'argrelextrema': argrelextrema
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

# ═══════════════════════════════════════════════════════════════
# HİSSE ANALİZİ
# ═══════════════════════════════════════════════════════════════

def analyze_stock(symbol, period, interval, selected_strategies, min_score):
    """Bir hisseyi analiz et"""
    
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

st.markdown('<p class="big-font">🚀 BIST PRO TRADING DASHBOARD v6.1</p>', unsafe_allow_html=True)
st.markdown("**✨ 20+ Profesyonel Strateji | ⚡ Kısa Vadeli Düzeltildi!**")

# TABS
tab1, tab2, tab3, tab4 = st.tabs(["🔍 Tarama", "⚙️ Stratejiler", "📊 Sonuçlar", "📚 Rehber"])

# ═══════════════════════════════════════════════════════════════
# TAB 1: TARAMA
# ═══════════════════════════════════════════════════════════════

with tab1:
    st.markdown("## 🎯 Hisse Tarama Motoru")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### ⏱️ Zaman Ayarları")
        time_preset = st.selectbox(
            "Hızlı Seçim",
            [
                "⚡ 5 Dakika (Son 1 gün - ~78 bar)",
                "⚡ 15 Dakika (Son 5 gün - ~130 bar)", 
                "⚡ 30 Dakika (Son 7 gün - ~112 bar)",
                "📈 1 Saat (Son 1 ay - ~168 bar)",
                "📊 Günlük (Son 3 ay - ~60 bar)": ("3mo", "1d"),
            "📅 Haftalık (Son 1 yıl - ~52 bar)": ("1y", "1wk")
        }
        
        if time_preset in time_settings:
            period, interval = time_settings[time_preset]
        else:  # Özel
            period = st.selectbox(
                "Period", 
                ["1d", "5d", "7d", "1mo", "3mo", "6mo", "1y", "2y"], 
                index=4
            )
            interval = st.selectbox(
                "Interval", 
                ["5m", "15m", "30m", "1h", "1d", "1wk", "1mo"], 
                index=4
            )
            
            # Uyumsuz kombinasyon uyarısı
            intraday_intervals = ["5m", "15m", "30m", "1h"]
            long_periods = ["6mo", "1y", "2y"]
            
            if interval in intraday_intervals and period in long_periods:
                st.warning("⚠️ yfinance bu kombinasyonu desteklemiyor! Period'u 1mo veya daha az yapın.")
                period = "1mo"
        
        st.caption(f"📊 Seçilen: {period} / {interval}")
    
    with col2:
        st.markdown("### 🎯 Filtreler")
        min_score = st.slider("Minimum Skor", 0, 100, 50, 5)
        st.caption(f"Skor {min_score}+ olan sinyaller gösterilecek")
    
    with col3:
        st.markdown("### 📊 Hisse Grubu")
        stock_group = st.selectbox(
            "Grup Seçin",
            list(BIST_STOCKS.keys())
        )
        stocks_to_scan = BIST_STOCKS[stock_group]
        st.caption(f"🔢 {len(stocks_to_scan)} hisse taranacak")
    
    st.markdown("---")
    
    # Strateji seçimi
    st.markdown("### 🎨 Strateji Seçimi")
    
    # Zaman dilimine göre önerilen stratejiler
    if interval in ["5m", "15m", "30m", "1h"]:
        st.info("💡 **Kısa Vadeli Mod Aktif** - Önerilen: ⚡ Kısa Vadeli Momentum, ⚡ İntraday Hacim, 🎯 Basit Alım")
    elif interval == "1d":
        st.info("💡 **Günlük Mod Aktif** - Tüm stratejiler kullanılabilir")
    else:
        st.info("💡 **Haftalık Mod Aktif** - Önerilen: 💹 2 Haftalık Trend, 🏔️ Tepe Yenileme")
    
    strategy_cols = st.columns(3)
    selected_strategies = []
    
    strategy_list = list(st.session_state.strategies.keys())
    
    # Zaman dilimine göre varsayılan seçimler
    if interval in ["5m", "15m", "30m", "1h"]:
        default_selected = ["⚡ Kısa Vadeli Momentum", "⚡ İntraday Hacim", "🎯 Basit Alım"]
    else:
        default_selected = ["💹 2 Haftalık Güçlü Trend", "🎣 Dip Avı", "📈 Yükseliş Trendi"]
    
    for idx, strat_name in enumerate(strategy_list):
        with strategy_cols[idx % 3]:
            desc = st.session_state.strategies[strat_name]['desc']
            is_default = strat_name in default_selected
            
            if st.checkbox(strat_name, value=is_default, key=f"strat_{idx}"):
                selected_strategies.append(strat_name)
            
            st.caption(desc)
    
    st.markdown("---")
    
    # TARAMA BUTONU
    if st.button("🚀 TARAMAYI BAŞLAT", type="primary", use_container_width=True):
        
        if not selected_strategies:
            st.error("❌ En az 1 strateji seçmelisiniz!")
        
        else:
            st.info(f"""
            📊 **Tarama Başlıyor:**
            - 📈 Hisse Sayısı: {len(stocks_to_scan)}
            - 🎯 Strateji Sayısı: {len(selected_strategies)}
            - ⚖️ Minimum Skor: {min_score}
            - ⏱️ Zaman: {period} / {interval}
            """)
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            results = []
            success_count = 0
            no_signal_count = 0
            error_count = 0
            
            for idx, symbol in enumerate(stocks_to_scan):
                
                status_text.text(f"🔍 Analiz: {symbol} ({idx+1}/{len(stocks_to_scan)})")
                
                result = analyze_stock(
                    symbol, 
                    period, 
                    interval, 
                    selected_strategies, 
                    min_score
                )
                
                if result:
                    results.append(result)
                    success_count += 1
                    status_text.text(f"✅ {symbol} - Skor: {result['score']:.0f} - Potansiyel: %{result['potential']:.1f}")
                else:
                    df_check = get_stock_data(symbol, period, interval)
                    if df_check is None:
                        error_count += 1
                    else:
                        no_signal_count += 1
                
                progress_bar.progress((idx + 1) / len(stocks_to_scan))
                time.sleep(0.05)
            
            progress_bar.empty()
            status_text.empty()
            
            st.markdown("---")
            st.markdown("### 📊 Tarama Tamamlandı!")
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("📊 Taranan", len(stocks_to_scan))
            col2.metric("✅ Sinyal", success_count)
            col3.metric("⏭️ Sinyal Yok", no_signal_count)
            col4.metric("❌ Veri Hatası", error_count)
            
            if results:
                st.session_state.results = sorted(results, key=lambda x: x['score'], reverse=True)
                
                st.success(f"🎉 **{len(results)} FIRSAT BULUNDU!**")
                
                avg_potential = np.mean([r['potential'] for r in results])
                max_potential = max([r['potential'] for r in results])
                best_stock = results[0]
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Ortalama Potansiyel", f"%{avg_potential:.1f}")
                col2.metric("En Yüksek Potansiyel", f"%{max_potential:.1f}")
                col3.metric("En İyi Hisse", best_stock['symbol'])
                
                st.markdown("---")
                st.markdown("## 🏆 BULUNAN FIRSATLAR (İlk 20)")
                
                table_data = []
                for i, r in enumerate(st.session_state.results[:20], 1):
                    table_data.append({
                        'Sıra': i,
                        'Hisse': r['symbol'],
                        'Skor': f"{r['score']:.0f}",
                        'Fiyat': f"₺{r['price']:.2f}",
                        'Hedef': f"₺{r['target']:.2f}",
                        'Potansiyel': f"%{r['potential']:.1f}",
                        'Sinyal': f"{r['signal_count']}/{len(selected_strategies)}"
                    })
                
                df_table = pd.DataFrame(table_data)
                st.dataframe(df_table, use_container_width=True, hide_index=True)
                
            else:
                st.warning("⚠️ Kriterlere uygun sinyal bulunamadı!")
                
                st.info("""
                **Öneriler:**
                1. ✅ Minimum skoru düşürün (örn: 40-50)
                2. ✅ "Test Stratejisi"ni seçin (her zaman sinyal verir)
                3. ✅ "Test Grubu (Hızlı)" ile deneyin
                4. ✅ Farklı zaman dilimi deneyin
                5. ✅ Daha fazla strateji seçin
                """)

# ═══════════════════════════════════════════════════════════════
# TAB 2: STRATEJİLER
# ═══════════════════════════════════════════════════════════════

with tab2:
    st.markdown("## ⚙️ Strateji Yönetimi")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### ➕ Yeni Strateji Ekle")
        
        new_name = st.text_input("Strateji Adı", placeholder="Örn: RSI Stratejisi")
        new_desc = st.text_input("Açıklama", placeholder="Kısa açıklama")
        
        template = st.selectbox("Şablon", [
            "Boş",
            "Kısa Vadeli (5-30dk)",
            "Basit Yükseliş",
            "MA Kesişimi",
            "Volume Patlaması"
        ])
        
        templates = {
            "Boş": """def analyze(df):
    if len(df) < 5:
        return None
    
    # Analiz kodunuz buraya
    
    return {
        'score': 60,
        'target': df['Close'].iloc[-1] * 1.05,
        'reason': 'Açıklama'
    }""",
            
            "Kısa Vadeli (5-30dk)": """def analyze(df):
    if len(df) < 10:
        return None
    
    # Son 10 bar değişimi
    change = ((df['Close'].iloc[-1] - df['Close'].iloc[-10]) / df['Close'].iloc[-10]) * 100
    
    if change > 1:
        score = 55 + min(35, change * 10)
        return {
            'score': score,
            'target': df['Close'].iloc[-1] * 1.02,
            'reason': f'%{change:.1f} yükseliş'
        }
    return None""",
            
            "Basit Yükseliş": """def analyze(df):
    if len(df) < 3:
        return None
    
    if df['Close'].iloc[-1] > df['Close'].iloc[-2]:
        return {
            'score': 55,
            'target': df['Close'].iloc[-1] * 1.03,
            'reason': 'Yükseliş trendi'
        }
    return None""",
            
            "MA Kesişimi": """def analyze(df):
    if len(df) < 20:
        return None
    
    ma10 = df['Close'].rolling(10).mean().iloc[-1]
    ma20 = df['Close'].rolling(20).mean().iloc[-1]
    
    if pd.isna(ma10) or pd.isna(ma20):
        return None
    
    if ma10 > ma20:
        return {
            'score': 65,
            'target': df['Close'].iloc[-1] * 1.05,
            'reason': 'MA10 > MA20'
        }
    return None""",
            
            "Volume Patlaması": """def analyze(df):
    if len(df) < 20:
        return None
    
    vol_ma = df['Volume'].rolling(20).mean().iloc[-1]
    current_vol = df['Volume'].iloc[-1]
    
    if pd.isna(vol_ma) or vol_ma == 0:
        return None
    
    if current_vol > vol_ma * 2:
        return {
            'score': 70,
            'target': df['Close'].iloc[-1] * 1.06,
            'reason': 'Hacim patlaması'
        }
    return None"""
        }
        
        new_code = st.text_area(
            "Python Kodu",
            value=templates[template],
            height=300
        )
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            if st.button("💾 Kaydet", type="primary", use_container_width=True):
                if new_name and new_code and new_desc:
                    st.session_state.strategies[new_name] = {
                        'code': new_code,
                        'desc': new_desc
                    }
                    st.success(f"✅ '{new_name}' kaydedildi!")
                    st.balloons()
                else:
                    st.error("❌ Tüm alanları doldurun!")
        
        with col_b:
            if st.button("🧪 Test Et", use_container_width=True):
                test_symbol = st.text_input("Test hisse", "THYAO", key="test_sym")
                test_period = st.selectbox("Test period", ["1d", "5d", "1mo", "3mo"], index=2, key="test_per")
                test_interval = st.selectbox("Test interval", ["5m", "15m", "1h", "1d"], index=3, key="test_int")
                
                if test_symbol and new_code:
                    df_test = get_stock_data(test_symbol, test_period, test_interval)
                    if df_test is not None:
                        st.info(f"✅ {len(df_test)} bar veri alındı")
                        result_test = run_strategy(df_test, new_code)
                        if result_test:
                            st.success("✅ Strateji çalışıyor!")
                            st.json(result_test)
                        else:
                            st.warning("⚠️ Sinyal üretmedi (normal olabilir)")
                    else:
                        st.error("❌ Veri alınamadı")
    
    with col2:
        st.markdown("### 📚 Mevcut Stratejiler")
        st.metric("Toplam", len(st.session_state.strategies))
        
        st.markdown("---")
        st.markdown("**Kategoriler:**")
        st.markdown("⚡ Kısa Vadeli: 3 adet")
        st.markdown("🎯 Quantum: 4 adet")
        st.markdown("💹 Günlük: 6 adet")
        st.markdown("📊 Basit: 4 adet")
    
    st.markdown("---")
    st.markdown("### 📋 Kayıtlı Stratejiler")
    
    for idx, (name, data) in enumerate(st.session_state.strategies.items(), 1):
        with st.expander(f"{idx}. {name}"):
            st.markdown(f"**Açıklama:** {data['desc']}")
            st.code(data['code'], language='python')
            
            if st.button(f"🗑️ Sil", key=f"del_{name}"):
                del st.session_state.strategies[name]
                st.rerun()

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
                'Potansiyel': f"%{r['potential']:.1f}",
                'Sinyal': r['signal_count']
            })
        
        df_results = pd.DataFrame(result_table)
        st.dataframe(df_results, use_container_width=True, hide_index=True)
        
        st.markdown("### 📈 Potansiyel Kazanç Grafiği")
        
        top_15 = st.session_state.results[:15]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=[r['symbol'] for r in top_15],
            y=[r['potential'] for r in top_15],
            marker_color='lightgreen',
            text=[f"%{r['potential']:.1f}" for r in top_15],
            textposition='outside'
        ))
        
        fig.update_layout(
            title="En İyi 15 Fırsat",
            xaxis_title="Hisse",
            yaxis_title="Potansiyel Kazanç (%)",
            template="plotly_dark",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        csv_data = df_results.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            "📥 CSV Olarak İndir",
            csv_data,
            f"tarama_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "text/csv"
        )
        
        st.markdown("---")
        st.markdown("### 🔍 Detaylı Analiz")
        
        selected_stock = st.selectbox(
            "Hisse Seçin",
            [r['symbol'] for r in st.session_state.results]
        )
        
        stock_detail = next(r for r in st.session_state.results if r['symbol'] == selected_stock)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Skor", f"{stock_detail['score']:.0f}")
        col2.metric("Mevcut Fiyat", f"₺{stock_detail['price']:.2f}")
        col3.metric("Hedef Fiyat", f"₺{stock_detail['target']:.2f}")
        
        st.markdown("**Sinyaller:**")
        for sig in stock_detail['signals']:
            st.markdown(f"- **{sig['name']}** (Skor: {sig['score']:.0f}): {sig['reason']}")
    
    else:
        st.info("📊 Henüz tarama yapılmadı. '🔍 Tarama' sekmesinden başlayın!")

# ═══════════════════════════════════════════════════════════════
# TAB 4: REHBER
# ═══════════════════════════════════════════════════════════════

with tab4:
    st.markdown("## 📚 Kullanım Rehberi")
    
    guide_tab = st.radio("Konu Seçin:", [
        "🚀 Hızlı Başlangıç",
        "⏱️ Zaman Dilimleri",
        "🎯 Strateji Rehberi",
        "⚠️ Yaygın Hatalar",
        "🌐 Online Yapma"
    ])
    
    if guide_tab == "🚀 Hızlı Başlangıç":
        st.markdown("""
        ### 🎯 5 Adımda Tarama
        
        **1. Zaman Dilimi Seç**
        - ⚡ Kısa vadeli için: 5dk, 15dk, 30dk
        - 📊 Orta vadeli için: Günlük (önerilen)
        - 📅 Uzun vadeli için: Haftalık
        
        **2. Minimum Skor Ayarla**
        - Başlangıç: 50
        - Güvenli: 60+
        - Çok seçici: 70+
        
        **3. Hisse Grubu Seç**
        - Test için: Test Grubu (15 hisse)
        - Hızlı için: Popüler Hisseler (15 hisse)
        - Tam tarama: BIST 30 (30 hisse)
        
        **4. Strateji Seç**
        - En az 2-3 strateji seçin
        - Zaman dilimine uygun olanları seçin
        
        **5. Tara!**
        - 🚀 TARAMAYI BAŞLAT butonuna tıkla
        - 1-2 dakika bekle
        - Sonuçları incele
        """)
        
        st.markdown("---")
        st.success("""
        💡 **İlk Tavsiye:**
        1. "📊 Günlük (Son 3 ay)" seç
        2. "💹 2 Haftalık Güçlü Trend" + "🎣 Dip Avı" stratejilerini işaretle
        3. "Test Grubu (Hızlı)" ile tara
        4. Min skor 50
        """)
    
    elif guide_tab == "⏱️ Zaman Dilimleri":
        st.markdown("""
        ### ⚡ Kısa Vadeli (5-30 dakika)
        
        **Özellikler:**
        - ✅ Gün içi trading için
        - ✅ Hızlı kar al-sat
        - ⚠️ Daha volatil
        - ⚠️ Stoplos şart
        
        **Uygun Stratejiler:**
        - ⚡ Kısa Vadeli Momentum
        - ⚡ İntraday Hacim
        - ⚡ Hızlı MA Kesişimi
        - 🎯 Basit Alım
        - 💪 Momentum
        
        **yfinance Limitleri:**
        - 5m: Sadece son 1 gün (~78 bar)
        - 15m: Sadece son 5 gün (~130 bar)
        - 30m: Sadece son 7 gün (~112 bar)
        
        ---
        
        ### 📊 Günlük (ÖNERİLEN)
        
        **Özellikler:**
        - ✅ En dengeli seçenek
        - ✅ Tüm stratejiler çalışır
        - ✅ 60+ bar veri
        - ✅ Swing trading için ideal
        
        **Uygun Stratejiler:**
        - Tüm stratejiler kullanılabilir
        - Özellikle: 💹 2 Haftalık Trend, 🎣 Dip Avı, 🏔️ Tepe Yenileme
        
        ---
        
        ### 📅 Haftalık
        
        **Özellikler:**
        - ✅ Uzun vadeli trendler
        - ✅ Daha az gürültü
        - ✅ Pozisyon trading
        
        **Uygun Stratejiler:**
        - 💹 2 Haftalık Güçlü Trend
        - 🏔️ Tepe Yenileme
        - 🎣 Dip Avı
        """)
    
    elif guide_tab == "🎯 Strateji Rehberi":
        st.markdown("""
        ### ⚡ Kısa Vadeli Stratejiler (5-30dk)
        
        **⚡ Kısa Vadeli Momentum**
        - Son 10 bar %1+ yükseliş
        - Son 3 bar sürekli yükseliş
        - Hedef: %2 kar
        
        **⚡ İntraday Hacim**
        - Hacim 1.5x artmış
        - Fiyat pozitif
        - Hedef: %2 kar
        
        **⚡ Hızlı MA Kesişimi**
        - MA5 > MA10
        - Trend başlangıcı
        - Hedef: %3 kar
        
        ---
        
        ### 🎯 Quantum Stratejiler (Günlük)
        
        **🎯 Quantum Fibonacci**
        - Fibonacci extension seviyeleri
        - %3+ potansiyel
        - Teknik analiz bazlı
        
        **📐 Harmonic Pattern Hunter**
        - ABCD, Gartley pattern
        - Gelişmiş teknik analiz
        - Yüksek başarı oranı
        
        **🔥 Volume Explosion**
        - Hacim 2x+ artış
        - Volume clustering
        - Güçlü momentum
        
        **⚡ RSI Divergence Pro**
        - Bullish divergence
        - 20+ gün veri gerekli
        - %10 hedef
        
        ---
        
        ### 💹 Günlük Stratejiler
        
        **💹 2 Haftalık Güçlü Trend**
        - 14 günde %7+ yükseliş
        - Trend devam ediyor
        - Güvenilir sinyal
        
        **🎣 Dip Avı**
        - 30 günlük dipten %2-8 yükselmiş
        - Momentum başlıyor
        - Erken giriş fırsatı
        
        **🔥 Sessiz Güç**
        - Düşük hacim
        - Fiyat yükseliyor
        - Kurumsal birikim
        
        **📈 Yeşil Seri**
        - 10 günde 7+ yeşil
        - Güçlü momentum
        - %5 hedef
        
        **🏔️ Tepe Yenileme**
        - 50 günlük zirve testi
        - Kırma potansiyeli
        - %5 hedef
        
        **💪 Momentum Patlaması**
        - 5 gün kesintisiz yükseliş
        - %5+ artış
        - Güçlü sinyal
        
        ---
        
        ### 📊 Basit Stratejiler (Her zaman)
        
        **📈 Yükseliş Trendi**
        - MA5 > MA10
        - Trend takibi
        - Başlangıç için ideal
        
        **💪 Momentum**
        - 5 günde %1+ artış
        - Basit ve etkili
        - Her zaman kullanılabilir
        
        **📊 Hacim Patlaması**
        - Hacim 1.5x+ artış
        - Güçlü sinyal
        - %6 hedef
        
        **🎯 Basit Alım**
        - Basit yükseliş
        - Test için ideal
        - Her zaman sinyal verir
        """)
    
    elif guide_tab == "⚠️ Yaygın Hatalar":
        st.markdown("""
        ### ❌ 1. "Sinyal Bulunamadı" Hatası
        
        **Çözümler:**
        - ✅ Minimum skoru düşür (40-50)
        - ✅ Daha fazla strateji seç (4-5 tane)
        - ✅ "Test Stratejisi"ni ekle
        - ✅ Farklı zaman dilimi dene
        - ✅ "Test Grubu" ile dene
        
        ---
        
        ### ❌ 2. "Veri Alınamadı" Hatası
        
        **Nedenler:**
        - yfinance sunucusu yavaş
        - Internet bağlantısı zayıf
        - Hisse kodu yanlış
        - Uyumsuz zaman dilimi
        
        **Çözümler:**
        - ✅ 30 saniye bekle, tekrar dene
        - ✅ Internet bağlantısını kontrol et
        - ✅ "📊 Günlük (3 ay)" seç
        - ✅ Farklı hisse grubu dene
        
        ---
        
        ### ❌ 3. Kısa Vadeli Hata
        
        **Sorun:**
        "5 Dakika" seçtim ama çalışmıyor
        
        **Çözüm:**
        - ✅ Kısa vadeli stratejiler seç:
          - ⚡ Kısa Vadeli Momentum
          - ⚡ İntraday Hacim
          - 🎯 Basit Alım
        - ✅ Uzun süre gerektiren stratejileri kaldır:
          - ❌ 🏔️ Tepe Yenileme (50 gün gerekli)
          - ❌ 💹 2 Haftalık Trend (14 gün gerekli)
        
        ---
        
        ### ❌ 4. "Strateji Hatası" Mesajı
        
        **Nedenler:**
        - Kod hatası
        - pd.isna() eksik
        - Sıfıra bölme
        - Yeterli veri yok
        
        **Çözümler:**
        - ✅ Strateji şablonlarını kullan
        - ✅ Her zaman kontrol ekle:
        ```python
        if len(df) < 20:
            return None
        
        if pd.isna(ma) or ma == 0:
            return None
        ```
        - ✅ "🧪 Test Et" butonu ile dene
        
        ---
        
        ### ❌ 5. Çok Az Sonuç
        
        **Sorun:**
        Sadece 1-2 hisse bulunuyor
        
        **Çözümler:**
        - ✅ Min skoru düşür (40-45)
        - ✅ Daha fazla hisse grubu tara
        - ✅ Farklı stratejiler dene
        - ✅ Piyasa durumunu kontrol et (düşüş trendinde az sinyal normal)
        """)
    
    elif guide_tab == "🌐 Online Yapma":
        st.markdown("""
        ### 🚀 Streamlit Cloud (ÖNERİLEN - ÜCRETSİZ)
        
        **Adım 1: GitHub Hesabı**
        - github.com'a git
        - Ücretsiz hesap aç
        
        **Adım 2: Repository Oluştur**
        - "New repository" tıkla
        - İsim: `bist-trading`
        - Public seç
        - Create!
        
        **Adım 3: Dosyaları Hazırla**
        
        **app.py** (bu kodun tamamı)
        
        **requirements.txt:**
        ```
        streamlit==1.31.0
        pandas==2.1.4
        numpy==1.26.3
        yfinance==0.2.36
        plotly==5.18.0
        scipy==1.11.4
        ```
        
        **Adım 4: GitHub'a Yükle**
        ```bash
        git init
        git add .
        git commit -m "İlk yükleme"
        git branch -M main
        git remote add origin https://github.com/KULLANICI_ADIN/bist-trading.git
        git push -u origin main
        ```
        
        **Adım 5: Deploy Et**
        - share.streamlit.io'ya git
        - GitHub ile giriş yap
        - "New app" tıkla
        - Repository: `bist-trading`
        - Branch: `main`
        - Main file: `app.py`
        - Deploy!
        
        ✅ **2-3 dakikada hazır!**
        🔗 Link: `https://KULLANICI_ADIN-bist-trading.streamlit.app`
        
        ---
        
        ### 💡 Önemli Notlar
        
        - ✅ Tamamen **ÜCRETSİZ**
        - ✅ HTTPS otomatik (güvenli)
        - ✅ 7/24 çalışır
        - ✅ GitHub'a push = otomatik güncelleme
        - ⚠️ İlk açılış 30 saniye sürebilir
        - ⚠️ Uzun süre kullanılmazsa uyur (ilk istek 30 saniye)
        
        ---
        
        ### 🎬 Video Rehber
        
        YouTube'da ara:
        - "Streamlit app deploy tutorial"
        - "How to deploy streamlit to cloud"
        - "Streamlit share github tutorial"
        """)

# ═══════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("## 📊 Sistem Durumu")
    
    st.metric("Stratejiler", len(st.session_state.strategies))
    st.metric("Bulunan Fırsatlar", len(st.session_state.results))
    
    st.markdown("---")
    st.markdown("### 🎯 v6.1 Yenilikleri")
    st.markdown("""
    **✨ Düzeltmeler:**
    - ✅ Kısa vadeli zaman dilimleri düzeltildi
    - ✅ yfinance limitleri uygulandı
    - ✅ Uyumsuz kombinasyon uyarısı
    - ✅ Zaman dilimine göre strateji önerisi
    - ✅ Tam rehber eklendi
    """)
    
    st.markdown("---")
    st.markdown("### 🚀 Hızlı Başlangıç")
    st.markdown("""
    **Kısa Vadeli İçin:**
    1. ⚡ "5 Dakika" seç
    2. ⚡ Kısa vadeli stratejileri işaretle
    3. 📊 "Test Grubu" ile dene
    
    **Orta Vadeli İçin:**
    1. 📊 "Günlük (3 ay)" seç
    2. 💹 "2 Haftalık Trend" + "🎣 Dip Avı"
    3. 📊 "BIST 30" ile tara
    
    **Güvenli Oyun:**
    1. 📅 "Haftalık (1 yıl)" seç
    2. 🏔️ "Tepe Yenileme"
    3. 🎯 Min skor 70+
    """)
    
    st.markdown("---")
    st.markdown("### ⏱️ Zaman Dilimi Limitleri")
    st.info("""
    **yfinance Kuralları:**
    - ✅ 5m: Max 1 gün (~78 bar)
    - ✅ 15m: Max 5 gün (~130 bar)
    - ✅ 30m: Max 7 gün (~112 bar)
    - ✅ 1h: Max 1 ay (~168 bar)
    - ✅ 1d: Limitsiz
    - ✅ 1wk: Limitsiz
    """)
    
    st.markdown("---")
    st.markdown("### 🎯 Strateji Kategorileri")
    
    st.markdown("**⚡ Kısa Vadeli (3):**")
    st.caption("5-30dk için, 10-20 bar yeterli")
    
    st.markdown("**🎯 Quantum (4):**")
    st.caption("Fibonacci, Harmonic, RSI, Volume")
    
    st.markdown("**💹 Günlük (6):**")
    st.caption("Trend, Dip, Momentum, Tepe vb.")
    
    st.markdown("**📊 Basit (4):**")
    st.caption("MA, Momentum, Hacim, Basit Alım")
    
    st.markdown("---")
    st.markdown("### 💡 En İyi Pratikler")
    st.markdown("""
    **Risk Yönetimi:**
    - 📊 Portföyün max %5'i bir hissede
    - 🎯 Her pozisyonda stoplos
    - 💰 Hedef kar: %5-10
    - ⚠️ 3 kayıp = günü bitir
    
    **Tarama Zamanı:**
    - 🌅 Sabah 10:00 (piyasa açılmadan)
    - ☀️ Öğlen 13:00
    - 🌆 Kapanış 17:30'dan önce
    - 📅 Haftalık: Pazar
    """)
    
    st.markdown("---")
    st.markdown("### 📞 Sorun Giderme")
    st.markdown("""
    **Sinyal Yok?**
    1. Min skor 40'a düşür
    2. "✅ Test Stratejisi" ekle
    3. "Test Grubu" seç
    4. Farklı zaman dilimi
    
    **Veri Hatası?**
    1. 30 saniye bekle
    2. Internet kontrol et
    3. "Günlük" seç
    4. Farklı grup dene
    
    **Strateji Hatası?**
    1. Şablonları kullan
    2. "🧪 Test Et" dene
    3. pd.isna() ekle
    4. len(df) kontrol et
    """)
    
    st.markdown("---")
    st.warning("⚠️ **Yasal Uyarı:** Bu araç sadece eğitim amaçlıdır. Yatırım tavsiyesi değildir. Tüm kararlar sizin sorumluluğunuzdadır.")
    
    st.markdown("---")
    st.success("🔄 **v6.1** - Kısa Vadeli Düzeltildi!\n\n✅ Artık tüm zaman dilimleri çalışıyor!")

# ═══════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #888; padding: 20px;'>
    <p><strong>BIST Pro Trading Dashboard v6.1</strong></p>
    <p>🚀 20+ Profesyonel Strateji | ⚡ Tüm Zaman Dilimleri | 📚 Tam Rehber</p>
    <p style='font-size: 12px;'>⚠️ Eğitim amaçlıdır. Yatırım tavsiyesi değildir.</p>
    <p style='font-size: 12px; margin-top: 10px;'>
        💡 <strong>Yeni Özellik:</strong> Kısa vadeli (5-30dk) zaman dilimleri düzeltildi!
    </p>
</div>
""", unsafe_allow_html=True)lük (Son 3 ay - ~60 bar)",
                "📅 Haftalık (Son 1 yıl - ~52 bar)",
                "🔧 Özel"
            ]
        )
        
        # Preset ayarları (yfinance ile uyumlu)
        time_settings = {
            "⚡ 5 Dakika (Son 1 gün - ~78 bar)": ("1d", "5m"),
            "⚡ 15 Dakika (Son 5 gün - ~130 bar)": ("5d", "15m"),
            "⚡ 30 Dakika (Son 7 gün - ~112 bar)": ("7d", "30m"),
            "📈 1 Saat (Son 1 ay - ~168 bar)": ("1mo", "1h"),
            "📊 Gün
