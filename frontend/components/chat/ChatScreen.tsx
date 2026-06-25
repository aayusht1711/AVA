"use client";

import { useState, useEffect, useRef } from "react";
import { Session } from "next-auth";
import { Screen } from "@/app/dashboard/page";
import { chatApi } from "@/lib/api";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  agent?: string;
  time: string;
}

interface ChatScreenProps {
  onNavigate: (s: Screen) => void;
  session: Session;
}

const SUGGESTIONS = [
  "▶ Run a Python script",
  "+ Search the web",
  "→ Generate a PDF",
  "? Explain something",
  "📄 Write a report",
];

const TRACE_COLORS: Record<string, string> = {
  orchestrator: "border-[rgba(99,102,241,0.35)] text-[#818cf8] bg-[rgba(99,102,241,0.07)]",
  coder:        "border-[rgba(165,180,252,0.35)] text-[#a5b4fc] bg-[rgba(165,180,252,0.07)]",
  researcher:   "border-[rgba(134,239,172,0.32)] text-[#86efac] bg-[rgba(134,239,172,0.06)]",
  memory:       "border-[rgba(252,211,77,0.32)]  text-[#fcd34d] bg-[rgba(252,211,77,0.06)]",
  document:     "border-[rgba(252,211,77,0.32)]  text-[#fcd34d] bg-[rgba(252,211,77,0.06)]",
};

