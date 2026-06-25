"use client";

import { Screen } from "@/app/dashboard/page";

interface SplashScreenProps {
  onNavigate: (s: Screen) => void;
}

export default function SplashScreen({ onNavigate }: SplashScreenProps) {
  return (
    <div className="w-full h-full flex items-center"
      style={{ background: "linear-gradient(160deg,#03060f 0%,#0c0d22 55%,#060d1c 100%)" }}>

      {/* Left */}
      <div className="flex-1 flex flex-col gap-6 px-16 py-12">
        <span className="font-mono text-[9px] tracking-[0.12em] text-[#818cf8] px-4 py-1.5 rounded-full border border-[rgba(99,102,241,0.28)] bg-[rgba(99,102,241,0.08)] w-fit">
          ● AUTONOMOUS AI ASSISTANT
        </span>

        <div className="font-hud text-[42px] font-black leading-[1.08] text-white">
          Meet the<br />
          <span className="text-[#818cf8]" style={{ textShadow: "0 0 24px rgba(129,140,248,0.55)" }}>
            AVA Mind!
          </span>
        </div>

        <div className="text-[15px] text-[#6878aa] leading-relaxed max-w-[400px]">
          Your personal Jarvis — witty, adaptive, always ready.
          I write code, search the web, read files, remember you, and talk like a real human.
        </div>

        <div className="flex flex-wrap gap-2 max-w-[400px]">
          {["💻 Code & Debug", "🔍 Web Search", "🎙 Voice AI", "🔮 Memory", "📄 Documents", "📊 Data", "⏰ Reminders", "📁 Files"].map(pill => (
            <span key={pill}
              className="font-mono text-[9px] px-3 py-[5px] rounded-full border border-[rgba(99,102,241,0.28)] text-[#6878aa] bg-[rgba(99,102,241,0.06)]">
              {pill}
            </span>
          ))}
        </div>

        <div className="flex flex-col gap-3">
          <button
            onClick={() => onNavigate("home")}
            className="inline-flex items-center gap-3 px-9 py-4 rounded-[18px] font-hud text-[12px] font-bold tracking-[0.12em] text-white uppercase transition-all hover:-translate-y-0.5 w-fit"
            style={{ background: "linear-gradient(135deg,#4f46e5,#6366f1)", boxShadow: "0 8px 28px rgba(99,102,241,0.42)" }}>
            Get Started
            <span style={{ animation: "arrSlide 1.6s ease-in-out infinite" }}>›</span>
          </button>
          <div className="font-mono text-[10px] text-[#2a3660]">Sign in · Create account · Free to start</div>
        </div>
      </div>

      {/* Right — Mascot */}
      <div className="flex-[0_0_480px] flex items-center justify-center">
        <div className="relative w-[320px] h-[320px] flex items-center justify-center">
          <div className="absolute inset-[-30px] rounded-full"
            style={{ background: "radial-gradient(circle,rgba(99,102,241,0.07) 0%,transparent 70%)" }} />
          <div className="absolute inset-0 rounded-full"
            style={{ background: "radial-gradient(circle,rgba(99,102,241,0.16) 0%,transparent 70%)", animation: "orbPulse 3s ease-in-out infinite" }} />

          <svg style={{ position:"relative", zIndex:2, width:260, height:260, animation:"float 3.5s ease-in-out infinite" }} viewBox="0 0 150 150" fill="none">
            <ellipse cx="75" cy="133" rx="36" ry="8" fill="rgba(99,102,241,0.22)"/>
            <rect x="32" y="78" width="86" height="54" rx="22" fill="#1e1b4b"/>
            <rect x="32" y="78" width="86" height="54" rx="22" fill="url(#sg)" opacity="0.45"/>
            <ellipse cx="75" cy="104" rx="14" ry="8.5" fill="rgba(99,102,241,0.22)"/>
            <ellipse cx="75" cy="104" rx="7" ry="4.5" fill="rgba(129,140,248,0.4)"/>
            <ellipse cx="75" cy="104" rx="3" ry="2" fill="rgba(199,210,254,0.6)"/>
            <rect x="30" y="20" width="90" height="66" rx="24" fill="#312e81"/>
            <rect x="30" y="20" width="90" height="66" rx="24" stroke="rgba(129,140,248,0.42)" strokeWidth="1.5"/>
            <ellipse cx="54" cy="54" rx="12" ry="12" fill="#0f0e2a"/>
            <ellipse cx="96" cy="54" rx="12" ry="12" fill="#0f0e2a"/>
            <ellipse cx="54" cy="54" rx="7.5" ry="7.5" fill="#6366f1"/>
            <ellipse cx="96" cy="54" rx="7.5" ry="7.5" fill="#6366f1"/>
            <ellipse cx="54" cy="54" rx="3.8" ry="3.8" fill="#a5b4fc"/>
            <ellipse cx="96" cy="54" rx="3.8" ry="3.8" fill="#a5b4fc"/>
            <ellipse cx="56.5" cy="51" rx="2" ry="2" fill="white" opacity="0.9"/>
            <ellipse cx="98.5" cy="51" rx="2" ry="2" fill="white" opacity="0.9"/>
            <path d="M45 40 Q54 36 63 40" stroke="rgba(165,180,252,0.55)" strokeWidth="2" fill="none" strokeLinecap="round"/>
            <path d="M87 40 Q96 36 105 40" stroke="rgba(165,180,252,0.55)" strokeWidth="2" fill="none" strokeLinecap="round"/>
            <path d="M58 70 Q75 80 92 70" stroke="rgba(199,210,254,0.8)" strokeWidth="2.5" fill="none" strokeLinecap="round"/>
            <ellipse cx="40" cy="64" rx="8" ry="5.5" fill="rgba(167,139,250,0.22)"/>
            <ellipse cx="110" cy="64" rx="8" ry="5.5" fill="rgba(167,139,250,0.22)"/>
            <line x1="57" y1="20" x2="50" y2="7" stroke="#4f46e5" strokeWidth="2.5" strokeLinecap="round"/>
            <circle cx="49" cy="6" r="4.5" fill="#818cf8"/><circle cx="49" cy="6" r="2.2" fill="#c7d2fe"/>
            <line x1="93" y1="20" x2="100" y2="7" stroke="#4f46e5" strokeWidth="2.5" strokeLinecap="round"/>
            <circle cx="101" cy="6" r="4.5" fill="#818cf8"/><circle cx="101" cy="6" r="2.2" fill="#c7d2fe"/>
            <rect x="10" y="80" width="24" height="14" rx="7" fill="#312e81" stroke="rgba(99,102,241,0.28)" strokeWidth="1"/>
            <rect x="116" y="80" width="24" height="14" rx="7" fill="#312e81" stroke="rgba(99,102,241,0.28)" strokeWidth="1"/>
            <rect x="47" y="124" width="22" height="13" rx="7" fill="#1e1b4b"/>
            <rect x="81" y="124" width="22" height="13" rx="7" fill="#1e1b4b"/>
            <defs>
              <linearGradient id="sg" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="rgba(129,140,248,0.5)"/>
                <stop offset="100%" stopColor="transparent"/>
              </linearGradient>
            </defs>
          </svg>

          {/* Speech bubble */}
          <div className="absolute top-10 right-0 z-10 bg-[rgba(10,18,40,0.96)] border border-[rgba(99,102,241,0.28)] rounded-[16px_16px_16px_4px] px-4 py-2">
            <span className="inline-block w-[5px] h-[5px] rounded-full bg-[#818cf8] mr-1.5 align-middle"
              style={{ animation: "heartbeat 1.1s ease-in-out infinite" }} />
            <span className="text-[13px] font-semibold text-[#dde4ff]">Need my help? 🚀</span>
          </div>
        </div>
      </div>

      <style jsx>{`
        @keyframes float { 0%,100%{transform:translateY(0);} 50%{transform:translateY(-12px);} }
        @keyframes orbPulse { 0%,100%{opacity:0.7;transform:scale(1);} 50%{opacity:1;transform:scale(1.06);} }
        @keyframes arrSlide { 0%,100%{transform:translateX(0);} 50%{transform:translateX(6px);} }
        @keyframes heartbeat { 0%,100%{transform:scale(1);opacity:1;} 50%{transform:scale(0.6);opacity:0.5;} }
      `}</style>
    </div>
  );
}
