"""
afnan_predictor.py
Streamlit web app for predicting next opponents in Magic Chess GOGO (Afnan Predictor)
Created by Aby
"""

import streamlit as st
from typing import List, Set, Optional
import pandas as pd

st.set_page_config(page_title="Afnan Predictor", layout="centered")

st.title("Afnan Predictor — Magic Chess GOGO")
st.markdown("Aplikasi ringan untuk memprediksi lawan berikutnya berdasarkan pola rotasi adaptif dan daftar pemain hidup. Cocok dibuka di HP Android lewat browser.")

# --- Utilities ---
def generate_offsets_for_slot6() -> List[int]:
    # Observed offsets for slot 6 derived from loop [5,3,4,1,2,7,8]
    return [7,5,6,3,4,1,2]

def offsets_to_loop_for_slot(slot: int, offsets: List[int]) -> List[int]:
    loop = []
    for off in offsets:
        op = (slot + off) % 8
        if op == 0:
            op = 8
        if op == slot:
            continue
        loop.append(op)
    if len(loop) != 7:
        loop = [i for i in range(1,9) if i != slot]
    return loop

def next_opponent_from_loop(player_loop: List[int], alive: Set[int], round_number: int) -> Optional[int]:
    if not player_loop:
        return None
    if len(alive) <= 1:
        return None
    n = len(player_loop)
    start_idx = (round_number - 1) % n
    for i in range(n):
        idx = (start_idx + i) % n
        candidate = player_loop[idx]
        if candidate in alive:
            return candidate
    return None

# --- UI Inputs ---
cols = st.columns([1,1,1])
with cols[0]:
    slot = st.selectbox("Pilih slot kamu (1–8)", list(range(1,9)), index=5)
with cols[1]:
    round_now = st.number_input("Ronde PvP (misal: 1 untuk 1-2, 2 untuk 1-3, dst)", min_value=1, value=1, step=1)
with cols[2]:
    auto_advance = st.checkbox("Auto-advance saat 'Lanjut'", value=True)

st.markdown("---")

# Player names (optional)
default_names = {i: f"Player {i}" for i in range(1,9)}
if "player_names" not in st.session_state:
    st.session_state.player_names = default_names.copy()

with st.expander("(Optional) Edit nama pemain"):
    for i in range(1,9):
        st.session_state.player_names[i] = st.text_input(f"Nama pemain {i}", value=st.session_state.player_names[i], key=f"name_{i}")

# Alive checkboxes
if "alive" not in st.session_state:
    st.session_state.alive = set(range(1,9))

st.write("**Pemain hidup (klik untuk toggle gugur / hidup):**")
cols_alive = st.columns(4)
for idx, p in enumerate(range(1,9)):
    c = cols_alive[idx % 4]
    label = f"{p}. {st.session_state.player_names[p]}"
    if c.button(label, key=f"alive_btn_{p}"):
        if p in st.session_state.alive:
            st.session_state.alive.remove(p)
        else:
            st.session_state.alive.add(p)

st.write("Pemain hidup saat ini:", sorted(list(st.session_state.alive)))

# Generate loop automatically (adaptive approach)
offsets = generate_offsets_for_slot6()
player_loop = offsets_to_loop_for_slot(slot, offsets)

st.markdown("---")
st.subheader("Loop (urutan lawan yang digunakan oleh algoritme)")
st.write(player_loop)
st.caption("Loop ini di-generate adaptif dari pola yang teramati; bisa diabaikan jika kamu pakai custom loop.")

use_custom = st.checkbox("Gunakan loop kustom (atur sendiri)")
if use_custom:
    custom_text = st.text_input("Masukkan urutan lawan, dipisah koma (contoh: 5,3,4,1,2,7,8)")
    if custom_text:
        try:
            parsed = [int(x.strip()) for x in custom_text.split(",") if x.strip()]
            parsed = [x for x in parsed if 1 <= x <= 8 and x != slot]
            if len(parsed) >= 1:
                player_loop = parsed
        except Exception:
            st.warning("Format tidak valid — pakai angka 1–8, pisah koma")

alive_set = set(st.session_state.alive)
pred = next_opponent_from_loop(player_loop, alive_set, round_now)

if pred is None:
    st.error("Tidak ada lawan (mungkin hanya kamu yang tersisa).")
else:
    st.metric("Prediksi lawan berikutnya", f"{pred}. {st.session_state.player_names[pred]}")

# --- History and Controls ---
if "history" not in st.session_state:
    st.session_state.history = []

cols2 = st.columns([1,1,1])
with cols2[0]:
    if st.button("Lanjut ke ronde berikut"):
        st.session_state.history.append({
            "round": round_now,
            "slot": slot,
            "opponent": pred,
            "alive_before": sorted(list(alive_set))
        })
        if auto_advance:
            st.session_state.round_now = round_now + 1
            st.experimental_rerun()
with cols2[1]:
    if st.button("Tandai lawan gugur (jika tereliminasi setelah ronde ini)"):
        if pred is not None and pred in st.session_state.alive:
            st.session_state.alive.remove(pred)
            st.success(f"Tandai: pemain {pred} ({st.session_state.player_names[pred]}) gugur")
            st.session_state.history.append({
                "round": round_now,
                "slot": slot,
                "opponent": pred,
                "alive_before": sorted(list(alive_set)),
                "eliminated": True
            })
            st.experimental_rerun()
        else:
            st.warning("Tidak ada prediksi lawan valid untuk ditandai gugur.")
with cols2[2]:
    if st.button("Reset match"):
        st.session_state.alive = set(range(1,9))
        st.session_state.history = []
        st.session_state.round_now = 1
        st.experimental_rerun()

st.markdown("---")
st.subheader("Riwayat (log) pertandingan")
if st.session_state.history:
    df = pd.DataFrame(st.session_state.history)
    st.dataframe(df)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download log CSV", data=csv, file_name="afnan_gogo_log.csv", mime="text/csv")
else:
    st.write("Belum ada riwayat. Tekan 'Lanjut ke ronde berikut' untuk mulai mencatat.")

st.markdown("---")
st.caption("Catatan: algoritme menggunakan pola adaptif yang dihasilkan dari pola yang teramati. Jika kamu menemukan perbedaan di lapangan, aktifkan 'Loop kustom' dan masukkan urutan lawan yang kamu lihat.")

st.write('---') 
st.write('Created by Aby') 
