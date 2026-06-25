"use client";

import { Screen } from "@/app/dashboard/page";

interface HomeScreenProps {
  onNavigate: (s: Screen) => void;
  userName: string;
}

const ACTIONS = [
  { icon: "💬", label: "Chat",        sub: "Text conversation", screen: "chat" as Screen },
  { icon: "🎙", label: "Voice",       sub: "Speak to AVA",      screen: "voice" as Screen },
  { icon: "💻", label: "Debug Code",  sub: "E2B sandbox",       screen: "chat" as Screen },
  { icon: "📄", label: "Generate PDF",sub: "ReportLab",         screen: "chat" as Screen },
];

const TOPICS = [
  { icon: "💻", label: "Code" },
  { icon: "🔍", label: "Research" },
  { icon: "📈", label: "Finance" },
  { icon: "📄", label: "Docs" },
  { icon: "📊", label: "Data" },
  { icon: "🎨", label: "Design" },
];

const HISTORY = [
  { icon: "🎙", main: "Debug my Python scraper",      meta: "2 min ago · Coder Agent" },
  { icon: "💬", main: "Generate quarterly PDF report", meta: "1 hr ago · Document Agent" },
  { icon: "🔍", main: "Search latest AI news",         meta: "3 hrs ago · Researcher" },
];

