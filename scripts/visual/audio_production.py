#!/usr/bin/env python3
"""
Audio Production — Procedural Sound Design
============================================
Generate layered sound effects using scipy signal processing.
Demonstrates professional sound design principles:
layered construction, frequency domain control, envelope shaping.
"""

import numpy as np
import soundfile as sf
from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).parent.parent.parent
OUTPUT = PROJECT_ROOT / "artifacts" / "visual" / "mastery_audio"
OUTPUT.mkdir(parents=True, exist_ok=True)

SAMPLE_RATE = 44100

def envelope(length, attack=0.01, decay=0.1, sustain=0.7, release=0.3, sr=SAMPLE_RATE):
    """Generate ADSR envelope."""
    total_samples = int(length * sr)
    attack_samples = int(attack * sr)
    decay_samples = int(decay * sr)
    release_samples = int(release * sr)
    sustain_samples = total_samples - attack_samples - decay_samples - release_samples

    env = np.concatenate([
        np.linspace(0, 1, attack_samples),
        np.linspace(1, sustain, decay_samples),
        np.full(sustain_samples, sustain),
        np.linspace(sustain, 0, release_samples),
    ])
    return env[:total_samples]

def layer_signals(signals, gains=None):
    """Layer multiple signals with individual gains."""
    if gains is None:
        gains = [1.0] * len(signals)
    max_len = max(len(s) for s in signals)
    result = np.zeros(max_len)
    for sig, gain in zip(signals, gains):
        padded = np.zeros(max_len)
        padded[:len(sig)] = sig
        result += padded * gain
    return result / max(abs(result).max(), 1e-10)

def lowpass(signal, cutoff, sr=SAMPLE_RATE, order=4):
    """Simple lowpass filter."""
    from scipy.signal import butter, filtfilt
    nyq = sr / 2
    b, a = butter(order, cutoff / nyq, btype='low')
    return filtfilt(b, a, signal)

def highpass(signal, cutoff, sr=SAMPLE_RATE, order=4):
    """Simple highpass filter."""
    from scipy.signal import butter, filtfilt
    nyq = sr / 2
    b, a = butter(order, cutoff / nyq, btype='high')
    return filtfilt(b, a, signal)

def bandpass(signal, low, high, sr=SAMPLE_RATE, order=4):
    """Bandpass filter."""
    from scipy.signal import butter, filtfilt
    nyq = sr / 2
    b, a = butter(order, [low / nyq, high / nyq], btype='band')
    return filtfilt(b, a, signal)

# ============================================================
# SOUND 1: MAGICAL IMPACT
# ============================================================
def make_magical_impact():
    """
    Layered magical impact:
    - Layer 1: Transient (high-frequency click)
    - Layer 2: Body (low-frequency thump)
    - Layer 3: Spectral element (shimmer/sparkle)
    - Layer 4: Tail (reverb tail)
    - Layer 5: Low-frequency weight
    """
    duration = 1.5
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    # Layer 1: Transient click
    transient = np.random.randn(len(t)) * 0.5
    transient = highpass(transient, 2000)
    transient_env = np.exp(-t * 30)
    transient *= transient_env

    # Layer 2: Body thump
    body = np.sin(2 * np.pi * 60 * t) * np.sin(2 * np.pi * 4 * t)
    body_env = np.exp(-t * 8)
    body *= body_env

    # Layer 3: Spectral shimmer (metallic resonance)
    shimmer = np.sin(2 * np.pi * 800 * t) * 0.3 + np.sin(2 * np.pi * 1200 * t) * 0.2
    shimmer += np.sin(2 * np.pi * 2400 * t) * 0.1
    shimmer_env = np.exp(-t * 5)
    shimmer *= shimmer_env

    # Layer 4: Reverb tail (filtered noise)
    tail = np.random.randn(len(t)) * 0.15
    tail = bandpass(tail, 200, 3000)
    tail_env = np.exp(-t * 2)
    tail *= tail_env

    # Layer 5: Low-frequency weight
    sub = np.sin(2 * np.pi * 35 * t) * 0.4
    sub_env = np.exp(-t * 6)
    sub *= sub_env

    # Mix
    result = layer_signals(
        [transient, body, shimmer, tail, sub],
        gains=[1.0, 0.8, 0.6, 0.5, 0.7]
    )

    # Master envelope
    master_env = envelope(1.5, attack=0.001, decay=0.05, sustain=0.3, release=1.0)
    result *= master_env[:len(result)]

    return result

# ============================================================
# SOUND 2: SWORD WHOOSH
# ============================================================
def make_sword_whoosh():
    """
    Sword swing whoosh:
    - Noise swept through bandpass
    - Doppler pitch shift effect
    - Metallic ring
    """
    duration = 0.8
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    # Filtered noise with swept center frequency
    noise = np.random.randn(len(t))
    # Manual swept filter approximation
    center_freq = np.linspace(200, 2000, len(t))
    whoosh = np.zeros(len(t))
    for i in range(len(t)):
        phase = 2 * np.pi * center_freq[i] * t[i]
        whoosh[i] = noise[i] * np.sin(phase) * 0.3

    whoosh_env = envelope(0.8, attack=0.05, decay=0.1, sustain=0.5, release=0.3)
    whoosh *= whoosh_env[:len(whoosh)]

    # Metallic ring
    ring = np.sin(2 * np.pi * 1500 * t) * np.exp(-t * 8) * 0.15

    # Low whoosh body
    body = lowpass(np.random.randn(len(t)), 300) * np.exp(-t * 4) * 0.4

    result = layer_signals([whoosh, ring, body], gains=[1.0, 0.3, 0.5])
    return result

