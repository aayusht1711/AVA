"use client";

import { useState, useEffect } from "react";
import { Screen } from "@/app/dashboard/page";

const GREETINGS = ["Hello.", "Namaste.", "Hola.", "Bonjour.", "Welcome to AVA."];

interface SplashScreenProps {
  onNavigate: (s: Screen) => void;
}

export default function SplashScreen({ onNavigate }: SplashScreenProps) {
  const [step, setStep] = useState(0);
  const [greetingIndex, setGreetingIndex] = useState(0);
  const [fade, setFade] = useState(false);

  useEffect(() => {
    if (step === 0) {
      // Cycle through greetings
      let i = 0;
      setFade(true);
      const interval = setInterval(() => {
        setFade(false);
        setTimeout(() => {
          i++;
          if (i < GREETINGS.length) {
            setGreetingIndex(i);
            setFade(true);
          } else {
            clearInterval(interval);
            setStep(1); // Move to setup phase
          }
        }, 500); // Wait for fade out
      }, 2500); // 2.5s per greeting

      return () => clearInterval(interval);
    }
  }, [step]);

  useEffect(() => {
    if (step === 1) {
      setFade(true);
    }
  }, [step]);

  function handleComplete(devMode: boolean) {
    if (typeof window !== "undefined") {
      localStorage.setItem("ava_developer_mode", devMode ? "true" : "false");
      localStorage.setItem("ava_first_boot_done", "true");
    }
    onNavigate("home");
  }

  return (
    <div className="w-full h-full flex items-center justify-center bg-black text-white overflow-hidden relative selection:bg-[rgba(99,102,241,0.3)]">
      {/* Background Subtle Glow */}
      <div className="absolute inset-0 pointer-events-none" style={{ background: "radial-gradient(circle at 50% 50%, rgba(99,102,241,0.05) 0%, transparent 60%)" }} />

      {step === 0 && (
        <div 
          className="font-hud text-[48px] md:text-[64px] tracking-widest text-[#dde4ff] transition-opacity duration-1000 ease-in-out"
          style={{ opacity: fade ? 1 : 0 }}
        >
          {GREETINGS[greetingIndex]}
        </div>
      )}

      {step === 1 && (
        <div 
          className="flex flex-col items-center max-w-lg px-6 transition-opacity duration-1000 ease-in-out"
          style={{ opacity: fade ? 1 : 0 }}
        >
          <div className="relative w-20 h-20 mb-8">
            <div className="absolute inset-0 rounded-full border border-[rgba(129,140,248,0.4)]" style={{animation:"spin 5s linear infinite"}}/>
            <div className="absolute inset-[4px] rounded-full border border-[rgba(99,102,241,0.22)]" style={{animation:"spin 9s linear infinite reverse"}}/>
            <div className="absolute inset-[10px] rounded-full" style={{background:"linear-gradient(135deg,#818cf8,#4f46e5)",animation:"orbPulse 2.5s ease-in-out infinite"}}/>
          </div>

          <h1 className="font-hud text-3xl md:text-4xl font-bold mb-4 text-center tracking-wider text-white">
            Let's set up <span className="text-[#818cf8]">AVA</span>
          </h1>
          <p className="text-[#6878aa] text-center mb-10 font-mono text-sm leading-relaxed">
            AVA is your autonomous virtual assistant. Before we start, how would you like your interface?
          </p>

          <div className="flex flex-col md:flex-row gap-4 w-full">
            <button 
              onClick={() => handleComplete(false)}
              className="flex-1 flex flex-col items-center justify-center p-6 rounded-2xl border border-[rgba(99,102,241,0.2)] bg-[rgba(10,18,40,0.4)] hover:bg-[rgba(99,102,241,0.1)] hover:border-[rgba(99,102,241,0.4)] transition-all group"
            >
              <span className="text-3xl mb-3 group-hover:scale-110 transition-transform">✨</span>
              <span className="font-hud text-sm font-bold tracking-widest text-white mb-1">Standard Mode</span>
              <span className="font-mono text-[10px] text-[#6878aa] text-center">Clean, simple interface for everyday use.</span>
            </button>

            <button 
              onClick={() => handleComplete(true)}
              className="flex-1 flex flex-col items-center justify-center p-6 rounded-2xl border border-[rgba(99,102,241,0.2)] bg-[rgba(10,18,40,0.4)] hover:bg-[rgba(99,102,241,0.1)] hover:border-[rgba(99,102,241,0.4)] transition-all group"
            >
              <span className="text-3xl mb-3 group-hover:scale-110 transition-transform">⚙️</span>
              <span className="font-hud text-sm font-bold tracking-widest text-[#818cf8] mb-1">Developer Mode</span>
              <span className="font-mono text-[10px] text-[#6878aa] text-center">Live agent traces and system stats enabled.</span>
            </button>
          </div>
        </div>
      )}

      <style jsx>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes orbPulse { 0%,100%{opacity:0.8;transform:scale(1);} 50%{opacity:1;transform:scale(1.1);} }
      `}</style>
    </div>
  );
}
