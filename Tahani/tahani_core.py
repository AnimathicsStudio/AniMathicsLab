import pandas as pd
import streamlit as st

def to_fuzzy_tahani(x, min_val, max_val):
    x, min_val, max_val = list(map(float, [x, min_val, max_val]))
    tengah = (min_val + max_val) / 2
    
    # Fuzzy Tahani untuk 'Rendah' = (min, min, tengah)
    if x <= min_val:
        rendah = 1
    elif min_val < x <= tengah:
        rendah = (tengah - x) / (tengah - min_val)
    else:
        rendah = 0
    
    # Fuzzy Tahani untuk 'Sedang' = (min, tengah, max)
    if x <= min_val:
        sedang = 0
    elif min_val < x <= tengah:
        sedang = (x - min_val) / (tengah - min_val)
    elif tengah < x <= max_val:
        sedang = (max_val - x) / (max_val - tengah)
    else:
        sedang = 0
    
    # Fuzzy Tahani untuk 'Tinggi' = (tengah, max, max)
    if x <= tengah:
        tinggi = 0
    elif tengah < x <= max_val:
        tinggi = (x - tengah) / (max_val - tengah)
    else:
        tinggi = 1
    
    return {'rendah': rendah, 'sedang': sedang, 'tinggi': tinggi}

def hitung_skor(derajat_keanggotaan, nilai_pengguna):
    return (
        derajat_keanggotaan['rendah'] * (1 - nilai_pengguna) +
        derajat_keanggotaan['sedang'] * (1 - abs(nilai_pengguna - 0.5) * 2) +
        derajat_keanggotaan['tinggi'] * nilai_pengguna
    )

def hitung_rekomendasi(pilihan_user, df):
    Skor = []
    
    for idx, baris in df.iterrows():
        SemuaDjtKeanggotaan = {}
        for fitur in pilihan_user:
            if fitur != 'df' and fitur in df.columns:
                nilai_min = df[fitur].min()
                nilai_max = df[fitur].max()
                SemuaDjtKeanggotaan[fitur] = to_fuzzy_tahani(baris[fitur], nilai_min, nilai_max)
        
        skor_total = 0
        for fitur, derajat_keanggotaan in SemuaDjtKeanggotaan.items():
            nilai_pengguna = pilihan_user[fitur]
            skor = hitung_skor(derajat_keanggotaan, nilai_pengguna)
            skor_total += skor
        
        Skor.append(skor_total)
    
    df['Skor'] = Skor
    df_sorted = df.sort_values(by='Skor', ascending=False)
    return df_sorted