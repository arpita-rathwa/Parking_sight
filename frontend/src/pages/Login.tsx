import { useState } from "react";
import { motion } from "framer-motion";
import { useLocation } from "wouter";
import { ArrowRight, Mail, Lock, ArrowLeft, Loader2 } from "lucide-react";
import { Link } from "wouter";
import { FloatingLights, AnimatedCanvas } from "@/components/CinematicBackground";
import { setToken } from "@/lib/api";
const API_BASE = import.meta.env.VITE_API_URL || "/api";

const GoogleIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">
    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" />
    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
  </svg>
);

export default function Login() {
  const [, setLocation] = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [emailFocused, setEmailFocused] = useState(false);
  const [passwordFocused, setPasswordFocused] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const formData = new URLSearchParams();
      formData.append("username", email);
      formData.append("password", password);
      const res = await fetch(`${API_BASE}/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData,
      });
      if (!res.ok) {
        const err = await res.text();
        throw new Error(err || "Invalid credentials");
      }
      const data = await res.json();
      setToken(data.access_token);
      setLocation("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[100dvh] bg-[#0B1120] text-white flex items-center justify-center p-6 relative overflow-hidden">
      <FloatingLights />
      <AnimatedCanvas />

      <div className="absolute inset-0 bg-[#0B1120]/60 z-[1] pointer-events-none" />

      <Link
        href="/"
        className="absolute top-6 left-6 z-20 inline-flex items-center gap-2 text-slate-400 hover:text-blue-300 transition-colors text-xs tracking-widest uppercase font-medium"
        data-testid="link-back-home"
      >
        <ArrowLeft className="w-4 h-4" />
        Back
      </Link>

      <motion.div
        className="w-full max-w-md relative z-10"
        initial={{ opacity: 0, y: 32, scale: 0.97 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        whileHover={{ y: -3 }}
      >
        <div
          className="relative rounded-[28px] p-8 overflow-hidden"
          style={{
            background: "rgba(255,255,255,0.08)",
            backdropFilter: "blur(25px)",
            WebkitBackdropFilter: "blur(25px)",
            border: "1px solid rgba(255,255,255,0.15)",
            boxShadow: "0 32px 80px rgba(0,0,0,0.6), 0 0 60px rgba(59,130,246,0.08), inset 0 1px 0 rgba(255,255,255,0.1)",
          }}
        >
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-64 h-px bg-gradient-to-r from-transparent via-blue-400/50 to-transparent" />

          <div className="text-center mb-8">
            <motion.h1
              className="text-3xl font-black mb-2"
              style={{ fontFamily: "'Orbitron', sans-serif", letterSpacing: "0.06em", textShadow: "0 0 30px rgba(59,130,246,0.5)" }}
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2, duration: 0.5 }}
              data-testid="text-login-title"
            >
              ParkSight
            </motion.h1>
            <motion.p
              className="text-blue-300/80 text-xs tracking-widest uppercase font-semibold mb-3"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.35, duration: 0.5 }}
              data-testid="text-login-subtitle"
            >
              AI-Powered Parking Intelligence
            </motion.p>
            <motion.p
              className="text-slate-400 text-sm font-light"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.45, duration: 0.5 }}
            >
              Sign in to access the command center.
            </motion.p>
          </div>

          <motion.button
            className="w-full flex items-center justify-center gap-3 bg-white text-gray-700 rounded-2xl py-3.5 px-6 font-semibold text-sm hover:bg-gray-50 transition-all duration-200 hover:scale-[1.02]"
            style={{ boxShadow: "0 4px 16px rgba(0,0,0,0.25), 0 1px 3px rgba(0,0,0,0.15)" }}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.4 }}
            whileTap={{ scale: 0.98 }}
            whileHover={{ boxShadow: "0 8px 28px rgba(0,0,0,0.3)" }}
            data-testid="button-google-login"
          >
            <GoogleIcon />
            Continue with Google
          </motion.button>

          <motion.div
            className="flex items-center gap-4 my-6"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6, duration: 0.4 }}
          >
            <div className="flex-1 h-px bg-white/10" />
            <span className="text-slate-500 text-xs tracking-widest uppercase font-medium">or</span>
            <div className="flex-1 h-px bg-white/10" />
          </motion.div>

          <motion.form
            onSubmit={handleSubmit}
            className="space-y-4"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.65, duration: 0.5 }}
          >
            <div>
              <label className="block text-xs tracking-wider uppercase text-slate-400 mb-2 font-medium">
                Email Address
              </label>
              <div
                className="relative rounded-xl transition-all duration-300"
                style={{
                  background: "rgba(255,255,255,0.05)",
                  border: emailFocused ? "1px solid rgba(59,130,246,0.7)" : "1px solid rgba(255,255,255,0.08)",
                  boxShadow: emailFocused ? "0 0 16px rgba(59,130,246,0.2)" : "none",
                }}
              >
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  onFocus={() => setEmailFocused(true)}
                  onBlur={() => setEmailFocused(false)}
                  placeholder="officer@city.gov"
                  className="w-full bg-transparent text-white placeholder:text-slate-600 text-sm py-3.5 pl-11 pr-4 rounded-xl outline-none"
                  data-testid="input-login-email"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs tracking-wider uppercase text-slate-400 mb-2 font-medium">
                Password
              </label>
              <div
                className="relative rounded-xl transition-all duration-300"
                style={{
                  background: "rgba(255,255,255,0.05)",
                  border: passwordFocused ? "1px solid rgba(59,130,246,0.7)" : "1px solid rgba(255,255,255,0.08)",
                  boxShadow: passwordFocused ? "0 0 16px rgba(59,130,246,0.2)" : "none",
                }}
              >
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  onFocus={() => setPasswordFocused(true)}
                  onBlur={() => setPasswordFocused(false)}
                  placeholder="••••••••"
                  className="w-full bg-transparent text-white placeholder:text-slate-600 text-sm py-3.5 pl-11 pr-4 rounded-xl outline-none"
                  data-testid="input-login-password"
                />
              </div>
            </div>

            {error && (
              <motion.p
                initial={{ opacity: 0, y: -5 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-red-400 text-xs font-medium text-center"
              >
                {error}
              </motion.p>
            )}
            <motion.button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-3 rounded-2xl py-4 font-bold text-sm tracking-wide text-white transition-all duration-300 hover:scale-[1.02] disabled:opacity-60 disabled:cursor-not-allowed"
              style={{
                background: "linear-gradient(135deg, #2563EB 0%, #7C3AED 100%)",
                boxShadow: "0 0 20px rgba(37,99,235,0.35)",
              }}
              whileHover={{ boxShadow: "0 0 40px rgba(37,99,235,0.6)" }}
              whileTap={{ scale: 0.98 }}
              data-testid="button-access-dashboard"
            >
              {loading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  Access Dashboard
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </motion.button>
          </motion.form>

          <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-48 h-px bg-gradient-to-r from-transparent via-purple-400/40 to-transparent" />
        </div>
      </motion.div>
    </div>
  );
}
