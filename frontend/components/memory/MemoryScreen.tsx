import { Screen } from "@/app/dashboard/page";

export default function MemoryScreen({ onNavigate }: { onNavigate: (s: Screen) => void }) {
  return (
    <div className="w-full h-full flex flex-col items-center justify-center text-white p-8">
      <h1 className="text-3xl font-hud text-[#818cf8] mb-4 tracking-widest">MEMORY BROWSER</h1>
      <p className="text-sm text-gray-400 max-w-lg text-center mb-8 font-mono">
        View and manage the facts and data AVA has extracted about you and stored in ChromaDB.
      </p>
      
      <div className="w-full max-w-3xl bg-[rgba(3,6,15,0.8)] border border-[rgba(99,102,241,0.2)] rounded-lg p-6">
        <div className="text-[#86efac] font-mono text-xs mb-4 flex items-center gap-2">
           <span className="w-2 h-2 rounded-full bg-[#86efac] animate-pulse" />
           ChromaDB Connection Active
        </div>
        <div className="text-gray-500 text-sm italic">
          No memories found. Chat with AVA to let her learn about you.
        </div>
      </div>
    </div>
  );
}
