"use client";

import { useEffect, useState } from "react";
import { Screen } from "@/app/dashboard/page";
import { signOut } from "next-auth/react";

interface TopBarProps {
  screen: Screen;
  onNavigate: (s: Screen) => void;
  userName: string;
}

const TABS: { id: Screen; label: string; icon: string }[] = [
  { id: "voice",  label: "Voice",  icon: "🎙" },
  { id: "splash", label: "Splash", icon: "✦" },
  { id: "home",   label: "Home",   icon: "⌂" },
  { id: "chat",   label: "Chat",   icon: "💬" },
  { id: "memory", label: "Memory", icon: "🔮" },
  { id: "tasks",  label: "Tasks",  icon: "⏰" },
  { id: "files",  label: "Files",  icon: "📁" },
];

export default function TopBar({ screen, onNavigate, userName }: TopBarProps) {
  const [time, setTime] = useState("");

  useEffect(() => {
    const tick = () => {
      const n = new Date();
      setTime([n.getHours(), n.getMinutes(), n.getSeconds()]
        .map(v => String(v).padStart(2, "0")).join(":"));
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="h-[52px] flex-shrink-0 flex items-center justify-between px-5
      bg-[rgba(3,6,15,0.98)] border-b border-[rgba(99,102,241,0.22)] relative z-20 overflow-hidden">

      {/* Bottom glow line */}
      <div className="absolute bottom-0 left-0 right-0 h-px pointer-events-none"
        style={{ background: "linear-gradient(90deg,transparent,#818cf8,transparent)", opacity: 0.16 }} />

      {/* Brand */}
      <div className="flex items-center gap-3">
        <div className="w-2 h-2 rounded-full bg-[#86efac] flex-shrink-0"
          style={{ boxShadow: "0 0 8px #86efac", animation: "heartbeat 2.2s ease-in-out infinite" }} />
        <div>
          <div className="font-hud text-[17px] font-black text-[#818cf8] tracking-[0.18em] leading-none"
            style={{ textShadow: "0 0 16px rgba(129,140,248,0.35)" }}>
            AVA
          </div>
          <div className="font-mono text-[8px] text-[#2a3660] tracking-wide">
            Autonomous Virtual Assistant · v1.0
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1">
        {TABS.map(tab => (
          <button
            key={tab.id}
            onClick={() => onNavigate(tab.id)}
            className={`font-hud text-[8px] tracking-[0.1em] uppercase px-4 py-[5px] rounded-full
              border transition-all duration-200 ${
              screen === tab.id
                ? "text-[#818cf8] border-[rgba(99,102,241,0.42)] bg-[rgba(99,102,241,0.08)]"
                : "text-[#2a3660] border-transparent hover:text-[#6878aa] hover:border-[rgba(99,102,241,0.1)]"
            }`}
          >
            {tab.icon} {tab.label}
          </button>
        ))}
      </div>

      {/* Right: chips + clock + user */}
      <div className="flex items-center gap-2">
        <div className="flex items-center gap-1 font-mono text-[9px] px-[10px] py-[3px] rounded-full border
          border-[rgba(134,239,172,0.28)] text-[#86efac] bg-[rgba(134,239,172,0.05)]">
          <span className="w-1 h-1 rounded-full bg-[#86efac] inline-block"
            style={{ animation: "heartbeat 1.5s ease-in-out infinite" }} />
          All Systems Online
        </div>
        <div className="flex items-center gap-1 font-mono text-[9px] px-[10px] py-[3px] rounded-full border
          border-[rgba(99,102,241,0.28)] text-[#818cf8] bg-[rgba(99,102,241,0.05)]">
          <span className="w-1 h-1 rounded-full bg-[#818cf8] inline-block"
            style={{ animation: "heartbeat 1.5s ease-in-out infinite" }} />
          Groq · Gemini
        </div>
        <div className="font-hud text-[13px] font-bold text-[#818cf8] tracking-[0.12em] min-w-[64px] text-right"
          style={{ textShadow: "0 0 10px rgba(129,140,248,0.28)" }}>
          {time}
        </div>
        <button
          onClick={() => signOut({ callbackUrl: "/login" })}
          className="w-[30px] h-[30px] rounded-full bg-[rgba(99,102,241,0.12)] border border-[rgba(99,102,241,0.28)]
            flex items-center justify-center text-[13px] cursor-pointer transition-all
            hover:bg-[rgba(99,102,241,0.22)]"
          title={`Signed in as ${userName}`}
        >
          👤
        </button>
      </div>

      <style jsx>{`
        @keyframes heartbeat {
          0%,100% { transform:scale(1);opacity:1; }
          50% { transform:scale(0.6);opacity:0.5; }
        }
      `}</style>
    </div>
  );
}
