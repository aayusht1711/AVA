"use client";

import { useState } from "react";
import { signIn } from "next-auth/react";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    const res = await signIn("credentials", {
      email,
      password,
      redirect: false,
    });

    setLoading(false);

    if (res?.error) {
      setError("Invalid email or password");
    } else {
      router.push("/dashboard");
    }
  }

  return (
    <div className="min-h-screen w-full flex items-center justify-center relative overflow-hidden bg-[#03060f]">
      {/* BG grid */}
      <div className="fixed inset-0 bg-grid pointer-events-none" />
      <div className="fixed inset-0 pointer-events-none"
        style={{ background: "radial-gradient(ellipse at 40% 30%, rgba(79,70,229,0.14) 0%, transparent 65%)" }} />
      <div className="fixed inset-0 pointer-events-none"
        style={{ background: "radial-gradient(ellipse at center, transparent 30%, rgba(3,6,15,0.85) 100%)" }} />

      <div className="relative z-10 w-full max-w-sm px-6">
        {/* Logo */}
        <div className="flex flex-col items-center gap-3 mb-8">
          <div className="relative w-16 h-16">
            <div className="absolute inset-0 rounded-full border border-[rgba(129,140,248,0.4)] animate-spin-slow" />
            <div className="absolute inset-2 rounded-full border border-[rgba(99,102,241,0.22)] animate-[spin_9s_linear_infinite_reverse]" />
            <div className="absolute inset-4 rounded-full"
              style={{ background: "linear-gradient(135deg,#818cf8,#4f46e5)", animation: "pulse 2.5s ease-in-out infinite" }} />
          </div>
          <div className="font-hud text-2xl font-black text-[#818cf8] tracking-[0.18em]"
            style={{ textShadow: "0 0 18px rgba(129,140,248,0.35)" }}>
            AVA
          </div>
          <div className="font-mono text-xs text-[#2a3660] tracking-wider">
            Autonomous Virtual Assistant
          </div>
        </div>

        {/* Card */}
        <div className="glass rounded-2xl p-7 relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-px"
            style={{ background: "linear-gradient(90deg, transparent, #6366f1, transparent)", opacity: 0.4 }} />

          <h1 className="font-hud text-base font-bold text-[#dde4ff] tracking-wider mb-1">
            Welcome back
          </h1>
          <p className="font-mono text-xs text-[#2a3660] mb-6">
            Sign in to your AVA account
          </p>

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="font-hud text-[10px] text-[#6878aa] tracking-[0.12em] uppercase">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="you@example.com"
                className="w-full bg-[rgba(8,14,30,0.97)] border border-[rgba(99,102,241,0.2)] rounded-xl px-4 py-3 text-sm text-[#dde4ff] placeholder-[#2a3660] outline-none font-body transition-all focus:border-[rgba(99,102,241,0.5)]"
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="font-hud text-[10px] text-[#6878aa] tracking-[0.12em] uppercase">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder="••••••••"
                className="w-full bg-[rgba(8,14,30,0.97)] border border-[rgba(99,102,241,0.2)] rounded-xl px-4 py-3 text-sm text-[#dde4ff] placeholder-[#2a3660] outline-none font-body transition-all focus:border-[rgba(99,102,241,0.5)]"
              />
            </div>

            {error && (
              <div className="bg-[rgba(248,113,113,0.1)] border border-[rgba(248,113,113,0.3)] rounded-xl px-4 py-3 font-mono text-xs text-[#f87171]">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full h-12 rounded-xl font-hud text-xs font-bold tracking-[0.12em] text-white uppercase transition-all disabled:opacity-60"
              style={{
                background: "linear-gradient(135deg, #4f46e5, #6366f1)",
                boxShadow: "0 8px 28px rgba(99,102,241,0.42)",
              }}
            >
              {loading ? "Signing in..." : "Sign In"}
            </button>
          </form>

          <p className="text-center font-mono text-xs text-[#2a3660] mt-5">
            No account?{" "}
            <Link href="/signup" className="text-[#818cf8] hover:text-[#a5b4fc] transition-colors">
              Create one
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
