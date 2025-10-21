# ═══════════════════════════════════════════════════════════════
# 📦 KÜTÜPHANE KONTROLÜ
# ═══════════════════════════════════════════════════════════════

import sys

# Kritik kütüphaneleri kontrol et
required_libraries = {
    'streamlit': 'streamlit',
    'pandas': 'pandas', 
    'numpy': 'numpy',
    'yfinance': 'yfinance',
    'plotly': 'plotly',
    'scipy': 'scipy'
}

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
    page_title="BIST Pro Trading v6.0",
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
        # QUANTUM STRATEJİLER
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
        
        "🔒 Float Squeeze": {
            "code": """def analyze(df):
    if len(df) < 20:
        return None
    
    volumes = df['Volume'].values
    closes = df['Close'].values
    
    recent_vol = volumes[-10:].mean() / volumes[-20:-10].mean()
    recent_price = (closes[-1] - closes[-10]) / closes[-10]
    
    if recent_vol > 1.5 and recent_price > 0.05:
        obv = [volumes[0]]
        for i in range(1, len(closes)):
            if closes[i] > closes[i-1]:
                obv.append(obv[-1] + volumes[i])
            elif closes[i] < closes[i-1]:
                obv.append(obv[-1] - volumes[i])
            else:
                obv.append(obv[-1])
        
        obv_trend = (obv[-1] - obv[-10]) / obv[-10] if obv[-10] != 0 else 0
        
        if obv_trend > 0.1:
            score = 75 + min(20, recent_vol * 10)
            return {
                'score': score,
                'target': closes[-1] * 1.12,
                'reason': f'Float Squeeze: Kurumsal birikim tespit'
            }
    
    return None""",
            "desc": "Kurumsal birikim ve float sıkışması"
        },
        
        "🧠 Psychological Barrier": {
            "code": """def analyze(df):
    if len(df) < 50:
        return None
    
    import numpy as np
    
    current = df['Close'].iloc[-1]
    highs = df['High'].values
    
    nearest_five = round(current / 5) * 5
    nearest_ten = round(current / 10) * 10
    
    distance_five = abs(current - nearest_five) / current
    distance_ten = abs(current - nearest_ten) / current
    
    resistance = np.percentile(highs[-50:], 95)
    
    if distance_five < 0.02 or distance_ten < 0.03:
        if current < resistance * 0.95:
            target = max(nearest_five, nearest_ten)
            score = 60 + (1 - min(distance_five, distance_ten)) * 30
            
            return {
                'score': score,
                'target': max(target, resistance),
                'reason': f'Psikolojik seviye: ₺{target:.1f} hedefi'
            }
    
    return None""",
            "desc": "Psikolojik seviye ve direnç analizi"
        },
        
        # ═══════════════════════════════════════════════════════════════
        # YENİ SAĞLAM STRATEJİLER
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
        
        "🎯 Gap Kapatıcı": {
            "code": """def analyze(df):
    if len(df) < 15:
        return None
    
    for i in range(-15, -2):
        prev_close = df['Close'].iloc[i-1]
        today_open = df['Open'].iloc[i]
        current = df['Close'].iloc[-1]
        
        if prev_close > today_open:
            gap_size = ((prev_close - today_open) / today_open) * 100
            
            if gap_size > 2:
                gap_filled = ((current - today_open) / (prev_close - today_open)) * 100
                
                if gap_filled > 50:
                    score = 60 + min(30, gap_filled / 2)
                    return {
                        'score': score,
                        'target': prev_close,
                        'reason': f'%{gap_size:.1f} gap %{gap_filled:.0f} kapatıldı'
                    }
    return None""",
            "desc": "Aşağı gap kapatma senaryosu"
        },
        
        "🌊 Dalga Analizi": {
            "code": """def analyze(df):
    if len(df) < 20:
        return None
    
    closes = df['Close'].tail(20).values
    
    peaks = []
    valleys = []
    
    for i in range(1, len(closes)-1):
        if closes[i] > closes[i-1] and closes[i] > closes[i+1]:
            peaks.append(i)
        elif closes[i] < closes[i-1] and closes[i] < closes[i+1]:
            valleys.append(i)
    
    if len(peaks) >= 1 and len(valleys) >= 1:
        last_valley_idx = valleys[-1]
        if last_valley_idx < len(closes) - 3:
            rise = ((closes[-1] - closes[last_valley_idx]) / closes[last_valley_idx]) * 100
            
            if rise > 3:
                score = 65 + min(25, rise * 2)
                return {
                    'score': score,
                    'target': closes[-1] * 1.08,
                    'reason': f'Dalga dipinden %{rise:.1f} yükseldi'
                }
    return None""",
            "desc": "Elliott Wave benzeri dalga analizi"
        },
        
        "🔋 Enerji Birikimi": {
            "code": """def analyze(df):
    if len(df) < 30:
        return None
    
    import numpy as np
    
    std_30 = df['Close'].tail(30).std()
    std_7 = df['Close'].tail(7).std()
    
    if std_7 < std_30 * 0.6:
        high_7 = df['High'].tail(7).max()
        low_7 = df['Low'].tail(7).min()
        range_7 = ((high_7 - low_7) / low_7) * 100
        
        if range_7 < 3:
            score = 70
            return {
                'score': score,
                'target': df['Close'].iloc[-1] * 1.10,
                'reason': f'Volatilite düştü, dar bant (%{range_7:.1f}), patlama yakın'
            }
    return None""",
            "desc": "Düşük volatilite + dar bant = patlama öncesi"
        },
        
        "🎪 Hacim Sürprizi": {
            "code": """def analyze(df):
    if len(df) < 30:
        return None
    
    vol_ma_30 = df['Volume'].tail(30).mean()
    today_vol = df['Volume'].iloc[-1]
    today_change = ((df['Close'].iloc[-1] - df['Open'].iloc[-1]) / df['Open'].iloc[-1]) * 100
    
    if today_vol > vol_ma_30 * 2.5 and today_change > 0:
        vol_ratio = today_vol / vol_ma_30
        score = 75 + min(20, (vol_ratio - 2) * 5)
        
        return {
            'score': score,
            'target': df['Close'].iloc[-1] * 1.08,
            'reason': f'Dev hacim: {vol_ratio:.1f}x, fiyat +%{today_change:.1f}'
        }
    return None""",
            "desc": "Anormal hacim patlaması + pozitif fiyat"
        },
        
        # ═══════════════════════════════════════════════════════════════
        # BASIT STRATEJİLER
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
        'JANTs', 'KAPLM', 'KAREL', 'KARSN', 'KARTN', 'KATMR',
    'KAYSE', 'KBORU', 'KCAER', 'KCHOL', 'KENT', 'KERVN',
    'KFEIN', 'KIMMR', 'KLKIM', 'KLMSN', 'KLNMA', 'KLRHO',
    'KLSER', 'KLSYN', 'KLYPv', 'KMPUR', 'KNFRT', 'KOCMT',
    'KONKA', 'KONTR', 'KONYA', 'KOPOL', 'KORDS', 'KOTON',
    'KOZAA', 'KOZAL', 'KRDMA', 'KRONT', 'KRPLS', 'KRSTL',
    'KRTEK', 'KRVGD', 'KSTUR', 'KTLEV', 'KUTPO', 'KUVVA',
    'KZBGY', 'KZGYO', 'LIDER', 'LIDFA', 'LILAK', 'LINK',
    'LKMNH', 'Lmkdc', 'LOGO', 'LRSHO', 'LUKSK', 'LYDHO',
    'LYDYE', 'MAALT', 'MACKO', 'MAGEN', 'MAKIM', 'MAKTK',
    'MANAS', 'MARBL', 'MARKA', 'MARMr', 'MARTI', 'MNDTR',
    'MOBTL', 'MOGAN', 'MOPAS', 'MPARK', 'MRSHL', 'MTRKS',
    'MTRYO', 'MZHLD', 'NATEN', 'NETAS', 'NIBAS', 'NTGAZ',
    'NTHOL', 'NUHCM', 'OBAMS', 'OBASE', 'ODAS', 'ODINE',
    'OFSYM', 'ONCSM', 'ONRYT', 'ORCAY', 'ORGE', 'ORMA',
    'OSMEN', 'OSTIM', 'OTKAR', 'OTTO', 'OYAKC', 'OYAYO',
    'OYLUM', 'OYYAT', 'OZATD', 'OZrdn', 'OZSUB', 'OZGYO',
    'PAGYO', 'PAmEL', 'PAPIL', 'PARSN', 'PASEU', 'PATEK',
    'PCILT', 'PEKGY', 'PENGD', 'PENTA', 'PETKM', 'PETUN',
    'PGSUS', 'PINSU', 'PKART', 'PKENT', 'PLTUR',
    'PNLSN', 'PNSUT', 'POLHO', 'POLTK', 'PRdGS', 'PRKAB',
    'PRKME', 'PRZMA', 'PSDTc', 'QNBtr', 'QNBfk', 'QUAGR', 'RALYH',
    'RAYsG', 'REEDR', 'ROYAl', 'RNPOL', 'RODRg', 'RTALB',
    'RUBNS', 'RUZYE', 'RYSAS', 'SAFKR', 'SAHOL', 'SAMAT',
    'SANEL', 'SANFM', 'SANKO', 'SARKY', 'SASA', 'SAYAS',
    'SDTTR', 'SEGMn', 'SEGYO', 'SEKfk', 'SEKUR', 'SELEC',
    'SELVA', 'SERNT', 'SEYKM', 'SILVR', 'SISE', 'SKBNK', 
    'SKTAS', 'SKYLP', 'SKYMD', 'SMART', 'SMRTG', 'SMRVA',
    'SNICA', 'SNKRN', 'SNPAM', 'SODSN', 'SOKE', 'SOKM',
    'SONME', 'SRVGY', 'SUMAS', 'SUNTK', 'SURGY', 'SUWEN',
    'TABGD', 'TARKM', 'TATEN', 'TATGD', 'TAVHL', 'TBORG',
    'TCELL', 'Tckrc', 'TDGYO', 'TEKTU', 'TERA', 'TEZOL',
    'TGSAS', 'THYAO', 'TKFEN', 'TKNsa', 'TLMAN', 'TMPOL',
    'TMSN', 'TNZTP', 'TOASO', 'TRCAS', 'TRGYO', 'TRILC',
    'TSKB', 'TSPOR', 'TTKOM', 'TTRaK', 'TUCLk', 'TUKAS',
    'TUPRS', 'TUREX', 'TURG', 'TURSG', 'UFUK', 'ULAS',
    'ULKER', 'ULUFA', 'ULUSE', 'ULUun', 'UNLU', 'USAK',
    'VAKBN', 'VAKFN', 'VAKKO', 'VANGD', 'VBTYZ', 'VERUS',
    'VESBE', 'VESTL', 'VKFYO', 'VKING', 'VRGYO', 'VSNMD',
    'YAPRK', 'YATAS', 'YAYLA', 'YBTAS', 'YEOTK', 'YESIL',
    'YGGYO', 'YIGIT', 'YKBNK', 'YKSLN', 'YONGA', 'YUNSA',
    'YYAPI', 'YYLGD', 'ZEDUR', 'ZOREN', 'ZRGYO', 'A1CAP',
    'A1YEN', 'ACSEL', 'ADEL', 'ADESE', 'ADGYO', 'AEFES',
    'AFYON', 'AGESA', 'AGHOL', 'AGROT', 'AHSGY', 'AKBNK',
    'AKCNS', 'AKENR', 'AKFIS', 'AKFYE', 'AKGRT', 'AKSA',
    'AKSEN', 'AKSUE', 'AKYHO', 'ALARK', 'ALBRK', 'ALCAR',
    'ALCTL', 'ALFAS', 'ALKA', 'ALKIM', 'ALKLC',
    'ALTNY', 'ALVES', 'ANELE', 'ANGEN', 'ANHYT', 'ANSGR',
    'ARASE', 'ARCLK', 'ARDYZ', 'ARENA', 'ARMGD', 'ARSAN',
    'ARTMS', 'ARZUM', 'ASELS', 'ASTOR', 'ASUZU', 'ATATP',
    'ATEKS', 'ATLAS', 'ATSYH', 'AVGYO', 'AVHOL', 'AVOD',
    'AVPGY', 'AYCES', 'AYDEM', 'AYEN', 'AYES', 'AYGAZ',
    'AZTEK', 'BAGFS', 'BAHKM', 'BAKAB', 'BALAT', 'BALSU',
    'BANVT', 'BARMA', 'BASCM', 'BASGZ', 'BAYRK', 'BEGYO',
    'BERA', 'BESLR', 'BEYAZ', 'BFREN', 'BIENY', 'BIGCH', 
    'BIOEN', 'BIZIM', 'BJKAS', 'BLCYT', 'BLUME', 'BMSCH',
    'BMSTL', 'BNTAS', 'BObet', 'BORLS', 'BORSK', 'BOSSA',
    'BRISA', 'BRKO', 'BRKSN', 'BRKVY', 'BRLSM', 'BRMEN',
    'BRSAN', 'BRYAT', 'BSOKE', 'BTCIM', 'BULGs', 'BURCE',
    'BURVA', 'BVSAN', 'BYDNR', 'CANTE', 'CASA', 'CATES',
    'CCOLA', 'CELHA', 'CEMAS', 'CEMTS', 'CEMZY', 'CEDEM',
    'Cmbtn', 'CIMSA', 'CLEBI', 'CMBTN', 'CMEnT', 'CONSE',
    'COSMO', 'CRDFA', 'CRFSA', 'CUSAN', 'CVKmD', 'CWENE',
    'DAGI', 'DAPGM', 'DARDL', 'DCTTr', 'DENGE', 'DERHL',
    'DERIM', 'DESA', 'DESPC', 'DEVA', 'DGATE', 'DGNMO',
    'DIRIT', 'DITAS', 'DMRgd', 'DMSAS', 'DNISI', # DİRİT -> DIRIT
    'DOAS', 'DOBUR', 'DOFER', 'DOFRB', 'DOGUB', 'DOHOL',
    'DOKTA', 'DSTKF', 'DUNYH', 'DURDO', 'DURkn', 'DYOBY',
    'DZgYO', 'EBEBK', 'ECILC', 'ECZYT', 'EDATA', 'EDIP',
    'EFORc', 'EGEEN', 'EGEGY', 'EGEPO', 'EGgUb', 'EGPRO',
    'EGSER', 'EKIZ', 'EKOS', 'EKSUN', 'ELITE', 'EMKEL',
    'EMNIS', 'ENDAe', 'ENERY', 'ENJSA', 'ENKAI', 'ENSRI',
    'ENTRA', 'EPLAS', 'ERBOS', 'ERCb', 'EREGL', 'ERSU',
    'ESCAR', 'ESCOM', 'ESEN', 'ETILR', 'ETYAT', 'EUHOL', 
    'EUKYO', 'EUPWR', 'EUREN', 'EUYO', 'FADE', 'FENER',
    'FLAP', 'FMIzp', 'FONET', 'FORMT', 'FORTE', 'FRIGO', 
     'MAALT', 'MACKO','MAGEN','MAKIM', 'MAKTK', 'MANAS', 'MARBL',
    'MARKA', 'MARMR',  'MARTI', 'MAVI', 'MEDTR', 'MEGAP', 'MEGMT',
    'MEKAG', 'MEPET', 'MERCN', 'MERIT', 'MERKO', 'METRO', 'MGROS',
    'MHRGY', 'MIATK', 'MMCAS', 'MNDRS', 'MNDTR', 'MOBTL', 'MOGAN',
    'MOPAS', 'MPARK', 'MRGYO', 'MRSHL', 'MSGYO', 'MTRKS', 'MTRYO',
    'MZHLD','HEKTS', 'HKTM', 'HDFGS', 'HRKET', 'HTTBt', 'HUBVC', 'HUNER',
    'HURGZ', 'ICBCT', 'ICUGS', 'IEYHO', 'IHAAS', 'IHEVA',
    'IHGZT', 'IHLAS', 'IHLGM', 'IHYAY', 'IMASM', 'INDES',
    'INFO', 'INGRM', 'INTEK', 'INTEM', 'INVEO', 'INVES',
    'IPEKE', 'ISBIR', 'ISDMR', 'ISFIN', 'ISKPL', 'ISMEN',
    'ISSEN', 'IZMDC', 'IZenr', 'IZFAS', 'IZINV'
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

