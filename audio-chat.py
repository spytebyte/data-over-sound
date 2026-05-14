#!/usr/bin/env python3
"""
Two-Way Audio Chat
Bidirectional text communication over sound using FSK
"""

import numpy as np
import sounddevice as sd
from scipy.fft import fft
import threading
import queue
import time
import sys

# Configuration
SAMPLE_RATE = 44100
BIT_DURATION = 0.1
FREQ_0 = 1000
FREQ_1 = 2000
START_FREQ = 3000
STOP_FREQ = 3500
FREQ_TOLERANCE = 100

# Global state
incoming_messages = queue.Queue()
is_listening = True
is_transmitting = False

def text_to_binary(text):
    """Convert text to binary string"""
    return ''.join(format(ord(char), '08b') for char in text)

def binary_to_text(binary_string):
    """Convert binary string to text"""
    if len(binary_string) % 8 != 0:
        binary_string = binary_string[:-(len(binary_string) % 8)]
    
    text = ''
    for i in range(0, len(binary_string), 8):
        byte = binary_string[i:i+8]
        try:
            char = chr(int(byte, 2))
            if 32 <= ord(char) <= 126:  # Printable ASCII only
                text += char
            else:
                text += '?'
        except ValueError:
            text += '?'
    return text

def generate_tone(frequency, duration, sample_rate=SAMPLE_RATE):
    """Generate a pure tone at given frequency"""
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    tone = np.sin(2 * np.pi * frequency * t)
    return tone

def detect_frequency(audio_chunk, sample_rate=SAMPLE_RATE):
    """Detect the dominant frequency in an audio chunk using FFT"""
    windowed = audio_chunk * np.hanning(len(audio_chunk))
    fft_data = fft(windowed)
    freqs = np.fft.fftfreq(len(fft_data), 1/sample_rate)
    
    positive_freqs = freqs[:len(freqs)//2]
    magnitude = np.abs(fft_data[:len(fft_data)//2])
    
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

def transmit_message(message, username):
    """Transmit a text message as audio tones"""
    global is_transmitting
    is_transmitting = True
    
    # Add username prefix
    full_message = f"{username}: {message}"
    binary_data = text_to_binary(full_message)
    
    # Build the audio signal
    audio_signal = []
    
    # Start marker
    audio_signal.append(generate_tone(START_FREQ, BIT_DURATION * 2))
    
    # Transmit each bit
    for bit in binary_data:
        freq = FREQ_1 if bit == '1' else FREQ_0
        audio_signal.append(generate_tone(freq, BIT_DURATION))
    
    # Stop marker
    audio_signal.append(generate_tone(STOP_FREQ, BIT_DURATION * 2))
    
    # Concatenate and normalize
    complete_signal = np.concatenate(audio_signal)
    complete_signal = complete_signal / np.max(np.abs(complete_signal)) * 0.8
    
    # Play the audio
    sd.play(complete_signal, SAMPLE_RATE)
    sd.wait()
    
    is_transmitting = False

def audio_callback(indata, frames, time_info, status):
    """Callback for continuous audio input"""
    if status:
        print(f"⚠️  Audio status: {status}", file=sys.stderr)
    
    # Add audio data to processing queue
    if is_listening and not is_transmitting:
        incoming_messages.put(indata.copy())

def process_audio_stream():
    """Process incoming audio stream and decode messages"""
    global is_listening
    
    chunk_size = int(BIT_DURATION * SAMPLE_RATE)
    buffer = np.array([])
    receiving = False
    bits = []
    last_receive_time = time.time()
    
    while is_listening:
        try:
            # Get audio data from queue (with timeout)
            audio_chunk = incoming_messages.get(timeout=0.1)
            buffer = np.append(buffer, audio_chunk[:, 0])
            
            # Process when we have enough data
            while len(buffer) >= chunk_size:
                chunk = buffer[:chunk_size]
                buffer = buffer[chunk_size:]
                
                freq = detect_frequency(chunk)
                bit_type = classify_bit(freq)
                
                # State machine
                if bit_type == 'START' and not receiving:
                    receiving = True
                    bits = []
                    last_receive_time = time.time()
                
                elif bit_type == 'STOP' and receiving:
                    receiving = False
                    
                    if bits:
                        binary_string = ''.join(bits)
                        decoded_message = binary_to_text(binary_string)
                        
                        # Print received message
                        print(f"\n📨 {decoded_message}")
                        print("You: ", end='', flush=True)
                
                elif receiving and bit_type in ['0', '1']:
                    bits.append(bit_type)
                    last_receive_time = time.time()
                
                # Timeout if receiving stalls
                if receiving and (time.time() - last_receive_time) > 2.0:
                    receiving = False
                    bits = []
        
        except queue.Empty:
            continue
        except Exception as e:
            print(f"\n❌ Decode error: {e}", file=sys.stderr)

def main():
    global is_listening
    
    print("\n" + "="*60)
    print("   🎙️  TWO-WAY AUDIO CHAT")
    print("="*60)
    print("This chat transmits your messages as audio tones.")
    print("Both users need to run this program simultaneously.")
    print("="*60)
    
    # Get username
    username = input("\nEnter your username: ").strip()
    if not username:
        username = "Anonymous"
    
    print(f"\n✅ Signed in as: {username}")
    print("\n📡 Configuration:")
    print(f"   Frequency for '0': {FREQ_0} Hz")
    print(f"   Frequency for '1': {FREQ_1} Hz")
    print(f"   Bit duration: {BIT_DURATION} seconds")
    print(f"   ~{1/BIT_DURATION:.0f} bits per second")
    
    print("\n" + "="*60)
    print("INSTRUCTIONS:")
    print("1. Make sure your microphone and speakers are working")
    print("2. Adjust volume to medium level (50-70%)")
    print("3. Type your message and press Enter to send")
    print("4. Messages from others will appear automatically")
    print("5. Type 'quit' to exit")
    print("="*60)
    
    input("\nPress Enter when ready to start chat...")
    
    # Start audio input stream
    print("\n🎤 Listening for incoming messages...")
    print("💬 You can start chatting now!\n")
    
    # Start the audio processing thread
    processor_thread = threading.Thread(target=process_audio_stream, daemon=True)
    processor_thread.start()
    
    # Start audio input stream
    try:
        with sd.InputStream(callback=audio_callback, 
                          channels=1, 
                          samplerate=SAMPLE_RATE,
                          blocksize=int(SAMPLE_RATE * 0.05)):  # 50ms blocks
            
            # Main chat loop
            while True:
                try:
                    message = input("You: ").strip()
                    
                    if message.lower() == 'quit':
                        print("\n👋 Goodbye!")
                        is_listening = False
                        break
                    
                    if not message:
                        continue
                    
                    if len(message) > 50:
                        print("⚠️  Message too long (max 50 characters)")
                        continue
                    
                    # Transmit the message
                    print("🔊 Sending...", end='', flush=True)
                    transmit_message(message, username)
                    print("\r✅ Sent!     ")
                
                except KeyboardInterrupt:
                    print("\n\n👋 Chat ended!")
                    is_listening = False
                    break
                except Exception as e:
                    print(f"\n❌ Error: {e}")
    
    except Exception as e:
        print(f"❌ Audio stream error: {e}")
        print("\nTroubleshooting:")
        print("- Check microphone permissions")
        print("- Verify audio devices are connected")
        print("- Try adjusting sample rate or block size")
    
    # Cleanup
    time.sleep(0.5)
    print("\n" + "="*60)

if __name__ == "__main__":
    main()