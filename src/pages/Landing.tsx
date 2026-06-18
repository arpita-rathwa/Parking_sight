import { motion } from "framer-motion";
import { Camera, Shield, ArrowRight, Circle } from "lucide-react";
import { Link } from "wouter";
import { FloatingLights, AnimatedCanvas } from "@/components/CinematicBackground";
import { WebGLBackground } from "@/components/WebGLBackground";
import { ElegantShape } from "@/components/ui/shape-landing-hero";

const orbitron = { fontFamily: "'Orbitron', sans-serif" };

export default function Landing() {
  const fadeUpVariants = {
    hidden: { opacity: 0, y: 30 },
    visible: (i: number) => ({
      opacity: 1,
      y: 0,
      transition: {
        duration: 1,
        delay: 0.4 + i * 0.18,
        ease: [0.25, 0.4, 0.25, 1] as [number, number, number, number],
      },
    }),
  };

  return (
    <div className="min-h-[100dvh] bg-[#0B1120] text-white relative overflow-hidden flex flex-col items-center justify-center">
      {/* Background layers — deepest first */}
      <WebGLBackground />
      <FloatingLights />
      <AnimatedCanvas />

      {/* ElegantShape decorations */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none z-[2]">
        <ElegantShape
          delay={0.3} width={620} height={145} rotate={12}
          gradient="from-blue-500/[0.10]"
          className="left-[-12%] top-[18%]"
        />
        <ElegantShape
          delay={0.5} width={520} height={125} rotate={-15}
          gradient="from-purple-500/[0.10]"
          className="right-[-6%] top-[68%]"
        />
        <ElegantShape
          delay={0.4} width={280} height={75} rotate={-8}
          gradient="from-violet-500/[0.10]"
          className="left-[6%] bottom-[8%]"
        />
        <ElegantShape
          delay={0.6} width={190} height={55} rotate={20}
          gradient="from-cyan-500/[0.10]"
          className="right-[18%] top-[10%]"
        />
        <ElegantShape
          delay={0.7} width={140} height={38} rotate={-25}
          gradient="from-indigo-500/[0.10]"
          className="left-[22%] top-[6%]"
        />
      </div>

      {/* Content */}
      <div className="relative z-10 container mx-auto px-6 py-20 flex flex-col items-center text-center">

        {/* Badge */}
        <motion.div
          custom={0}
          variants={fadeUpVariants}
          initial="hidden"
          animate="visible"
          className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/[0.04] border border-white/[0.08] mb-10"
        >
          <Circle className="h-2 w-2 fill-blue-400/80 text-blue-400/80" />
          <span className="text-xs text-white/55 tracking-[0.2em] uppercase font-medium">
            AI Parking Intelligence System
          </span>
        </motion.div>

        {/* Title */}
        <motion.div
          custom={1}
          variants={fadeUpVariants}
          initial="hidden"
          animate="visible"
          className="mb-5"
        >
          <h1
            className="text-6xl md:text-8xl lg:text-9xl font-black leading-none bg-clip-text text-transparent bg-gradient-to-b from-white via-white to-white/75"
            style={{
              ...orbitron,
              letterSpacing: "0.04em",
              textShadow: "0 0 80px rgba(59,130,246,0.35)",
            }}
            data-testid="text-hero-title"
          >
            ParkSight
          </h1>
        </motion.div>

        {/* Subtitle */}
        <motion.p
          custom={2}
          variants={fadeUpVariants}
          initial="hidden"
          animate="visible"
          className="text-lg md:text-xl bg-clip-text text-transparent bg-gradient-to-r from-blue-300 via-white/80 to-purple-300 mb-5 font-semibold tracking-[0.15em] uppercase"
          data-testid="text-hero-subtitle"
        >
          AI-Powered Parking Intelligence &amp; Enforcement
        </motion.p>

        {/* Description */}
        <motion.p
          custom={3}
          variants={fadeUpVariants}
          initial="hidden"
          animate="visible"
          className="text-base md:text-lg text-white/40 max-w-2xl mx-auto mb-12 leading-relaxed font-light tracking-wide"
          data-testid="text-hero-description"
        >
          Transforming urban mobility by detecting parking-induced congestion and enabling smarter enforcement.
        </motion.p>

        {/* CTA */}
        <motion.div
          custom={4}
          variants={fadeUpVariants}
          initial="hidden"
          animate="visible"
        >
          <Link
            href="/login"
            className="inline-flex items-center gap-3 px-10 py-4 rounded-full bg-gradient-to-r from-blue-600 to-purple-700 font-bold text-sm uppercase tracking-widest hover:shadow-[0_0_40px_rgba(59,130,246,0.55)] transition-all duration-300 hover:scale-105 hover:from-blue-500 hover:to-purple-600"
            style={orbitron}
            data-testid="link-login-cta"
          >
            Login to Dashboard
            <ArrowRight className="w-5 h-5" />
          </Link>
        </motion.div>

        {/* Cards */}
        <motion.div
          className="mt-28 grid grid-cols-1 md:grid-cols-2 gap-8 w-full max-w-5xl"
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.1, duration: 0.8 }}
        >
          {/* Card 1 */}
          <div
            className="relative group rounded-2xl bg-white/[0.04] backdrop-blur-xl border border-white/[0.08] p-8 hover:border-blue-400/30 transition-all duration-500 hover:-translate-y-2 overflow-hidden"
            data-testid="card-real-time-detection"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            <div className="relative z-10 flex flex-col items-start text-left">
              <div className="p-4 rounded-xl bg-white/[0.05] border border-white/[0.1] mb-6">
                <Camera className="w-8 h-8 text-blue-400 drop-shadow-[0_0_10px_rgba(96,165,250,0.8)]" />
              </div>
              <h3
                className="text-lg font-bold mb-3 text-white tracking-wide uppercase"
                style={orbitron}
              >
                Real-Time Detection
              </h3>
              <p className="text-white/40 leading-relaxed text-sm font-light tracking-wide">
                Monitor parking violations and congestion hotspots instantly using AI-powered analysis.
              </p>
            </div>
          </div>

          {/* Card 2 */}
          <div
            className="relative group rounded-2xl bg-white/[0.04] backdrop-blur-xl border border-white/[0.08] p-8 hover:border-blue-400/30 transition-all duration-500 hover:-translate-y-2 overflow-hidden"
            data-testid="card-smarter-enforcement"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-purple-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            <div className="relative z-10 flex flex-col items-start text-left">
              <div className="p-4 rounded-xl bg-white/[0.05] border border-white/[0.1] mb-6">
                <Shield className="w-8 h-8 text-blue-400 drop-shadow-[0_0_10px_rgba(96,165,250,0.8)]" />
              </div>
              <h3
                className="text-lg font-bold mb-3 text-white tracking-wide uppercase"
                style={orbitron}
              >
                Smarter Enforcement
              </h3>
              <p className="text-white/40 leading-relaxed text-sm font-light tracking-wide">
                Prioritize high-impact zones and enable faster response for traffic officers.
              </p>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Bottom fade */}
      <div className="absolute inset-0 bg-gradient-to-t from-[#0B1120] via-transparent to-[#0B1120]/60 pointer-events-none z-[3]" />
    </div>
  );
}