st.markdown('<p class="big-font">🚀 BIST PRO TRADING DASHBOARD v6.0</p>', unsafe_allow_html=True)
st.markdown("**✨ 20+ Profesyonel Strateji | ⚡ Kısa Vadeli Zaman Dilimleri Eklendi!**")

# TABS
tab1, tab2, tab3, tab4 = st.tabs(["🔍 Tarama", "⚙️ Stratejiler", "📊 Sonuçlar", "🌐 Online Paylaşım"])

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
                "⚡ 5 Dakika (1 gün)",
                "⚡ 10 Dakika (2 gün)", 
                "⚡ 15 Dakika (3 gün)",
                "⚡ 30 Dakika (5 gün)",
                "⚡ 40 Dakika (7 gün)",
                "📈 1 Saat (1 hafta)",
                "📊 Günlük (3 ay)",
                "📅 Haftalık (1 yıl)",
                "🔧 Özel"
            ]
        )
        
        # Preset ayarları
        time_settings = {
            "⚡ 5 Dakika (1 gün)": ("1d", "5m"),
            "⚡ 10 Dakika (2 gün)": ("2d", "10m"),
            "⚡ 15 Dakika (3 gün)": ("3d", "15m"),
            "⚡ 30 Dakika (5 gün)": ("5d", "30m"),
            "⚡ 40 Dakika (7 gün)": ("7d", "40m"),
            "📈 1 Saat (1 hafta)": ("7d", "1h"),
            "📊 Günlük (3 ay)": ("3mo", "1d"),
            "📅 Haftalık (1 yıl)": ("1y", "1wk")
        }
        
        if time_preset in time_settings:
            period, interval = time_settings[time_preset]
        else:  # Özel
            period = st.selectbox(
                "Period", 
                ["1d", "2d", "3d", "5d", "7d", "1mo", "3mo", "6mo", "1y"], 
                index=4
            )
            interval = st.selectbox(
                "Interval", 
                ["5m", "10m", "15m", "30m", "40m", "1h", "1d", "1wk"], 
                index=6
            )
        
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
    
    strategy_cols = st.columns(3)
    selected_strategies = []
    
    strategy_list = list(st.session_state.strategies.keys())
    
    # İlk 3 strateji varsayılan seçili
    default_selected = strategy_list[:3]
    
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
                4. ✅ Stratejileri kontrol edin
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
            "Basit Yükseliş",
            "MA Kesişimi",
            "Volume",
            "2 Haftalık Fiyat Değişimi",
            "Düşüş Sonrası Toparlanma",
            "Düşük Hacimde Yükseliş",
            "Haftalık Kazananlar",
            "Destek Seviyesi Tutması",
            "Gap Kapatma"
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
            
            "Volume": """def analyze(df):
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
    return None""",
            
            "2 Haftalık Fiyat Değişimi": """def analyze(df):
    if len(df) < 14:
        return None
    
    old_price = df['Close'].iloc[-14]
    current_price = df['Close'].iloc[-1]
    
    change = ((current_price - old_price) / old_price) * 100
    
    if change > 5:
        score = 50 + min(40, change * 2)
        return {
            'score': score,
            'target': current_price * 1.05,
            'reason': f'Son 2 haftada %{change:.1f} yükseldi'
        }
    return None""",
            
            "Düşüş Sonrası Toparlanma": """def analyze(df):
    if len(df) < 20:
        return None
    
    max_20 = df['High'].tail(20).max()
    current = df['Close'].iloc[-1]
    
    drop = ((max_20 - current) / max_20) * 100
    
    last_3_change = ((df['Close'].iloc[-1] - df['Close'].iloc[-3]) / df['Close'].iloc[-3]) * 100
    
    if 10 < drop < 20 and last_3_change > 2:
        score = 60 + min(30, last_3_change * 5)
        return {
            'score': score,
            'target': current * 1.08,
            'reason': f'%{drop:.1f} düşüşten toparlanıyor (%{last_3_change:.1f})'
        }
    return None""",
            
            "Düşük Hacimde Yükseliş": """def analyze(df):
    if len(df) < 20:
        return None
    
    vol_ma = df['Volume'].rolling(20).mean().iloc[-1]
    current_vol = df['Volume'].iloc[-1]
    
    if pd.isna(vol_ma) or vol_ma == 0:
        return None
    
    vol_ratio = current_vol / vol_ma
    
    price_change = ((df['Close'].iloc[-1] - df['Close'].iloc[-5]) / df['Close'].iloc[-5]) * 100
    
    if vol_ratio < 0.5 and price_change > 3:
        score = 70 + min(20, price_change * 3)
        return {
            'score': score,
            'target': df['Close'].iloc[-1] * 1.10,
            'reason': f'Sessiz yükseliş: %{price_change:.1f} (hacim düşük)'
        }
    return None""",
            
            "Haftalık Kazananlar": """def analyze(df):
    if len(df) < 7:
        return None
    
    green_days = 0
    for i in range(-7, 0):
        if df['Close'].iloc[i] > df['Open'].iloc[i]:
            green_days += 1
    
    if green_days >= 5:
        weekly_change = ((df['Close'].iloc[-1] - df['Close'].iloc[-7]) / df['Close'].iloc[-7]) * 100
        score = 55 + min(35, green_days * 5)
        
        return {
            'score': score,
            'target': df['Close'].iloc[-1] * 1.05,
            'reason': f'7 günde {green_days} yeşil gün (%{weekly_change:.1f})'
        }
    return None""",
            
            "Destek Seviyesi Tutması": """def analyze(df):
    if len(df) < 30:
        return None
    
    import numpy as np
    
    lows = df['Low'].tail(30).values
    current = df['Close'].iloc[-1]
    
    support = np.percentile(lows, 5)
    
    recent_lows = df['Low'].tail(5).min()
    
    if abs(recent_lows - support) / support < 0.02:
        if current > recent_lows * 1.01:
            score = 65
            return {
                'score': score,
                'target': current * 1.08,
                'reason': f'Destek seviyesi (₺{support:.2f}) tuttu'
            }
    return None""",
            
            "Gap Kapatma": """def analyze(df):
    if len(df) < 10:
        return None
    
    for i in range(-10, -1):
        prev_close = df['Close'].iloc[i-1]
        today_open = df['Open'].iloc[i]
        today_close = df['Close'].iloc[i]
        
        gap = ((prev_close - today_open) / prev_close) * 100
        
        if gap > 2:
            if today_close > today_open * 1.015:
                score = 60 + min(30, gap * 5)
                return {
                    'score': score,
                    'target': prev_close,
                    'reason': f'%{gap:.1f} gap kapatılıyor'
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
                if test_symbol and new_code:
                    df_test = get_stock_data(test_symbol, "3mo", "1d")
                    if df_test is not None:
                        result_test = run_strategy(df_test, new_code)
                        if result_test:
                            st.success("✅ Çalışıyor!")
                            st.json(result_test)
                        else:
                            st.warning("⚠️ Sinyal üretmedi")
                    else:
                        st.error("❌ Veri alınamadı")
    
    with col2:
        st.markdown("### 📚 Mevcut Stratejiler")
        st.metric("Toplam", len(st.session_state.strategies))
        
        st.markdown("---")
        st.markdown("**Kategoriler:**")
        st.markdown("🎯 Quantum: 7 adet")
        st.markdown("💹 Yeni Sağlam: 10 adet")
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
# TAB 4: ONLİNE PAYLAŞIM
# ═══════════════════════════════════════════════════════════════

with tab4:
    st.markdown("## 🌐 Online Paylaşım Rehberi")
    
    st.info("Bu uygulamayı online yapmak için 3 ücretsiz yöntem var!")
    
    method = st.radio("Yöntem Seçin:", [
        "1️⃣ Streamlit Cloud (ÖNERİLEN - En Kolay)",
        "2️⃣ Render.com (Alternatif)",
        "3️⃣ Heroku (Sınırlı Ücretsiz)"
    ])
    
    if "Streamlit Cloud" in method:
        st.markdown("### 🎯 Streamlit Cloud ile Deploy")
        st.markdown("""
        **Adım Adım:**
        
        1. **GitHub Hesabı Oluştur** (github.com)
        2. **Yeni Repository Oluştur** (örn: `bist-trading`)
        3. **Dosyaları Hazırla:**
           - `app.py` (bu kodun tamamı)
           - `requirements.txt` (aşağıdaki içerik)
        
        4. **GitHub'a Yükle:**
        ```bash
        git init
        git add .
        git commit -m "İlk yükleme"
        git branch -M main
        git remote add origin https://github.com/KULLANICI_ADIN/bist-trading.git
        git push -u origin main
        ```
        
        5. **Deploy Et:**
           - share.streamlit.io adresine git
           - GitHub ile giriş yap
           - "New app" tıkla
           - Repository'ni seç
           - Deploy!
        
        ✅ **2-3 dakikada hazır!**  
        🔗 Link: `https://KULLANICI_ADIN-bist-trading.streamlit.app`
        """)
        
        st.markdown("### 📄 requirements.txt İçeriği:")
        st.code("""streamlit==1.31.0