# ============================================================
# SOUND 3: AMBIENT FOREST
# ============================================================
def make_forest_ambience():
    """
    Forest ambience layer:
    - Wind (filtered noise)
    - Bird-like chirps
    - Rustling leaves
    """
    duration = 4.0
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    # Wind
    wind = np.random.randn(len(t))
    wind = bandpass(wind, 80, 800)
    wind *= 0.15
    wind_env = 0.5 + 0.5 * np.sin(2 * np.pi * 0.3 * t)
    wind *= wind_env

    # Bird chirps (modulated sine)
    chirps = np.zeros(len(t))
    for _ in range(6):
        start = int(np.random.uniform(0.5, 3.5) * SAMPLE_RATE)
        chirp_len = int(0.15 * SAMPLE_RATE)
        if start + chirp_len < len(t):
            ct = np.linspace(0, 0.15, chirp_len)
            freq = np.random.uniform(2000, 4000)
            chirp = np.sin(2 * np.pi * freq * ct + 3 * np.sin(2 * np.pi * 20 * ct))
            chirp_env = np.exp(-ct * 15)
            chirps[start:start + chirp_len] += chirp * chirp_env * 0.2

    # Leaf rustle
    leaves = np.random.randn(len(t))
    leaves = bandpass(leaves, 1000, 8000)
    leaves_env = 0.3 + 0.3 * np.sin(2 * np.pi * 0.5 * t + 1.0)
    leaves *= leaves_env * 0.08

    result = layer_signals([wind, chirps, leaves], gains=[1.0, 0.8, 0.6])

    # Fade in/out
    fade = np.ones(len(result))
    fade_in = int(0.5 * SAMPLE_RATE)
    fade_out = int(0.5 * SAMPLE_RATE)
    fade[:fade_in] = np.linspace(0, 1, fade_in)
    fade[-fade_out:] = np.linspace(1, 0, fade_out)
    result *= fade

    return result

# ============================================================
# SOUND 4: UI CLICK
# ============================================================
def make_ui_click():
    """Clean UI click — subtle, professional."""
    duration = 0.2
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    # High click
    click = np.sin(2 * np.pi * 1800 * t) * np.exp(-t * 60) * 0.3

    # Low body
    body = np.sin(2 * np.pi * 400 * t) * np.exp(-t * 40) * 0.2

    # Soft noise transient
    noise = np.random.randn(len(t)) * 0.1
    noise = highpass(noise, 3000) * np.exp(-t * 80)

    result = layer_signals([click, body, noise], gains=[1.0, 0.5, 0.3])
    return result

# ============================================================
# SOUND 5: MAGIC SPELL CAST
# ============================================================
def make_spell_cast():
    """Magical spell casting — build + release."""
    duration = 2.0
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    # Build-up: rising frequency sweep
    sweep_freq = np.linspace(200, 2000, len(t))
    build = np.sin(2 * np.pi * sweep_freq * t) * 0.3
    build_env = np.minimum(t / 1.0, 1.0) * np.exp(-np.maximum(t - 0.8, 0) * 3)
    build *= build_env

    # Sparkle layer
    sparkle = np.sin(2 * np.pi * 3000 * t) * np.sin(2 * np.pi * 7 * t) * 0.15
    sparkle_env = np.exp(-np.maximum(t - 0.5, 0) * 4)
    sparkle *= sparkle_env

    # Release burst at ~1s
    burst = np.random.randn(len(t)) * 0.2
    burst = bandpass(burst, 500, 4000)
    burst_env = np.exp(-np.maximum(t - 1.0, 0) * 5)
    burst *= burst_env

    # Low resonance
    low = np.sin(2 * np.pi * 80 * t) * np.exp(-np.maximum(t - 1.0, 0) * 6) * 0.4

    result = layer_signals([build, sparkle, burst, low], gains=[1.0, 0.6, 0.8, 0.7])
    return result


if __name__ == "__main__":
    print("=" * 60)
    print("AUDIO PRODUCTION — Procedural Sound Design")
    print("=" * 60)

    sounds = [
        ("magical_impact", make_magical_impact, "Layered magical impact (5 layers)"),
        ("sword_whoosh", make_sword_whoosh, "Sword swing whoosh (3 layers)"),
        ("forest_ambience", make_forest_ambience, "Forest ambience (3 layers, 4s)"),
        ("ui_click", make_ui_click, "Clean UI click (3 layers)"),
        ("spell_cast", make_spell_cast, "Magic spell cast (4 layers, 2s)"),
    ]

    for name, fn, desc in sounds:
        print(f"\n  [{name}] {desc}...", end=" ", flush=True)
        try:
            audio = fn()
            # Normalize
            audio = audio / max(abs(audio).max(), 1e-10) * 0.9
            # Save
            path = OUTPUT / f"{name}.wav"
            sf.write(str(path), audio.astype(np.float32), SAMPLE_RATE)
            duration = len(audio) / SAMPLE_RATE
            sz = os.path.getsize(str(path)) // 1024
            print(f"OK ({duration:.1f}s, {sz}KB)")
        except Exception as e:
            print(f"FAILED: {e}")

    # Summary
    print(f"\n{'='*60}")
    print("AUDIO OUTPUTS:")
    for f in sorted(OUTPUT.glob("*.wav")):
        sz = os.path.getsize(str(f)) // 1024
        print(f"  {f.name} ({sz}KB)")
