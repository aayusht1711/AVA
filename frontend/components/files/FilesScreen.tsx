import { Screen } from "@/app/dashboard/page";

export default function FilesScreen({ onNavigate }: { onNavigate: (s: Screen) => void }) {
  return (
    <div className="w-full h-full flex flex-col items-center justify-center text-white p-8">
      <h1 className="text-3xl font-hud text-[#818cf8] mb-4 tracking-widest">FILE MANAGER</h1>
      <p className="text-sm text-gray-400 max-w-lg text-center mb-8 font-mono">
        Upload PDFs, images, CSVs, or code files for AVA to analyze.
      </p>
      <div className="border-2 border-dashed border-[rgba(129,140,248,0.5)] rounded-xl p-16 bg-[rgba(99,102,241,0.05)] hover:bg-[rgba(99,102,241,0.1)] transition-colors cursor-pointer flex flex-col items-center w-full max-w-2xl">
        <div className="text-5xl mb-4 opacity-80">📁</div>
        <p className="text-[#818cf8] font-bold tracking-widest">DRAG AND DROP FILES HERE</p>
        <p className="text-xs text-gray-500 mt-2 font-mono uppercase">or click to browse</p>
      </div>
    </div>
  );
}
