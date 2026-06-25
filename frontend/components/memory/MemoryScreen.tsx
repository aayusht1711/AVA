"use client";

import { Screen } from "@/app/dashboard/page";
import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";

interface Memory {
  id: string;
  content: string;
  metadata: Record<string, any>;
}

export default function MemoryScreen({ onNavigate }: { onNavigate: (s: Screen) => void }) {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [loading, setLoading] = useState(true);
  const { data: session } = useSession();

  const fetchMemories = async () => {
    if (!session) return;
    try {
      const token = (session as any).accessToken || "";
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/memory`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      setMemories(data.memories || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMemories();
  }, [session]);

  const deleteMemory = async (id: string) => {
    try {
      const token = (session as any).accessToken || "";
      await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/memory/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` }
      });
      setMemories(memories.filter(m => m.id !== id));
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="w-full h-full flex flex-col items-center p-12 overflow-y-auto">
      <div className="w-full max-w-4xl">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-[28px] font-hud text-[#dde4ff] mb-2 tracking-[0.1em]">
              <span className="text-[#818cf8]">MEMORY</span> BROWSER
            </h1>
            <p className="text-[13px] text-[#6878aa] font-mono">
              Manage the facts and data AVA has extracted about you and stored in ChromaDB.
            </p>
          </div>
          <div className="text-[#86efac] font-mono text-[10px] flex items-center gap-2 bg-[rgba(134,239,172,0.1)] px-4 py-2 rounded-full border border-[rgba(134,239,172,0.2)]">
            <span className="w-2 h-2 rounded-full bg-[#86efac] animate-pulse" />
            ChromaDB Active
          </div>
        </div>

        {loading ? (
          <div className="text-[#818cf8] font-mono animate-pulse">Loading memories...</div>
        ) : memories.length === 0 ? (
          <div className="bg-[rgba(3,6,15,0.8)] border border-[rgba(99,102,241,0.2)] rounded-[16px] p-8 text-center text-[#6878aa] text-[13px] italic">
            No memories found. Chat with AVA to let her learn about you.
          </div>
        ) : (
          <div className="flex flex-col gap-4">
            {memories.map(m => (
              <div key={m.id} className="bg-[rgba(10,18,40,0.6)] border border-[rgba(99,102,241,0.15)] rounded-[12px] p-5 flex justify-between items-start hover:border-[rgba(99,102,241,0.4)] transition-colors group">
                <div className="flex-1">
                  <div className="font-mono text-[10px] text-[#2a3660] mb-2">ID: {m.id}</div>
                  <div className="text-[14px] text-[#dde4ff] font-medium leading-relaxed">{m.content}</div>
                  <div className="mt-3 flex gap-2">
                    {Object.entries(m.metadata).map(([k, v]) => (
                      <span key={k} className="text-[9px] font-mono bg-[rgba(99,102,241,0.08)] text-[#818cf8] px-2 py-1 rounded-[4px] border border-[rgba(99,102,241,0.15)]">
                        {k}: {String(v)}
                      </span>
                    ))}
                  </div>
                </div>
                <button onClick={() => deleteMemory(m.id)}
                  className="ml-4 px-3 py-1.5 rounded-[6px] bg-[rgba(248,113,113,0.1)] text-[#f87171] text-[10px] font-bold hover:bg-[rgba(248,113,113,0.2)] transition-colors opacity-0 group-hover:opacity-100">
                  DELETE
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
