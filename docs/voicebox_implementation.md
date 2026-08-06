# Voicebox — AnswerFirst AI Implementation Guide

## Repo Summary
- Source: https://github.com/jamiepine/voicebox
- Local clone: `C:\Users\azelt\repos\voicebox`
- What it is: open-source local AI voice studio for voice cloning, TTS, dictation, and MCP agent voice I/O
- Core value for AnswerFirst AI: automated inbound/outbound call handling, voice clones for receptionists, transcription of calls, agent voice integrations

## Windows Reality Check
- The repo’s primary dev path assumes macOS/Linux + Tauri desktop + optional GPU acceleration
- On this Windows host, the realistic path is backend-only via FastAPI + CPU-safe engines
- Treat the full Tauri desktop app as reference architecture, not the immediate deployment target

## Backend Capabilities To Use
- `POST /speak` — generate speech from text with a voice profile
- `POST /generate` — full generation request
- `GET /profiles` — list voice profiles
- `POST /profiles` — create profile from sample audio
- `POST /transcribe` — transcribe audio via Whisper
- MCP server at `/mcp` for agent voice integration

## TTS Engine Priority For This Machine
1. Kokoro — tiny CPU-friendly model, preset voices available
2. LuxTTS — lightweight, CPU-capable
3. Qwen3-TTS / CustomVoice — higher quality but heavier
4. Chatterbox Multilingual — broad coverage, heavier
5. Hume TADA — heavier, likely not practical here
6. Chatterbox Turbo — expressive tags, heavier
7. MLX — macOS only, skip on Windows

## AnswerFirst AI Call Handling Integration
1. Run `uvicorn backend.main:app --host 127.0.0.1 --port 17493`
2. Create a receptionist voice profile
3. Use `/speak` for outbound call scripts and IVR responses
4. Use `/transcribe` to convert inbound call recordings to text
5. Log call outcomes into `C:\Users\azelt\answerfirst-ai\dashboard\outreach.json`
6. Hook CRM updates from transcription + call events

## Files Modified For Integration
- `C:\Users\azelt\answerfirst-ai\docs\voicebox_implementation.md` — this file
- `C:\Users\azelt\answerfirst-ai\dashboard\index.html` — will be patched to show call metrics
- `C:\Users\azelt\answerfirst-ai\outreach\outreach_engine.py` — will be extended with Voicebox call logging

## Next Steps
1. Install backend Python deps
2. Start backend server
3. Create first voice profile
4. Test `/speak` and `/transcribe`
5. Wire into dashboard and outreach engine
