"use client";

import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import VoiceScreen from "@/components/voice/VoiceScreen";
import SplashScreen from "@/components/layout/SplashScreen";
import HomeScreen from "@/components/layout/HomeScreen";
import ChatScreen from "@/components/chat/ChatScreen";
import MemoryScreen from "@/components/memory/MemoryScreen";
import TasksScreen from "@/components/tasks/TasksScreen";
import FilesScreen from "@/components/files/FilesScreen";
import TopBar from "@/components/layout/TopBar";

export type Screen = "voice" | "splash" | "home" | "chat" | "memory" | "tasks" | "files";

export default function DashboardPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [screen, setScreen] = useState<Screen>("voice");

  useEffect(() => {
    if (status === "unauthenticated") router.push("/login");
  }, [status, router]);

  if (status === "loading") {
    return (
      <div className="w-full h-screen flex items-center justify-center bg-[#03060f]">
        <div className="flex flex-col items-center gap-4">
          <div className="relative w-12 h-12">
            <div className="absolute inset-0 rounded-full border border-[rgba(129,140,248,0.4)] animate-spin" />
            <div className="absolute inset-3 rounded-full bg-gradient-to-br from-[#818cf8] to-[#4f46e5] animate-pulse" />
          </div>
          <div className="font-hud text-xs text-[#818cf8] tracking-[0.2em]">LOADING AVA...</div>
        </div>
      </div>
    );
  }

  if (!session) return null;

  const userName = session.user?.name || "User";

  return (
    <div className="w-full h-screen flex flex-col overflow-hidden bg-[#03060f] relative">
      {/* Background */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute inset-0 bg-grid" />
        <div className="absolute top-[-20%] left-[15%] w-[65%] h-[80%]"
          style={{ background: "radial-gradient(ellipse, rgba(79,70,229,0.12) 0%, transparent 65%)" }} />
        <div className="absolute bottom-[-15%] right-0 w-[40%] h-[50%]"
          style={{ background: "radial-gradient(ellipse, rgba(99,102,241,0.07) 0%, transparent 65%)" }} />
        <div className="absolute inset-0"
          style={{ background: "radial-gradient(ellipse at center, transparent 30%, rgba(3,6,15,0.82) 100%)" }} />
        {/* Scanline */}
        <div className="scanline-anim" />
      </div>

      {/* Top Bar */}
      <TopBar screen={screen} onNavigate={setScreen} userName={userName} />

      {/* Screens */}
      <div className="flex-1 relative z-10 overflow-hidden">
        {screen === "voice" && <VoiceScreen onNavigate={setScreen} />}
        {screen === "splash" && <SplashScreen onNavigate={setScreen} />}
        {screen === "home" && <HomeScreen onNavigate={setScreen} userName={userName} />}
        {screen === "chat" && <ChatScreen onNavigate={setScreen} session={session} />}
        {screen === "memory" && <MemoryScreen onNavigate={setScreen} />}
        {screen === "tasks" && <TasksScreen onNavigate={setScreen} />}
        {screen === "files" && <FilesScreen onNavigate={setScreen} />}
      </div>

      <style jsx>{`
        .scanline-anim {
          position: absolute;
          left: 0; right: 0;
          height: 180px;
          top: -180px;
          background: linear-gradient(to bottom, transparent, rgba(99,102,241,0.018) 50%, transparent);
          animation: scanMove 14s linear infinite;
        }
        @keyframes scanMove { to { top: 110vh; } }
      `}</style>
    </div>
  );
}
