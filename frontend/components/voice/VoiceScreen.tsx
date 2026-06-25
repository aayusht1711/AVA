"use client";

import { useState, useRef, useEffect } from "react";
import { Screen } from "@/app/dashboard/page";

interface VoiceScreenProps {
  onNavigate: (s: Screen) => void;
}

export default function VoiceScreen({ onNavigate }: VoiceScreenProps) {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("Go ahead, I'm listening...");
  const [audioAmplitude, setAudioAmplitude] = useState(0);
  
  const mediaRef = useRef<MediaRecorder | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const silenceTimerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    // Initialize WebSocket for Phase 4 Voice Pipeline
    const ws = new WebSocket(`ws://${window.location.host}/api/voice/ws`);
    
    ws.onmessage = async (event) => {
      if (typeof event.data === "string") {
        const msg = JSON.parse(event.data);
        if (msg.type === "stop_audio_stream") {
          // Interrupt: stop current playback
          if (audioContextRef.current) {
            audioContextRef.current.close();
            audioContextRef.current = new AudioContext();
          }
        }
      } else if (event.data instanceof Blob) {
        // Playback incoming ElevenLabs audio chunks
        if (!audioContextRef.current) audioContextRef.current = new AudioContext();
        const arrayBuffer = await event.data.arrayBuffer();
        const audioBuffer = await audioContextRef.current.decodeAudioData(arrayBuffer);
        const source = audioContextRef.current.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(audioContextRef.current.destination);
        source.start();
      }
    };

    wsRef.current = ws;
    return () => {
      ws.close();
      if (audioContextRef.current) audioContextRef.current.close();
    };
  }, []);

  async function toggleMic() {
    if (isListening) {
      mediaRef.current?.stop();
      setIsListening(false);
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream, { mimeType: "audio/webm" });

      // Setup audio analyzer for amplitude and VAD (Voice Activity Detection)
      const audioCtx = new AudioContext();
      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      const dataArray = new Uint8Array(analyser.frequencyBinCount);

      const checkVolume = () => {
        if (!isListening) return;
        analyser.getByteFrequencyData(dataArray);
        const avg = dataArray.reduce((a, b) => a + b) / dataArray.length;
        setAudioAmplitude(avg);

        // Simple VAD: silence detection > 800ms
        if (avg < 10) {
          if (!silenceTimerRef.current) {
            silenceTimerRef.current = setTimeout(() => {
              if (wsRef.current?.readyState === WebSocket.OPEN) {
                // High priority stop signal
                wsRef.current.send(JSON.stringify({ type: "vad_stop" }));
              }
            }, 800);
          }
        } else {
          if (silenceTimerRef.current) {
            clearTimeout(silenceTimerRef.current);
            silenceTimerRef.current = null;
          }
        }
        requestAnimationFrame(checkVolume);
      };
      checkVolume();

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0 && wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(e.data); // Stream audio chunks to backend
        }
      };

      // Start recording with small timeslices to stream continuously
      recorder.start(250); 
      mediaRef.current = recorder;
      setIsListening(true);
      setTranscript("Listening and streaming...");

    } catch (err) {
      console.error(err);
      setTranscript("Microphone access denied.");
    }
  }

  // Calculate orb dynamic scale based on mic amplitude
  const dynamicScale = 1 + (audioAmplitude / 255) * 0.4;

  return (
    <div className="w-full h-full flex" style={{ background: "linear-gradient(160deg,#03060f 0%,#0a0e28 60%,#060d1c 100%)" }}>

      {/* Left — Orb */}
      <div className="flex-[0_0_50%] flex flex-col items-center justify-center p-10 border-r border-[rgba(99,102,241,0.1)]">
        <div className="relative w-[260px] h-[260px] flex items-center justify-center mb-6"
             style={{ transform: `scale(${dynamicScale})`, transition: "transform 0.05s linear" }}>
          
          <div className="absolute inset-[-28px] rounded-full"
            style={{ background: "radial-gradient(circle,rgba(99,102,241,0.05) 0%,transparent 70%)" }} />
          <div className="absolute inset-[-10px] rounded-full"
            style={{ background: "radial-gradient(circle,rgba(99,102,241,0.1) 0%,transparent 70%)", animation: "orbPulse 2.5s ease-in-out infinite" }} />
          <div className="absolute inset-0 rounded-full border border-[rgba(99,102,241,0.42)]"
            style={{ animation: "spin 7s linear infinite" }} />
          <div className="absolute inset-[18px] rounded-full border border-[rgba(99,102,241,0.24)]"
            style={{ animation: "spin 12s linear infinite reverse" }} />
          <div className="absolute inset-[36px] rounded-full border-dashed border border-[rgba(129,140,248,0.14)]"
            style={{ animation: "spin 5s linear infinite" }} />
          
          {/* Blob core */}
          <div className="absolute inset-[68px] rounded-full"
            style={{
              background: "radial-gradient(circle at 35% 35%,rgba(167,139,250,0.95) 0%,rgba(99,102,241,0.75) 35%,rgba(79,70,229,0.52) 65%,rgba(49,46,129,0.26) 100%)",
              animation: isListening
                ? "blobMorph 2s ease-in-out infinite, orbPulse 1.2s ease-in-out infinite"
                : "blobMorph 4.5s ease-in-out infinite, orbPulse 2.8s ease-in-out infinite",
            }} />
        </div>

        <div className="font-hud text-[12px] tracking-[0.22em] text-[#818cf8] mb-1">
          {isListening ? "AVA IS LISTENING" : "AVA READY"}
        </div>
      </div>

      {/* Right — Controls */}
      <div className="flex-1 flex flex-col justify-center p-12 gap-5">
        <div>
          <div className="font-hud text-[28px] font-black text-[#dde4ff] leading-[1.15] mb-3">
            Talk to <span className="text-[#818cf8]" style={{ textShadow: "0 0 20px rgba(129,140,248,0.45)" }}>AVA</span>
          </div>
          <div className="text-[14px] text-[#6878aa] leading-relaxed max-w-[380px]">
            Just speak — AVA understands natural language. Ask her to write code, search the web,
            set reminders, read files, or just have a real conversation.
          </div>
        </div>

        {/* Transcript */}
        <div className="relative bg-[rgba(10,18,40,0.92)] border border-[rgba(99,102,241,0.22)] rounded-[18px] p-4 overflow-hidden">
          <div className="font-mono text-[8px] text-[#2a3660] tracking-[0.12em] mb-2">LIVE TRANSCRIPT</div>
          <div className="text-[14px] font-medium text-[#dde4ff] leading-relaxed min-h-[40px]">
            {transcript}
          </div>
        </div>

        {/* Mic controls */}
        <div className="flex items-center gap-4">
          <button
            onClick={toggleMic}
            className="flex-1 h-[58px] rounded-[29px] flex items-center justify-center gap-3 font-hud text-[11px] font-bold tracking-[0.12em] text-white uppercase transition-all"
            style={{
              background: isListening
                ? "linear-gradient(135deg,#dc2626,#f87171)"
                : "linear-gradient(135deg,#4f46e5,#6366f1)",
            }}
          >
            {isListening ? "⏹ STOP LISTENING" : "🎙 TAP TO SPEAK"}
          </button>
        </div>
      </div>

      <style jsx>{`
        @keyframes spin { to { transform:rotate(360deg); } }
        @keyframes orbPulse { 0%,100%{opacity:0.7;} 50%{opacity:1;} }
        @keyframes blobMorph { 0%,100%{border-radius:50%;} 25%{border-radius:62% 38% 56% 44%;} 50%{border-radius:44% 56% 38% 62%;} 75%{border-radius:56% 44% 62% 38%;} }
      `}</style>
    </div>
  );
}
