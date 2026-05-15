# Audio Data Transmission Project

Transmit text messages over sound using your computer's speakers and microphone.

## What This Does

Converts text → binary → audio tones → transmits through air → decodes back to text

- **Binary '0'** = 1000 Hz tone
- **Binary '1'** = 2000 Hz tone
- Speed: ~1.25 characters per second

## Setup

```bash
pip install numpy scipy sounddevice
```

## The Scripts

### 1. One-Way Communication

**Sender** (`Audio Sender.py`):
- Type a message
- Plays it as audio tones
- Use for testing

**Receiver** (`Audio Receiver.py`):
- Listens for incoming tones
- Decodes and displays the message
- Use for testing

**How to use:**
```bash
# Terminal 1
python Audio Receiver.py
# Choose [L]isten, enter 10 seconds

# Terminal 2 (while receiver is listening!)
python Audio Sender.py
# Type "HELLO" and press Enter
```

### 2. Two-Way Chat

**Real-Time** (`audio-chat.py`)
- Both can send anytime
- Messages appear automatically

**How to use:**
```bash
# Both people run:
python audio-chat.py

# Just type messages and press Enter
# No need to coordinate turns
```

## Quick Tips

1. **Volume**: Set to 50-70%
2. **Distance**: Start 1-3 feet apart
3. **Timing**: Receiver must be listening BEFORE sender transmits
4. **Environment**: Quiet room works best
5. **Start simple**: Test with "HI" before longer messages

## Troubleshooting

**No message received?**
- Increase volume
- Move devices closer
- Make sure receiver started listening first

**Garbled text?**
- Lower volume (might be too loud)
- Reduce background noise
- Try shorter messages

**Message too long?**
- Each character takes ~0.8 seconds
- 10 characters = ~10 seconds minimum
- Increase listen duration if needed
