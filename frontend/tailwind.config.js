
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        
        navy: {
          DEFAULT: "#03060f",
          2: "#060d1c",
          3: "#0a1228",
          4: "#0e1a36",
          5: "#121f3d",
        },
        indigo: {
          DEFAULT: "#6366f1",
          2: "#818cf8",
          3: "#4f46e5",
          4: "#312e81",
          5: "#1e1b4b",
        },
        ava: {
          green: "#86efac",
          amber: "#fcd34d",
          red: "#f87171",
          text: "#dde4ff",
          "text-muted": "#6878aa",
          "text-dim": "#2a3660",
        },
      },
      fontFamily: {
        hud: ["Orbitron", "monospace"],
        mono: ["JetBrains Mono", "monospace"],
        body: ["Rajdhani", "sans-serif"],
      },
      animation: {
        heartbeat: "heartbeat 2.2s ease-in-out infinite",
        float: "float 3.5s ease-in-out infinite",
        "spin-slow": "spin 7s linear infinite",
        blob: "blob 4.5s ease-in-out infinite",
        "mic-pulse": "micPulse 2.5s ease-in-out infinite",
      },
      keyframes: {
        heartbeat: {
          "0%, 100%": { transform: "scale(1)", opacity: "1" },
          "50%": { transform: "scale(0.6)", opacity: "0.5" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-8px)" },
        },
        blob: {
          "0%, 100%": { borderRadius: "50%" },
          "25%": { borderRadius: "62% 38% 56% 44%" },
          "50%": { borderRadius: "44% 56% 38% 62%" },
          "75%": { borderRadius: "56% 44% 62% 38%" },
        },
        micPulse: {
          "0%, 100%": { boxShadow: "0 8px 28px rgba(99,102,241,0.38)" },
          "50%": { boxShadow: "0 8px 40px rgba(99,102,241,0.62)" },
        },
      },
      backdropBlur: {
        xs: "2px",
      },
    },
  },
  plugins: [],
};