export default function HomeScreen({ onNavigate, userName }: HomeScreenProps) {
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";

  return (
    <div className="w-full h-full overflow-y-auto bg-[#03060f] px-8 py-7 flex flex-col gap-6">

      {/* Top */}
      <div className="flex items-center justify-between flex-shrink-0">
        <div>
          <div className="text-[13px] text-[#6878aa]">{greeting},</div>
          <div className="font-hud text-[22px] font-black text-[#dde4ff] tracking-[0.04em]">
            {userName} 👋
          </div>
        </div>
        <div className="relative w-10 h-10 rounded-full bg-[rgba(10,18,40,0.95)] border border-[rgba(99,102,241,0.22)] flex items-center justify-center text-[17px] cursor-pointer">
          🔔
          <span className="absolute top-2 right-2 w-1.5 h-1.5 rounded-full bg-[#818cf8]"
            style={{ boxShadow: "0 0 5px #6366f1" }} />
        </div>
      </div>

      {/* AVA card */}
      <div onClick={() => onNavigate("chat")}
        className="flex items-center gap-5 px-6 py-5 rounded-[24px] border border-[rgba(99,102,241,0.22)] cursor-pointer transition-all hover:border-[rgba(99,102,241,0.48)] flex-shrink-0 relative overflow-hidden"
        style={{ background: "linear-gradient(135deg,#121f3d,#312e81)" }}>
        <div className="absolute top-[-40%] right-[-10%] w-40 h-40 rounded-full pointer-events-none"
          style={{ background: "radial-gradient(circle,rgba(99,102,241,0.28),transparent 70%)" }} />

        {/* Mini orb */}
        <div className="relative w-[58px] h-[58px] flex-shrink-0">
          <div className="absolute inset-0 rounded-full border border-[rgba(129,140,248,0.42)]"
            style={{ animation: "spin 5s linear infinite" }} />
          <div className="absolute inset-[9px] rounded-full border border-[rgba(99,102,241,0.22)]"
            style={{ animation: "spin 9s linear infinite reverse" }} />
          <div className="absolute inset-[16px] rounded-full"
            style={{ background: "linear-gradient(135deg,#818cf8,#4f46e5)", animation: "orbPulse 2.5s ease-in-out infinite" }} />
        </div>

        <div className="flex-1 relative z-10">
          <div className="font-hud text-[18px] font-bold text-white tracking-[0.08em]">AVA · ONLINE</div>
          <div className="font-mono text-[10px] text-[rgba(165,180,252,0.85)] flex items-center gap-1.5 mt-1">
            <span className="w-1 h-1 rounded-full bg-[#86efac]"
              style={{ boxShadow: "0 0 4px #86efac", animation: "heartbeat 1.2s ease-in-out infinite" }} />
            Ready to assist — Groq Llama 3.3 · Gemini Flash
          </div>
        </div>

        <button onClick={(e) => { e.stopPropagation(); onNavigate("chat"); }}
          className="relative z-10 font-hud text-[9px] tracking-[0.1em] uppercase text-[#818cf8] px-4 py-2.5 rounded-xl border border-[rgba(129,140,248,0.35)] bg-[rgba(99,102,241,0.22)] transition-all hover:bg-[rgba(99,102,241,0.38)]">
          Ask AVA
        </button>
      </div>

      {/* 3-col grid */}
      <div className="grid grid-cols-3 gap-5 flex-shrink-0">

        {/* Quick Actions */}
        <div className="flex flex-col gap-3">
          <div className="font-hud text-[10px] font-bold text-[#dde4ff] tracking-[0.08em]">Quick Actions</div>
          <div className="grid grid-cols-2 gap-2.5">
            {ACTIONS.map(a => (
              <div key={a.label} onClick={() => onNavigate(a.screen)}
                className="bg-[rgba(8,14,30,0.97)] border border-[rgba(99,102,241,0.1)] rounded-[16px] px-3 py-4 flex flex-col items-center gap-2 cursor-pointer transition-all hover:border-[rgba(99,102,241,0.22)]">
                <div className="w-11 h-11 rounded-[13px] bg-[rgba(99,102,241,0.1)] border border-[rgba(99,102,241,0.22)] flex items-center justify-center text-[19px]">
                  {a.icon}
                </div>
                <div className="text-[13px] font-bold text-[#dde4ff] text-center">{a.label}</div>
                <div className="font-mono text-[9px] text-[#2a3660] text-center">{a.sub}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Topics */}
        <div className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <div className="font-hud text-[10px] font-bold text-[#dde4ff] tracking-[0.08em]">Topics</div>
            <div className="font-mono text-[9px] text-[#818cf8] cursor-pointer">View All</div>
          </div>
          <div className="grid grid-cols-3 gap-2">
            {TOPICS.map(t => (
              <div key={t.label} onClick={() => onNavigate("chat")}
                className="flex flex-col items-center gap-1.5 cursor-pointer">
                <div className="w-11 h-11 rounded-[13px] bg-[rgba(8,14,30,0.97)] border border-[rgba(99,102,241,0.22)] flex items-center justify-center text-[19px] transition-all hover:bg-[rgba(99,102,241,0.12)] hover:border-[rgba(99,102,241,0.48)]">
                  {t.icon}
                </div>
                <div className="font-mono text-[9px] text-[#6878aa]">{t.label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* History */}
        <div className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <div className="font-hud text-[10px] font-bold text-[#dde4ff] tracking-[0.08em]">Recent History</div>
            <div className="font-mono text-[9px] text-[#818cf8] cursor-pointer">View All</div>
          </div>
          <div className="flex flex-col gap-2">
            {HISTORY.map(h => (
              <div key={h.main} onClick={() => onNavigate("chat")}
                className="bg-[rgba(8,14,30,0.97)] border border-[rgba(99,102,241,0.1)] rounded-[14px] px-3.5 py-3 flex items-center gap-2.5 cursor-pointer transition-all hover:border-[rgba(99,102,241,0.22)]">
                <div className="w-8 h-8 rounded-[10px] bg-[rgba(99,102,241,0.1)] border border-[rgba(99,102,241,0.22)] flex items-center justify-center text-[13px] flex-shrink-0">
                  {h.icon}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-[12px] font-semibold text-[#dde4ff] truncate">{h.main}</div>
                  <div className="font-mono text-[9px] text-[#2a3660] mt-0.5">{h.meta}</div>
                </div>
                <span className="text-[#2a3660] text-[13px]">›</span>
              </div>
            ))}
          </div>
        </div>

      </div>

      <style jsx>{`
        @keyframes spin { to { transform:rotate(360deg); } }
        @keyframes orbPulse { 0%,100%{opacity:0.8;transform:scale(1);} 50%{opacity:1;transform:scale(1.18);} }
        @keyframes heartbeat { 0%,100%{transform:scale(1);opacity:1;} 50%{transform:scale(0.6);opacity:0.5;} }
      `}</style>
    </div>
  );
}
