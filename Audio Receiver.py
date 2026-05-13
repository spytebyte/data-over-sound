#!/usr/bin/env python3
"""
Audio Data Receiver
Captures audio and decodes binary data transmitted as tones using FSK
"""

import numpy as np
import sounddevice as sd
from scipy import signal
from scipy.fft import fft
import time

# Configuration (must match sender)
SAMPLE_RATE = 44100
BIT_DURATION = 0.1
FREQ_0 = 1000
FREQ_1 = 2000
START_FREQ = 3000
STOP_FREQ = 3500

# Detection parameters
FREQ_TOLERANCE = 100  # Hz tolerance for frequency detection

def detect_frequency(audio_chunk, sample_rate=SAMPLE_RATE):
    """Detect the dominant frequency in an audio chunk using FFT"""
    # Apply window to reduce spectral leakage
    windowed = audio_chunk * np.hanning(len(audio_chunk))
    
    # Compute FFT
    fft_data = fft(windowed)
    freqs = np.fft.fftfreq(len(fft_data), 1/sample_rate)
    
    # Only look at positive frequencies
    positive_freqs = freqs[:len(freqs)//2]
    magnitude = np.abs(fft_data[:len(fft_data)//2])
    
    # Find peak frequency
    peak_idx = np.argmax(magnitude)
    detected_freq = abs(positive_freqs[peak_idx])
    
    return detected_freq

def classify_bit(frequency):
    """Classify a frequency as 0, 1, START, STOP, or UNKNOWN"""
    if abs(frequency - FREQ_0) < FREQ_TOLERANCE:
        return '0'
    elif abs(frequency - FREQ_1) < FREQ_TOLERANCE:
        return '1'
    elif abs(frequency - START_FREQ) < FREQ_TOLERANCE:
        return 'START'
    elif abs(frequency - STOP_FREQ) < FREQ_TOLERANCE:
        return 'STOP'
    else:
        return 'UNKNOWN'

def binary_to_text(binary_string):
    """Convert binary string to text"""
    # Ensure length is multiple of 8
    if len(binary_string) % 8 != 0:
        print(f"⚠️  Warning: Binary length {len(binary_string)} not multiple of 8")
        # Pad or truncate
        binary_string = binary_string[:-(len(binary_string) % 8)] if len(binary_string) % 8 else binary_string
    
    text = ''
    for i in range(0, len(binary_string), 8):
        byte = binary_string[i:i+8]
        try:
            char = chr(int(byte, 2))
            text += char
        except ValueError:
            text += '?'
    
    return text

def receive_message(duration=10):
    """Record audio and decode the message"""
    print(f"\n{'='*50}")
    print(f"LISTENING FOR {duration} SECONDS...")
    print(f"{'='*50}")
    print("🎤 Recording... (make sure sender is ready!)\n")
    
    # Record audio
    recording = sd.rec(int(duration * SAMPLE_RATE), 
                      samplerate=SAMPLE_RATE, 
                      channels=1, 
                      dtype='float64')
    sd.wait()
    
    print("✅ Recording complete! Decoding...\n")
    
    # Process audio in chunks
    chunk_size = int(BIT_DURATION * SAMPLE_RATE)
    num_chunks = len(recording) // chunk_size
    
    bits = []
    receiving = False
    
    for i in range(num_chunks):
        start_idx = i * chunk_size
        end_idx = start_idx + chunk_size
        chunk = recording[start_idx:end_idx, 0]
        
        # Detect frequency in this chunk
        freq = detect_frequency(chunk)
        bit_type = classify_bit(freq)
        
        # State machine for START/STOP markers
        if bit_type == 'START' and not receiving:
            print("🟢 START marker detected!")
            receiving = True
            continue
        
        if bit_type == 'STOP' and receiving:
            print("🔴 STOP marker detected!")
            receiving = False
            break
        
        # Collect data bits
        if receiving and bit_type in ['0', '1']:
            bits.append(bit_type)
            if len(bits) % 8 == 0:
                print(f"   Received {len(bits)//8} characters...")
    
    # Decode the message
    if bits:
        binary_string = ''.join(bits)
        print(f"\n{'='*50}")
        print(f"DECODED DATA:")
        print(f"{'='*50}")
        print(f"Binary: {binary_string}")
        print(f"Total bits: {len(bits)}")
        
        decoded_message = binary_to_text(binary_string)
        print(f"\n📨 MESSAGE: '{decoded_message}'")
        print(f"{'='*50}\n")
        
        return decoded_message
    else:
        print("❌ No data received. Make sure:")
        print("   1. Sender is transmitting")
        print("   2. Volume is adequate")
        print("   3. Microphone is working")
        return None

def main():
    print("\n" + "="*50)
    print("   AUDIO DATA RECEIVER")
    print("="*50)
    print(f"Listening for:")
    print(f"  '0' bit: {FREQ_0} Hz")
    print(f"  '1' bit: {FREQ_1} Hz")
    print(f"  START: {START_FREQ} Hz")
    print(f"  STOP: {STOP_FREQ} Hz")
    print("="*50)
    
    while True:
        choice = input("\n[L]isten for message, [T]est microphone, or [Q]uit? ").strip().upper()
        
        if choice == 'Q':
            print("Goodbye!")
            break
        
        elif choice == 'T':
            print("\n🎤 Recording 3 seconds of audio to test microphone...")
            test_rec = sd.rec(int(3 * SAMPLE_RATE), 
                             samplerate=SAMPLE_RATE, 
                             channels=1)
            sd.wait()
            max_amplitude = np.max(np.abs(test_rec))
            print(f"✅ Max amplitude: {max_amplitude:.4f}")
            if max_amplitude < 0.01:
                print("⚠️  Very quiet! Check microphone settings.")
            elif max_amplitude > 0.8:
                print("⚠️  Very loud! May cause clipping.")
            else:
                print("✅ Microphone level looks good!")
        
        elif choice == 'L':
            duration = input("Recording duration in seconds (default 10): ").strip()
            duration = int(duration) if duration.isdigit() else 10
            
            try:
                receive_message(duration)
            except KeyboardInterrupt:
                print("\n\nReceiving interrupted!")
            except Exception as e:
                print(f"❌ Error: {e}")
        
        else:
            print("Invalid choice!")

if __name__ == "__main__":
    main()