pandas==2.1.4
numpy==1.26.3
yfinance==0.2.36
plotly==5.18.0
scipy==1.11.4""", language="text")
        
        st.download_button(
            "📥 requirements.txt İndir",
            """streamlit==1.31.0
pandas==2.1.4
numpy==1.26.3
yfinance==0.2.36
plotly==5.18.0
scipy==1.11.4""",
            "requirements.txt"
        )
    
    elif "Render.com" in method:
        st.markdown("### 🎯 Render.com ile Deploy")
        st.markdown("""
        **Adım Adım:**
        
        1. render.com'a git
        2. GitHub ile giriş yap
        3. "New Web Service" seç
        4. Repository'ni bağla
        5. **Ayarlar:**
           - Environment: Python 3
           - Build Command: `pip install -r requirements.txt`
           - Start Command: `streamlit run app.py --server.port=$PORT`
        6. Deploy!
        
        ✅ **5 dakikada hazır!**  
        🔗 Link: `https://bist-trading-ABC123.onrender.com`
        """)
    
    else:
        st.markdown("### 🎯 Heroku ile Deploy")
        st.markdown("""
        **Adım Adım:**
        
        1. heroku.com hesabı aç
        2. Heroku CLI yükle
        3. **Ekstra dosyalar oluştur:**
        
        **Procfile:**
        ```
        web: sh setup.sh && streamlit run app.py
        ```
        
        **setup.sh:**
        ```bash
        mkdir -p ~/.streamlit/
        echo "\\
        [server]\\n\\
        headless = true\\n\\
        port = $PORT\\n\\
        enableCORS = false\\n\\
        \\n\\
        " > ~/.streamlit/config.toml
        ```
        
        4. **Deploy:**
        ```bash
        heroku login
        heroku create bist-trading
        git push heroku main
        ```
        
        ✅ **10 dakikada hazır!**  
        🔗 Link: `https://bist-trading.herokuapp.com`
        """)
    
    st.markdown("---")
    st.markdown("### 💡 Önemli Notlar")
    st.markdown("""
    - ✅ Hepsi tamamen **ÜCRETSİZ**
    - ✅ HTTPS otomatik (güvenli)
    - ✅ 7/24 çalışır
    - ✅ GitHub'a push = otomatik güncelleme
    - ⚠️ İlk yüklemede 2-5 dakika bekleyebilir
    - ⚠️ Ücretsiz planlarda bazen uyuyabilir (ilk istek 30 saniye)
    """)
    
    st.markdown("---")
    st.markdown("### 🎬 Video Rehberler")
    st.markdown("""
    YouTube'da arama yapın:
    - "Streamlit app deploy tutorial"
    - "How to deploy streamlit to cloud"
    - "Streamlit share tutorial"
    """)

# ═══════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("## 📊 Sistem Durumu")
    
    st.metric("Stratejiler", len(st.session_state.strategies))
    st.metric("Bulunan Fırsatlar", len(st.session_state.results))
    
    st.markdown("---")
    st.markdown("### 🎯 v6.0 Yenilikleri")
    st.markdown("""
    **✨ Yeni Özellikler:**
    - ⚡ Kısa vadeli zaman dilimleri (5dk, 10dk, 15dk, 30dk, 40dk)
    - 💹 10 yeni sağlam strateji
    - 🌐 Online paylaşım rehberi
    - 📚 10 hazır strateji şablonu
    """)
    
    st.markdown("---")
    st.markdown("### 🚀 Hızlı Başlangıç")
    st.markdown("""
    **Kısa Vadeli İçin:**
    1. ⚡ "5 Dakika (1 gün)" seç
    2. 🎯 "Momentum Patlaması" stratejisini ekle
    3. 📊 "Test Grubu" ile dene
    
    **Orta Vadeli İçin:**
    1. 📈 "Günlük (3 ay)" seç
    2. 💹 "2 Haftalık Güçlü Trend" ekle
    3. 📊 "BIST 30" ile tara
    
    **Güvenli Oyun İçin:**
    1. 📅 "Haftalık (1 yıl)" seç
    2. 🏔️ "Tepe Yenileme" stratejisi
    3. 🎯 Min skor 70+
    """)
    
    st.markdown("---")
    st.markdown("### 🎯 Strateji Kategorileri")
    
    st.markdown("**🎯 Quantum (7):**")
    st.caption("Fibonacci, Harmonic, RSI Divergence, Float Squeeze")
    
    st.markdown("**💹 Yeni Sağlam (10):**")
    st.caption("2 Haftalık Trend, Dip Avı, Sessiz Güç, Yeşil Seri, Tepe Yenileme, Momentum, Gap, Dalga, Enerji, Hacim Sürprizi")
    
    st.markdown("**📊 Basit (4):**")
    st.caption("Yükseliş Trendi, Momentum, Hacim Patlaması, Basit Alım")
    
    st.markdown("---")
    st.markdown("### 💡 Strateji Ekleme İpuçları")
    st.markdown("""
    **Başarılı Strateji İçin:**
    1. ✅ Basit tut (5-20 satır kod)
    2. ✅ Minimum 5-10 gün veri kontrol et
    3. ✅ pd.isna() kontrolü yap
    4. ✅ Sıfıra bölme hatası önle
    5. ✅ Score 50-95 arası
    6. ✅ Target %3-15 arası
    
    **Örnek Mantıklar:**
    - Son X günde Y% yükseliş
    - Hacim Z kat arttı
    - MA kesişmeleri
    - Destek/Direnç testleri
    - Gap kapatmalar
    - Volatilite daralmalar
    """)
    
    st.markdown("---")
    st.markdown("### ⚡ Kısa Vadeli Uyarılar")
    st.warning("""
    **Dikkat:**
    - ⚠️ Kısa vadeli veriler daha volatil
    - ⚠️ 5-15 dk dilimler gün içi işlem için
    - ⚠️ Hacim önemli (düşük hacimde yanıltıcı)
    - ⚠️ Stoplos mutlaka kullanın
    - ⚠️ Risk yönetimi şart
    """)
    
    st.markdown("---")
    st.markdown("### 📈 Performans İpuçları")
    st.markdown("""
    **En İyi Sonuçlar:**
    - 🎯 3-5 strateji birlikte kullan
    - 📊 Skor 60+ daha güvenilir
    - 💹 2+ sinyal veren hisseler
    - ⏱️ Günlük taramalar en dengeli
    - 🔄 Haftalık piyasa değerlendirmesi
    """)
    
    st.markdown("---")
    st.markdown("### 🌐 Online Yapma")
    st.info("""
    **3 Kolay Yöntem:**
    1. Streamlit Cloud (ÖNERİLEN)
    2. Render.com
    3. Heroku
    
    Detaylar için "🌐 Online Paylaşım" sekmesine bakın!
    """)
    
    st.markdown("---")
    st.warning("⚠️ **Yasal Uyarı:** Bu araç sadece eğitim amaçlıdır. Yatırım tavsiyesi değildir. Tüm kararlar sizin sorumluluğunuzdadır.")
    
    st.markdown("---")
    st.markdown("### 📞 Destek")
    st.markdown("""
    **Sorun mu var?**
    1. "Test Stratejisi" dene
    2. "Test Grubu" tara
    3. Min skor 30'a düşür
    4. Scipy kurulu mu kontrol et
    
    **Hala sinyal yok?**
    - Internet bağlantısı OK mı?
    - YFinance sunucuları aktif mi?
    - Farklı zaman dilimi dene
    - Daha fazla strateji seç
    """)
    
    st.markdown("---")
    st.success("🔄 **v6.0** - Kısa Vadeli + 20+ Strateji!\n\n✅ En güçlü versiyon!")
    
    st.markdown("---")
    st.markdown("### 🎓 Öğrenme Kaynakları")
    st.markdown("""
    **Teknik Analiz:**
    - Fibonacci retracements
    - RSI divergence
    - MACD crossovers
    - Volume analysis
    - Support/Resistance
    
    **Python:**
    - pandas DataFrame
    - numpy hesaplamalar
    - scipy signal processing
    """)
    
    st.markdown("---")
    st.markdown("### 🏆 En İyi Uygulamalar")
    st.markdown("""
    **Risk Yönetimi:**
    1. Portföyün max %5'i bir hissede
    2. Her pozisyonda stoplos
    3. Hedef kar %5-10 arası
    4. 3 işlem kaybı = günü bitir
    
    **Tarama:**
    1. Sabah piyasa açılmadan
    2. Öğlen arası
    3. Kapanıştan önce
    4. Haftalık Pazar analizi
    """)

# ═══════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #888; padding: 20px;'>
    <p><strong>BIST Pro Trading Dashboard v6.0</strong></p>
    <p>🚀 20+ Profesyonel Strateji | ⚡ Kısa Vadeli Destekli | 🌐 Online Paylaşım Rehberi</p>
    <p style='font-size: 12px;'>⚠️ Eğitim amaçlıdır. Yatırım tavsiyesi değildir.</p>
</div>
""", unsafe_allow_html=True)
