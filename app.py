"""
╔══════════════════════════════════════════════════════════════╗
║          🚀 KAZANCKAPISI - BIST TARAMA SİSTEMİ              ║
║     Profesyonel Çoklu Strateji + Telegram Entegrasyonu      ║
╚══════════════════════════════════════════════════════════════╝
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

try:
    import telebot
    TELEGRAM_OK = True
except:
    TELEGRAM_OK = False

# ═══════════════════════════════════════════════════════════════
# AYARLAR
# ═══════════════════════════════════════════════════════════════

TOKEN = "8310745808:AAGpnfSna6-6AJ5I2FNKyES2Rdj_Xqu4b7o"
CHAT_ID = "1801093830"

HISSELER = [
    "THYAO.IS", "GARAN.IS", "AKBNK.IS", "EREGL.IS", "TUPRS.IS",
    "PETKM.IS", "SISE.IS", "ASELS.IS", "TCELL.IS", "SAHOL.IS"
]

# ═══════════════════════════════════════════════════════════════
# VERİ ÇEKME + TEKNİK GÖSTERGELER
# ═══════════════════════════════════════════════════════════════

def veri_cek(sembol, period='3mo', interval='1d'):
    try:
        df = yf.download(sembol, period=period, interval=interval, progress=False)
        if df.empty or len(df) < 20:
            return None
        df = hesapla_gostergeler(df)
        return df
    except:
        return None

def hesapla_gostergeler(df):
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MFI
    tp = (df['High'] + df['Low'] + df['Close']) / 3
    mf = tp * df['Volume']
    pf = mf.where(tp > tp.shift(1), 0).rolling(14).sum()
    nf = mf.where(tp < tp.shift(1), 0).rolling(14).sum()
    df['MFI'] = 100 - (100 / (1 + pf / nf))
    
    # Stochastic RSI
    rsi_min = df['RSI'].rolling(14).min()
    rsi_max = df['RSI'].rolling(14).max()
    df['StochRSI'] = (df['RSI'] - rsi_min) / (rsi_max - rsi_min) * 100
    
    # MACD
    ema12 = df['Close'].ewm(span=12).mean()
    ema26 = df['Close'].ewm(span=26).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    
    # EMA
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    df['EMA200'] = df['Close'].ewm(span=200).mean()
    
    # Hacim
    df['Vol_MA20'] = df['Volume'].rolling(20).mean()
    
    # Bollinger Bands
    df['BB_Mid'] = df['Close'].rolling(20).mean()
    std = df['Close'].rolling(20).std()
    df['BB_Upper'] = df['BB_Mid'] + (std * 2)
    df['BB_Lower'] = df['BB_Mid'] - (std * 2)
    
    return df

# ═══════════════════════════════════════════════════════════════
# STRATEJİLER
# ═══════════════════════════════════════════════════════════════

class KAZANCKAPISI_1:
    """
    RSI + MFI + Stochastic RSI Kombinasyonu
    En İyi: 1 Saat, 4 Saat
    Üç momentum göstergesi birlikte aşırı satım bölgesinden çıkış yakalar
    """
    @staticmethod
    def analiz(df):
        if df is None or len(df) < 30:
            return None
        
        son = df.iloc[-1]
        if son['RSI'] < 30 and son['MFI'] < 30 and son['StochRSI'] > 20:
            skor = 75 + min(25, (30-son['RSI']) + (30-son['MFI']))
            return {
                'skor': skor,
                'hedef': son['Close'] * 1.08,
                'sebep': f"RSI:{son['RSI']:.0f} MFI:{son['MFI']:.0f} StochRSI:{son['StochRSI']:.0f}"
            }
        return None

class KAZANCKAPISI_2:
    """
    Quantum Fibonacci Extension
    En İyi: Günlük, Haftalık
    Son 20 bar swing'den Fib extension seviyeleri hesaplar
    """
    @staticmethod
    def analiz(df):
        if df is None or len(df) < 20:
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
                return {'skor': 60 + min(30, pot * 3), 'hedef': target, 'sebep': f"Fib Ext %{pot:.1f}"}
        return None

class KAZANCKAPISI_3:
    """
    Hacim Patlaması + MACD Kesişim
    En İyi: 5dk, 15dk, 1 Saat
    Hacim 2x + MACD pozitife dönüş = Güçlü momentum
    """
    @staticmethod
    def analiz(df):
        if df is None or len(df) < 20:
            return None
        
        son, onceki = df.iloc[-1], df.iloc[-2]
        vol_ratio = son['Volume'] / son['Vol_MA20']
        macd_kesisim = onceki['MACD_Hist'] < 0 and son['MACD_Hist'] > 0
        
        if vol_ratio > 2.0 and son['MACD_Hist'] > 0:
            bonus = 15 if macd_kesisim else 0
            skor = 70 + min(30, (vol_ratio - 2) * 10) + bonus
            return {'skor': skor, 'hedef': son['Close'] * 1.06, 'sebep': f"Hacim:{vol_ratio:.1f}x MACD✅"}
        return None

class KAZANCKAPISI_4:
    """
    Yükselen Üçgen Formasyonu
    En İyi: Günlük, 4 Saat
    Yatay direnç + yükselen destek = Kırılım potansiyeli
    """
    @staticmethod
    def analiz(df):
        if df is None or len(df) < 30:
            return None
        
        son_30 = df.tail(30)
        ust_var = son_30['High'].nlargest(5).std() / son_30['High'].nlargest(5).mean()
        alt_egim = (son_30['Low'].nsmallest(5).iloc[-1] - son_30['Low'].nsmallest(5).iloc[0]) / 5
        
        if ust_var < 0.02 and alt_egim > 0:
            return {'skor': 75, 'hedef': son_30['High'].max() * 1.05, 'sebep': "Yükselen Üçgen"}
        return None

class KAZANCKAPISI_5:
    """
    Çift Dip (W) Formasyonu
    En İyi: Günlük, Haftalık
    İki benzer dip + boyun çizgisi kırılımı
    """
    @staticmethod
    def analiz(df):
        if df is None or len(df) < 60:
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
                return {'skor': 80, 'hedef': boyun + (boyun - d1_val), 'sebep': "Çift Dip (W)"}
        return None

class KAZANCKAPISI_6:
    """
    EMA Dizilimi + RSI 50-70
    En İyi: 1 Saat, 4 Saat, Günlük
    EMA20>EMA50>EMA200 + RSI sağlıklı = Temiz trend
    """
    @staticmethod
    def analiz(df):
        if df is None or len(df) < 200:
            return None
        
        son = df.iloc[-1]
        if (son['EMA20'] > son['EMA50'] > son['EMA200'] and 
            son['Close'] > son['EMA20'] and 50 <= son['RSI'] <= 70):
            return {'skor': 70 + (son['RSI'] - 50) / 2, 'hedef': son['Close'] * 1.05, 
                   'sebep': f"Güçlü Trend RSI:{son['RSI']:.0f}"}
        return None

class KAZANCKAPISI_7:
    """
    Bollinger Bands Squeeze
    En İyi: 15dk, 1 Saat
    BB daralması = Volatilite sıkışması = Patlama hazırlığı
    """
    @staticmethod
    def analiz(df):
        if df is None or len(df) < 20:
            return None
        
        son = df.iloc[-1]
        bw = (son['BB_Upper'] - son['BB_Lower']) / son['BB_Mid']
        avg_bw = ((df['BB_Upper'] - df['BB_Lower']) / df['BB_Mid']).tail(20).mean()
        
        if bw < avg_bw * 0.6:
            return {'skor': 65 + (1 - bw / avg_bw) * 30, 'hedef': son['Close'] * 1.08, 
                   'sebep': "BB Squeeze"}
        return None

class KAZANCKAPISI_8:
    """
    5 Gün Kesintisiz Yükseliş
    En İyi: Günlük
    Ardışık 5 yeşil mum + %5+ artış
    """
    @staticmethod
    def analiz(df):
        if df is None or len(df) < 5:
            return None
        
        son_5 = df.tail(5)
        if all(son_5['Close'] > son_5['Open']):
            artis = ((son_5['Close'].iloc[-1] - son_5['Close'].iloc[0]) / son_5['Close'].iloc[0]) * 100
            if artis > 5:
                return {'skor': 75 + min(20, artis), 'hedef': son_5['Close'].iloc[-1] * 1.05, 
                       'sebep': f"5 Yeşil %{artis:.1f}"}
        return None

class KAZANCKAPISI_9:
    """
    Sessiz Güç (Düşük Hacimde Yükseliş)
    En İyi: Günlük, 4 Saat
    Düşük hacim + fiyat artışı = Kurumsal birikim
    """
    @staticmethod
    def analiz(df):
        if df is None or len(df) < 20:
            return None
        
        son_5 = df.tail(5)
        vol_ratio = son_5['Volume'].mean() / df['Vol_MA20'].iloc[-1]
        artis = ((son_5['Close'].iloc[-1] - son_5['Close'].iloc[0]) / son_5['Close'].iloc[0]) * 100
        
        if vol_ratio < 0.7 and artis > 3:
            return {'skor': 70 + min(25, artis * 3), 'hedef': df['Close'].iloc[-1] * 1.10, 
                   'sebep': "Sessiz Güç"}
        return None

class KAZANCKAPISI_10:
    """
    Gap Kapatma Senaryosu
    En İyi: Günlük
    Aşağı gap sonrası %50+ kapatma
    """
    @staticmethod
    def analiz(df):
        if df is None or len(df) < 15:
            return None
        
        for i in range(-15, -2):
            try:
                onceki = df['Close'].iloc[i-1]
                acilis = df['Open'].iloc[i]
                current = df['Close'].iloc[-1]
                gap = onceki - acilis
                
                if (gap / acilis) * 100 > 2:
                    kapanma = ((current - acilis) / gap) * 100
                    if kapanma > 50:
                        return {'skor': 65 + min(30, kapanma / 2), 'hedef': onceki, 
                               'sebep': f"Gap %{kapanma:.0f}"}
            except:
                continue
        return None

# ═══════════════════════════════════════════════════════════════
# TARAMA MOTORU
# ═══════════════════════════════════════════════════════════════

STRATEJILER = [
    KAZANCKAPISI_1, KAZANCKAPISI_2, KAZANCKAPISI_3, KAZANCKAPISI_4,
    KAZANCKAPISI_5, KAZANCKAPISI_6, KAZANCKAPISI_7, KAZANCKAPISI_8,
    KAZANCKAPISI_9, KAZANCKAPISI_10
]

def hisse_tara(sembol, period='3mo', interval='1d', min_skor=60):
    df = veri_cek(sembol, period, interval)
    if df is None:
        return None
    
    sinyaller = []
    for idx, Strateji in enumerate(STRATEJILER, 1):
        sonuc = Strateji.analiz(df)
        if sonuc and sonuc['skor'] >= min_skor:
            sinyaller.append({
                'strateji': f"KAZANCKAPISI_{idx}",
                'skor': sonuc['skor'],
                'hedef': sonuc['hedef'],
                'sebep': sonuc['sebep']
            })
    
    if not sinyaller:
        return None
    
    en_iyi = max(sinyaller, key=lambda x: x['skor'])
    
    return {
        'sembol': sembol.replace('.IS', ''),
        'fiyat': df['Close'].iloc[-1],
        'strateji': en_iyi['strateji'],
        'skor': en_iyi['skor'],
        'hedef': en_iyi['hedef'],
        'potansiyel': ((en_iyi['hedef'] / df['Close'].iloc[-1]) - 1) * 100,
        'sebep': en_iyi['sebep'],
        'sinyal_sayisi': len(sinyaller)
    }

def toplu_tara(hisseler, period='3mo', interval='1d', min_skor=60):
    print("\n" + "═" * 80)
    print(f"🚀 KAZANCKAPISI - {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print("═" * 80)
    print(f"📊 {period} | {interval} | Min Skor:{min_skor} | {len(hisseler)} Hisse")
    print("═" * 80 + "\n")
    
    sonuclar = []
    for i, sembol in enumerate(hisseler, 1):
        print(f"[{i}/{len(hisseler)}] {sembol.replace('.IS', '')}...", end=' ')
        sonuc = hisse_tara(sembol, period, interval, min_skor)
        if sonuc:
            sonuclar.append(sonuc)
            print(f"✅ {sonuc['strateji']} Skor:{sonuc['skor']:.0f}")
        else:
            print("❌")
    
    return sonuclar

# ═══════════════════════════════════════════════════════════════
# TELEGRAM
# ═══════════════════════════════════════════════════════════════

def telegram_gonder(sonuclar):
    if not TELEGRAM_OK:
        print("\n⚠️ pip install pyTelegramBotAPI")
        return False
    
    try:
        bot = telebot.TeleBot(TOKEN)
        now = datetime.now().strftime("%d.%m.%Y %H:%M")
        
        if not sonuclar:
            mesaj = f"⚠️ <b>KAZANCKAPISI</b>\n{now}\n\nSinyal yok"
        else:
            mesaj = f"🚀 <b>KAZANCKAPISI</b>\n{now}\n\n<code>{'═'*40}</code>\n\n"
            for idx, s in enumerate(sonuclar[:15], 1):
                mesaj += f"<b>{idx}. {s['sembol']}</b>\n💰 {s['fiyat']:.2f}₺→🎯{s['hedef']:.2f}₺ (%{s['potansiyel']:.1f})\n📊 {s['strateji']} Skor:{s['skor']:.0f}\n💡 {s['sebep']}\n\n"
            mesaj += f"<code>{'═'*40}</code>\n✅ {len(sonuclar)} fırsat"
        
        bot.send_message(CHAT_ID, mesaj, parse_mode='HTML')
        print("\n✅ Telegram'a gönderildi!")
        return True
    except Exception as e:
        print(f"\n❌ Telegram hatası: {e}")
        return False

# ═══════════════════════════════════════════════════════════════
# SONUÇ TABLOSU
# ═══════════════════════════════════════════════════════════════

def tablo_goster(sonuclar):
    if not sonuclar:
        print("\n⚠️ Sinyal bulunamadı!\n")
        return
    
    df = pd.DataFrame([{
        '#': i,
        'Hisse': s['sembol'],
        'Fiyat': f"{s['fiyat']:.2f}₺",
        'Hedef': f"{s['hedef']:.2f}₺",
        'Pot%': f"{s['potansiyel']:.1f}%",
        'Strateji': s['strateji'],
        'Skor': int(s['skor']),
        'Sinyal': s['sinyal_sayisi']
    } for i, s in enumerate(sonuclar, 1)])
    
    print("\n" + "═" * 100)
    print("🏆 FIRSATLAR")
    print("═" * 100)
    print(df.to_string(index=False))
    print("═" * 100 + "\n")

# ═══════════════════════════════════════════════════════════════
# ANA PROGRAM
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    sonuclar = toplu_tara(
        hisseler=HISSELER,
        period='3mo',
        interval='1d',
        min_skor=60
    )
    
    sonuclar.sort(key=lambda x: x['skor'], reverse=True)
    tablo_goster(sonuclar)
    telegram_gonder(sonuclar)
    print("✅ Tamamlandı!\n")
