#!/usr/bin/env python3
"""
Audio Data Transmitter
Converts text to binary and transmits as audio tones using FSK (Frequency Shift Keying)
"""

import numpy as np
import sounddevice as sd
import time

# Configuration
SAMPLE_RATE = 44100  # Hz
BIT_DURATION = 0.1   # seconds per bit
FREQ_0 = 1000        # Hz for binary '0'
FREQ_1 = 2000        # Hz for binary '1'
START_FREQ = 3000    # Hz - signal start marker
STOP_FREQ = 3500     # Hz - signal end marker

def text_to_binary(text):
    """Convert text to binary string"""
    binary = ''.join(format(ord(char), '08b') for char in text)
    return binary

def generate_tone(frequency, duration, sample_rate=SAMPLE_RATE):
    """Generate a pure tone at given frequency"""
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    tone = np.sin(2 * np.pi * frequency * t)
    return tone

def transmit_message(message):
    """Transmit a text message as audio tones"""
    print(f"\n{'='*50}")
    print(f"TRANSMITTING: '{message}'")
    print(f"{'='*50}")
    
    # Convert to binary
    binary_data = text_to_binary(message)
    print(f"Binary: {binary_data}")
    print(f"Total bits: {len(binary_data)}")
    print(f"Transmission time: ~{len(binary_data) * BIT_DURATION + 0.4:.1f} seconds")
    
    # Build the audio signal
    audio_signal = []
    
    # Start marker
    print("\n🔊 Sending START marker...")
    audio_signal.append(generate_tone(START_FREQ, BIT_DURATION * 2))
    
    # Transmit each bit
    print("🔊 Sending data bits...")
    for i, bit in enumerate(binary_data):
        freq = FREQ_1 if bit == '1' else FREQ_0
        audio_signal.append(generate_tone(freq, BIT_DURATION))
        
        # Progress indicator
        if (i + 1) % 8 == 0:
            char_index = i // 8
            if char_index < len(message):
                print(f"   Sent character {char_index + 1}/{len(message)}: '{message[char_index]}'")
    
    # Stop marker
    print("🔊 Sending STOP marker...")
    audio_signal.append(generate_tone(STOP_FREQ, BIT_DURATION * 2))
    
    # Concatenate all tones
    complete_signal = np.concatenate(audio_signal)
    
    # Normalize to prevent clipping
    complete_signal = complete_signal / np.max(np.abs(complete_signal)) * 0.8
    
    # Play the audio
    print("\n▶️  PLAYING AUDIO...")
    sd.play(complete_signal, SAMPLE_RATE)
    sd.wait()
    
    print("✅ Transmission complete!\n")

def main():
    print("\n" + "="*50)
    print("   AUDIO DATA TRANSMITTER")
    print("="*50)
    print(f"Frequency for '0': {FREQ_0} Hz")
    print(f"Frequency for '1': {FREQ_1} Hz")
    print(f"Bit duration: {BIT_DURATION} seconds")
    print(f"Start marker: {START_FREQ} Hz")
    print(f"Stop marker: {STOP_FREQ} Hz")
    print("="*50)
    
    while True:
        message = input("\nEnter message to transmit (or 'quit' to exit): ").strip()
        
        if message.lower() == 'quit':
            print("Goodbye!")
            break
        
        if not message:
            print("⚠️  Please enter a message")
            continue
        
        if len(message) > 50:
            print("⚠️  Message too long (max 50 characters)")
            continue
        
        try:
            transmit_message(message)
            time.sleep(0.5)
        except KeyboardInterrupt:
            print("\n\nTransmission interrupted!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()