function nowTime() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function renderContent(content: string, onShowArtifact: (data: any) => void) {
  // First check if it's a Prompt Blueprint
  const promptMatch = content.match(/<PROMPT_BLUEPRINT>([\s\S]*?)<\/PROMPT_BLUEPRINT>/);
  if (promptMatch) {
    const promptText = promptMatch[1].trim();
    return (
      <div className="mt-2 mb-2 rounded-xl overflow-hidden border border-[#818cf8] bg-[rgba(10,18,40,0.8)] shadow-[0_0_20px_rgba(99,102,241,0.2)]">
        <div className="flex items-center justify-between px-4 py-2 bg-[rgba(99,102,241,0.1)] border-b border-[rgba(99,102,241,0.2)]">
          <div className="flex items-center gap-2">
            <span className="text-[18px]">✨</span>
            <span className="font-hud text-[11px] font-bold text-[#dde4ff] tracking-wider">Prompt Blueprint</span>
          </div>
          <button 
            onClick={() => navigator.clipboard.writeText(promptText)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[rgba(99,102,241,0.2)] hover:bg-[#818cf8] hover:text-black transition-all text-[#818cf8] text-[10px] font-bold"
          >
            <span>📋</span> COPY
          </button>
        </div>
        <div className="p-4 font-mono text-[11px] leading-relaxed text-[#c7d2fe] whitespace-pre-wrap">
          {promptText}
        </div>
      </div>
    );
  }

  const parts = content.split(/(```[\s\S]*?```)/g);
  return parts.map((part, i) => {
    const codeMatch = part.match(/^```(\w+)?\n?([\s\S]*?)```$/);
    if (codeMatch) {
      const lang = codeMatch[1] || "code";
      const code = codeMatch[2] || "";
      
      // Data Canvas Hook: if it's csv or a generated image link from E2B
      if (lang === "csv" || content.includes("data:image/png;base64")) {
        return (
          <div key={i} className="mt-2 rounded-[10px] overflow-hidden border border-[rgba(134,239,172,0.3)] bg-[rgba(134,239,172,0.05)] p-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-[16px]">📊</span>
              <div>
                <div className="text-[12px] font-semibold text-[#86efac]">Data Generated</div>
                <div className="text-[9px] text-[#2a3660] font-mono">Interactive visualization ready</div>
              </div>
            </div>
            <button onClick={() => onShowArtifact({ title: "Analysis Results", type: lang, content: code || content })}
              className="px-3 py-1.5 rounded-[6px] bg-[rgba(134,239,172,0.15)] text-[#86efac] text-[10px] font-bold hover:bg-[rgba(134,239,172,0.25)] transition-colors">
              VIEW ARTIFACT
            </button>
          </div>
        );
      }

      return (
        <div key={i} className="mt-2 rounded-[10px] overflow-hidden border border-[rgba(99,102,241,0.15)]">
          <div className="flex items-center justify-between px-3 py-1.5 bg-[rgba(99,102,241,0.06)] border-b border-[rgba(99,102,241,0.1)]">
            <span className="font-mono text-[8px] text-[#2a3660] uppercase tracking-[0.08em] flex items-center gap-1.5">
              <span className="w-[5px] h-[5px] rounded-full bg-[#86efac] inline-block" />
              {lang}
            </span>
            <button onClick={() => navigator.clipboard.writeText(code)}
              className="font-mono text-[8px] text-[#2a3660] hover:text-[#818cf8] transition-colors border border-[rgba(99,102,241,0.1)] px-1.5 py-0.5 rounded">
              copy
            </button>
          </div>
          <pre className="px-3 py-2.5 text-[11px] font-mono text-[#93c5fd] overflow-x-auto bg-[rgba(0,0,0,0.55)] leading-relaxed">{code}</pre>
        </div>
      );
    }
    return <span key={i}>{part}</span>;
  });
}

export default function ChatScreen({ onNavigate, session }: ChatScreenProps) {
  const [messages,   setMessages]   = useState<Message[]>([]);
  const [input,      setInput]      = useState("");
  const [streaming,  setStreaming]  = useState(false);
  const [agent,      setAgent]      = useState("orchestrator");
  const [sessionId,  setSessionId]  = useState<string | null>(null);
  const [memEntries, setMemEntries] = useState<string[]>([]);
  const [memCount,   setMemCount]   = useState(0);
  const [wsStatus,   setWsStatus]   = useState<"connecting"|"open"|"closed">("connecting");
  const [activeArtifact, setActiveArtifact] = useState<{title: string, type: string, content: string} | null>(null);
  
  const [devMode, setDevMode] = useState(false);
  const [showTooltips, setShowTooltips] = useState(false);

  const msgsRef   = useRef<HTMLDivElement>(null);
  const wsRef     = useRef<WebSocket | null>(null);
  const bufferRef = useRef<string>("");
  const msgIdRef  = useRef<string>("");

  const userName    = session.user?.name?.split(" ")[0] || "there";
  const accessToken = (session as any).accessToken || "";

  useEffect(() => {
    msgsRef.current?.scrollTo({ top: msgsRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, streaming]);

  useEffect(() => {
    let mounted = true;
    async function init() {
      try {
        const res = await chatApi.createSession("Chat");
        const sid = res.data.id;
        if (!mounted) return;
        setSessionId(sid);
        setMessages([{
          id: "welcome", role: "assistant",
          content: `Hey ${userName} 👋 — AVA online. Think of me as your Jarvis. Code, research, documents, reminders — what are we building today?`,
          agent: "orchestrator", time: nowTime(),
        }]);
        connectWS(sid);
      } catch {
        setMessages([{ id: "err", role: "assistant",
          content: "Couldn't connect to AVA backend. Make sure Docker is running.",
          agent: "orchestrator", time: nowTime() }]);
        setWsStatus("closed");
      }
    }
    init();

    // Check Developer Mode and Tooltips
    if (typeof window !== "undefined") {
      setDevMode(localStorage.getItem("ava_developer_mode") === "true");
      
      // If it's their very first time seeing the dashboard (after setup)
      if (localStorage.getItem("ava_first_boot_done") === "true" && !localStorage.getItem("ava_tooltips_done")) {
        setShowTooltips(true);
      }
    }

    return () => { mounted = false; wsRef.current?.close(); };
  }, []);

  function dismissTooltips() {
    setShowTooltips(false);
    if (typeof window !== "undefined") {
      localStorage.setItem("ava_tooltips_done", "true");
    }
  }

  function connectWS(sid: string) {
    const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000"}/api/chat/ws/${sid}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;
    ws.onopen  = () => setWsStatus("open");
    ws.onclose = () => setWsStatus("closed");
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      if (data.type === "agent") {
        setAgent(data.agent);
        const streamId = `stream-${Date.now()}`;
        msgIdRef.current = streamId;
        bufferRef.current = "";
        setMessages(prev => [...prev, {
          id: streamId, role: "assistant",
          content: "", agent: data.agent, time: nowTime(),
        }]);
      }
      if (data.type === "chunk") {
        bufferRef.current += data.content;
        setMessages(prev => prev.map(m =>
          m.id === msgIdRef.current ? { ...m, content: bufferRef.current } : m
        ));
      }
      if (data.type === "done") setStreaming(false);
      if (data.type === "error") {
        setStreaming(false);
        setMessages(prev => [...prev, {
          id: `err-${Date.now()}`, role: "assistant",
          content: `⚠️ ${data.message}`, agent: "orchestrator", time: nowTime(),
        }]);
      }
    };
  }

  function addMemory(text: string) {
    const kw = text.match(/\b(python|javascript|code|web|file|pdf|search|debug|api|data|scrape|report)\b/gi);
    if (kw?.length) {
      setMemEntries(prev => [...prev.slice(-9), [...new Set(kw)].slice(0,3).join(", ")]);
      setMemCount(c => c + 1);
    }
  }

  function sendMessage(content: string) {
    if (!content.trim() || streaming) return;
    
    setMessages(prev => [...prev, {
      id: `u-${Date.now()}`, role: "user", content, time: nowTime(),
    }]);
    addMemory(content);
    setInput("");

    // Offline Mock Fallback for Prompt Maker
    if ((!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) && content.toLowerCase().includes("prompt")) {
      setStreaming(true);
      setTimeout(() => {
        setStreaming(false);
        setMessages(prev => [...prev, {
          id: `mock-prompt-${Date.now()}`, role: "assistant", agent: "orchestrator", time: nowTime(),
          content: `<PROMPT_BLUEPRINT>
[Context]
You are an expert Frontend Developer focusing on React and Next.js.

[Instructions]
Please create a highly optimized, responsive landing page using Tailwind CSS. It must include:
1. A hero section with a glowing gradient background.
2. A features grid.
3. A newsletter signup footer.

[Constraints]
- Do not use external CSS files, rely purely on Tailwind utility classes.
- Ensure the code is strictly TypeScript compliant.

[Output Format]
Output only the raw code block. Do not provide conversational filler.
</PROMPT_BLUEPRINT>`
        }]);
      }, 1500);
      return;
    }

    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      if (sessionId) connectWS(sessionId);
      return;
    }
    
    setStreaming(true);
    wsRef.current.send(JSON.stringify({ content, token: accessToken }));
  }

  return (
    <div className="w-full h-full flex">
      {/* Chat */}
      <div className="flex-1 flex flex-col overflow-hidden border-r border-[rgba(99,102,241,0.1)]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[rgba(99,102,241,0.1)] bg-[rgba(3,6,15,0.6)] flex-shrink-0">
          <div className="flex items-center gap-4">
            <div className="relative w-11 h-11">
              <div className="absolute inset-0 rounded-full border border-[rgba(129,140,248,0.4)]" style={{animation:"spin 5s linear infinite"}}/>
              <div className="absolute inset-[7px] rounded-full border border-[rgba(99,102,241,0.22)]" style={{animation:"spin 9s linear infinite reverse"}}/>
              <div className="absolute inset-[12px] rounded-full border-dashed border border-[rgba(99,102,241,0.12)]" style={{animation:"spin 4s linear infinite"}}/>
              <div className="absolute inset-[16px] rounded-full" style={{background:"linear-gradient(135deg,#818cf8,#4f46e5)",animation:"orbPulse 2.5s ease-in-out infinite"}}/>
            </div>
            <div>
              <div className="font-hud text-[14px] font-bold text-[#dde4ff] tracking-[0.08em]">AVA · ONLINE</div>
              <div className={`font-mono text-[10px] flex items-center gap-1.5 mt-0.5 ${wsStatus==="open"?"text-[#86efac]":"text-[#f87171]"}`}>
                <span className="w-1.5 h-1.5 rounded-full bg-current" style={{animation:wsStatus==="open"?"heartbeat 1.1s ease-in-out infinite":"none"}}/>
                {wsStatus==="open"?"Listening · Ready":wsStatus==="connecting"?"Connecting...":"Disconnected"}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <button 
              onClick={() => {
                setDevMode(!devMode);
                if (typeof window !== "undefined") localStorage.setItem("ava_developer_mode", (!devMode).toString());
              }}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-full border text-[10px] font-mono transition-colors ${devMode ? 'bg-[rgba(129,140,248,0.1)] border-[rgba(129,140,248,0.3)] text-[#818cf8]' : 'bg-[rgba(255,255,255,0.02)] border-[rgba(255,255,255,0.1)] text-[#6878aa] hover:text-white'}`}
            >
              <span>⚙️</span> {devMode ? 'Dev Mode ON' : 'Dev Mode OFF'}
            </button>
            <div className="flex gap-2 hidden md:flex">
              {["Groq Llama 3.3",`${messages.length} msgs`].map(c=>(
                <span key={c} className="font-mono text-[9px] px-[10px] py-[3px] rounded-full border border-[rgba(99,102,241,0.1)] text-[#6878aa] bg-[rgba(99,102,241,0.03)]">{c}</span>
              ))}
            </div>
          </div>
        </div>

        {/* Messages */}
        <div ref={msgsRef} className="flex-1 overflow-y-auto px-6 pt-5 pb-2 flex flex-col gap-4">
          <div className="flex items-center gap-2 my-1">
            <div className="flex-1 h-px bg-[rgba(99,102,241,0.1)]"/>
            <span className="font-mono text-[8px] text-[#2a3660]">TODAY</span>
            <div className="flex-1 h-px bg-[rgba(99,102,241,0.1)]"/>
          </div>
          {messages.map(msg => (
            <div key={msg.id} className={`flex gap-2.5 ${msg.role==="user"?"flex-row-reverse":""}`} style={{animation:"msgIn .28s ease-out"}}>
              <div className={`w-[34px] h-[34px] rounded-[9px] flex-shrink-0 flex items-center justify-center font-hud text-[10px] font-bold self-end ${msg.role==="assistant"?"bg-[rgba(99,102,241,0.12)] border border-[rgba(99,102,241,0.28)] text-[#818cf8]":"bg-[rgba(99,102,241,0.07)] border border-[rgba(99,102,241,0.14)] text-[#6878aa]"}`}>
                {msg.role==="assistant"?"A":session.user?.name?.[0]||"U"}
              </div>
              <div className="max-w-[72%]">
                {msg.role==="assistant"&&msg.agent&&(
                  <div className="flex gap-1.5 mb-1.5">
                    <span className={`font-mono text-[8px] px-2 py-[2px] rounded-full border flex items-center gap-1.5 ${TRACE_COLORS[msg.agent]||TRACE_COLORS.orchestrator}`}>
                      <span className="w-[3px] h-[3px] rounded-full bg-current"/>{msg.agent}
                    </span>
                  </div>
                )}
                <div className={`px-4 py-3 rounded-[18px] text-[13px] font-medium leading-relaxed relative overflow-hidden whitespace-pre-wrap ${msg.role==="assistant"?"bg-[rgba(6,12,26,0.98)] border border-[rgba(99,102,241,0.22)] rounded-bl-[4px] text-[#dde4ff]":"border border-[rgba(99,102,241,0.3)] rounded-br-[4px] text-[#e0e7ff]"}`}
                  style={msg.role==="user"?{background:"linear-gradient(135deg,#312e81,#4f46e5)"}:{}}>
                  {msg.role==="assistant"&&<div className="absolute top-0 left-0 right-0 h-px" style={{background:"linear-gradient(90deg,#4f46e5,transparent 55%)",opacity:0.45}}/>}
                  {renderContent(msg.content, setActiveArtifact)}
                  {streaming&&msg.id===msgIdRef.current&&(
                    <span className="inline-block w-[2px] h-[14px] bg-[#818cf8] ml-0.5 align-middle" style={{animation:"blink .8s ease-in-out infinite"}}/>
                  )}
                </div>
                <div className={`font-mono text-[8px] text-[#2a3660] mt-1 ${msg.role==="user"?"text-right":""}`}>
                  {msg.role==="assistant"?"AVA":"You"} · {msg.time}
                </div>
              </div>
            </div>
          ))}
          {streaming&&messages[messages.length-1]?.role==="user"&&(
            <div className="flex gap-2.5">
              <div className="w-[34px] h-[34px] rounded-[9px] flex-shrink-0 flex items-center justify-center font-hud text-[10px] font-bold bg-[rgba(99,102,241,0.12)] border border-[rgba(99,102,241,0.28)] text-[#818cf8]">A</div>
              <div className="px-4 py-3 bg-[rgba(6,12,26,0.98)] border border-[rgba(99,102,241,0.22)] rounded-[18px] rounded-bl-[4px] flex items-center gap-1.5">
                {[0,0.18,0.36].map((d,i)=>(
                  <div key={i} className="w-1.5 h-1.5 rounded-full bg-[#818cf8]" style={{animation:`typingDot 1.3s ease-in-out infinite ${d}s`,opacity:0.4}}/>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Suggestions */}
        <div className="flex gap-2 overflow-x-auto px-6 py-2 flex-shrink-0">
          {SUGGESTIONS.map(s=>(
            <button key={s} onClick={()=>sendMessage(s.replace(/^[▶+→?📄]\s*/,""))} disabled={streaming}
              className="font-mono text-[9px] whitespace-nowrap px-3.5 py-[5px] rounded-full border border-[rgba(99,102,241,0.22)] text-[#6878aa] bg-[rgba(99,102,241,0.05)] cursor-pointer transition-all hover:bg-[rgba(99,102,241,0.14)] hover:text-[#818cf8] flex-shrink-0 disabled:opacity-40">
              {s}
            </button>
          ))}
        </div>

        {/* Input */}
        <div className="flex items-center gap-2.5 px-5 pb-4 pt-2 bg-[rgba(3,6,15,0.99)] border-t border-[rgba(99,102,241,0.1)] flex-shrink-0 relative">
          <div className="absolute top-0 left-0 right-0 h-px" style={{background:"linear-gradient(90deg,transparent,#6366f1,transparent)",opacity:0.16}}/>
          <button onClick={()=>onNavigate("voice")}
            className="w-11 h-11 rounded-full flex-shrink-0 bg-[rgba(99,102,241,0.08)] border border-[rgba(99,102,241,0.22)] flex items-center justify-center text-[17px] cursor-pointer text-[#818cf8] transition-all hover:bg-[rgba(99,102,241,0.16)]">🎙</button>
          <div className="flex-1 flex items-center min-h-[46px] bg-[rgba(8,14,30,0.97)] border border-[rgba(99,102,241,0.1)] rounded-[26px] px-5 transition-all focus-within:border-[rgba(99,102,241,0.48)]">
            <input value={input} onChange={e=>setInput(e.target.value)}
              onKeyDown={e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();sendMessage(input);}}}
              disabled={streaming}
              placeholder={streaming?"AVA is thinking...":"Message AVA — type or click mic..."}
              className="flex-1 bg-transparent border-none outline-none text-[14px] font-medium text-[#dde4ff] placeholder-[#2a3660] caret-[#818cf8] font-body disabled:opacity-60"/>
            <button className="text-[17px] text-[#6878aa] hover:text-[#818cf8] transition-colors ml-1">📎</button>
          </div>
          <button onClick={()=>sendMessage(input)} disabled={streaming||!input.trim()}
            className="w-11 h-11 rounded-full flex-shrink-0 flex items-center justify-center text-[17px] text-white cursor-pointer transition-all hover:scale-105 disabled:opacity-40"
            style={{background:"linear-gradient(135deg,#4f46e5,#6366f1)",boxShadow:"0 4px 16px rgba(99,102,241,0.42)"}}>➤</button>
        </div>
      </div>

      {/* Right panel (Only shown if devMode is ON) */}
      <div className={`flex-shrink-0 flex flex-col overflow-hidden bg-[rgba(3,6,15,0.96)] transition-all duration-300 ${devMode ? 'w-[256px] border-l border-[rgba(99,102,241,0.1)]' : 'w-0 border-0'}`}>
        <div className="min-w-[256px] h-full flex flex-col">
          <div className="mx-3.5 mt-4 mb-2.5 relative overflow-hidden rounded-[16px] border border-[rgba(99,102,241,0.22)] p-3 flex items-center gap-2.5" style={{background:"linear-gradient(135deg,#121f3d,#312e81)"}}>
            <div className="absolute top-[-40%] right-[-20%] w-20 h-20 rounded-full pointer-events-none" style={{background:"radial-gradient(circle,rgba(99,102,241,0.28),transparent 70%)"}}/>
            <div className="text-[30px] flex-shrink-0 relative z-10" style={{animation:"float 3.5s ease-in-out infinite"}}>🤖</div>
            <div className="flex-1 relative z-10">
              <div className="font-hud text-[11px] font-bold text-white tracking-[0.07em]">AVA · ONLINE</div>
              <div className="font-mono text-[8px] text-[rgba(165,180,252,0.85)] flex items-center gap-1.5 mt-1">
                <span className="w-1 h-1 rounded-full bg-[#86efac]" style={{animation:"heartbeat 1.2s ease-in-out infinite"}}/>
                {streaming?`${agent} working...`:"Ready to assist"}
              </div>
            </div>
          </div>

        <div className="px-3.5 pb-3 flex-shrink-0">
          <div className="font-hud text-[7.5px] tracking-[0.16em] text-[#2a3660] uppercase mb-2.5">Live Tools</div>
          {[
            {icon:"🔒",name:"E2B Sandbox", sub:"code_exec",   active:agent==="coder"},
            {icon:"🌐",name:"Tavily Search",sub:"web_search",  active:agent==="researcher"},
            {icon:"🔮",name:"ChromaDB",    sub:"vector_query", active:agent==="memory"},
            {icon:"🔊",name:"ElevenLabs",  sub:"tts_stream",   active:false},
            {icon:"📄",name:"PDF Generator",sub:"gen_pdf",     active:agent==="document"},
          ].map(t=>(
            <div key={t.name} className="flex items-center gap-2 py-[5px] border-b border-[rgba(99,102,241,0.04)] last:border-0">
              <span className="text-[12px] w-[15px] text-center flex-shrink-0">{t.icon}</span>
              <div className="flex-1"><div className="text-[11.5px] font-semibold text-[#dde4ff]">{t.name}</div><div className="font-mono text-[9px] text-[#2a3660]">{t.sub}</div></div>
              <div className={`w-[5px] h-[5px] rounded-full ${t.active?"bg-[#fcd34d]":"bg-[#86efac]"}`}
                style={{boxShadow:t.active?"0 0 5px #fcd34d":"0 0 5px #86efac",animation:t.active?"heartbeat .7s ease-in-out infinite":"none"}}/>
            </div>
          ))}
        </div>

        <div className="px-3.5 pb-3 border-t border-[rgba(99,102,241,0.1)] pt-3 flex-shrink-0">
          <div className="font-hud text-[7.5px] tracking-[0.16em] text-[#2a3660] uppercase mb-2.5">
            Session Memory <span className="ml-1 text-[#818cf8]">{memCount}</span>
          </div>
          {memEntries.length===0?(
            <div className="font-mono text-[9px] text-[#2a3660]">No memories yet...</div>
          ):memEntries.slice(-5).map((e,i)=>(
            <div key={i} className="flex gap-2 py-1 border-b border-[rgba(99,102,241,0.04)] last:border-0 text-[11px]">
              <span className="font-mono text-[9px] text-[#818cf8] w-3.5 flex-shrink-0 pt-0.5">m{i+1}</span>
              <span className="text-[#6878aa] truncate">{e}</span>
            </div>
          ))}
        </div>

        <div className="px-3.5 pb-3 border-t border-[rgba(99,102,241,0.1)] pt-3">
          <div className="font-hud text-[7.5px] tracking-[0.16em] text-[#2a3660] uppercase mb-2.5">System Stats</div>
          <div className="grid grid-cols-2 gap-1.5">
            {[
              {label:"Model", value:"Groq",  unit:""},
              {label:"Agents",value:"8",     unit:" on"},
              {label:"Memory",value:String(memCount),unit:""},
              {label:"WS",    value:wsStatus==="open"?"Live":"Off",unit:""},
            ].map(s=>(
              <div key={s.label} className="bg-[rgba(99,102,241,0.04)] border border-[rgba(99,102,241,0.1)] rounded-[10px] p-1.5">
                <div className="font-hud text-[6.5px] text-[#2a3660] uppercase tracking-[0.08em]">{s.label}</div>
                <div className="font-hud text-[13px] text-[#818cf8] mt-0.5 leading-none">{s.value}<span className="text-[8px] text-[#2a3660]">{s.unit}</span></div>
              </div>
            ))}
          </div>
        </div>
        </div>
      </div>

      {/* Tooltips Overlay */}
      {showTooltips && (
        <div className="absolute inset-0 z-[100] flex items-center justify-center bg-[rgba(0,0,0,0.6)] backdrop-blur-sm pointer-events-auto" onClick={dismissTooltips}>
          <div className="bg-[#03060f] border border-[#818cf8] p-6 rounded-2xl max-w-sm text-center shadow-[0_0_40px_rgba(129,140,248,0.3)]" onClick={e => e.stopPropagation()}>
            <div className="text-4xl mb-4">✨</div>
            <h2 className="font-hud text-lg text-white mb-2 tracking-wide">Welcome to the Dashboard!</h2>
            <p className="font-mono text-xs text-[#6878aa] mb-6 leading-relaxed">
              Try clicking the <strong>Microphone icon</strong> at the bottom to talk to AVA naturally, or click the <strong>Memory tab</strong> to see what she remembers about you!
            </p>
            <button onClick={dismissTooltips} className="px-6 py-2.5 rounded-full font-bold text-xs bg-[#818cf8] text-black hover:bg-[#a5b4fc] transition-colors">
              Got it, let's go!
            </button>
          </div>
        </div>
      )}

      {/* Interactive Data Canvas */}
      <div className={`absolute top-0 right-0 bottom-0 w-[45%] bg-[rgba(6,12,28,0.85)] backdrop-blur-xl border-l border-[rgba(99,102,241,0.2)] transition-transform duration-500 z-50 flex flex-col shadow-[-20px_0_40px_rgba(0,0,0,0.5)] ${activeArtifact ? "translate-x-0" : "translate-x-[105%]"}`}>
        <div className="flex items-center justify-between px-6 py-4 border-b border-[rgba(99,102,241,0.1)] bg-[rgba(3,6,15,0.6)]">
          <div className="flex items-center gap-3">
            <span className="text-[20px]">📊</span>
            <div>
              <div className="font-hud text-[14px] font-bold text-[#dde4ff] tracking-[0.05em]">{activeArtifact?.title || "Data Canvas"}</div>
              <div className="font-mono text-[9px] text-[#86efac]">Interactive Visualization</div>
            </div>
          </div>
          <button onClick={() => setActiveArtifact(null)} className="w-8 h-8 rounded-full flex items-center justify-center bg-[rgba(255,255,255,0.05)] hover:bg-[rgba(255,255,255,0.1)] text-[#dde4ff] transition-colors">✕</button>
        </div>
        <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-4">
          <div className="font-mono text-[11px] text-[#93c5fd] bg-[rgba(0,0,0,0.4)] p-4 rounded-[12px] border border-[rgba(99,102,241,0.1)] whitespace-pre-wrap">
            {activeArtifact?.content}
          </div>
        </div>
      </div>

      <style jsx>{`
        @keyframes spin{to{transform:rotate(360deg);}}
        @keyframes orbPulse{0%,100%{opacity:0.8;transform:scale(1);}50%{opacity:1;transform:scale(1.2);}}
        @keyframes heartbeat{0%,100%{transform:scale(1);opacity:1;}50%{transform:scale(0.6);opacity:0.5;}}
        @keyframes float{0%,100%{transform:translateY(0);}50%{transform:translateY(-4px);}}
        @keyframes msgIn{from{opacity:0;transform:translateY(7px);}to{opacity:1;transform:translateY(0);}}
        @keyframes typingDot{0%,80%,100%{transform:scale(0.5);opacity:0.3;}40%{transform:scale(1.05);opacity:1;}}
        @keyframes blink{0%,100%{opacity:1;}50%{opacity:0;}}
      `}</style>
    </div>
  );
}
