import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  LayoutDashboard, AlertTriangle, BarChart2, Camera as CameraIcon, Settings, Radio, BrainCircuit,
  Search, Bell, Globe, Activity, Users, Clock, AlertOctagon, ChevronLeft, ChevronRight,
  Sun, Target, Navigation, TrendingUp, CheckCircle, Zap, Layers, MapPin
} from 'lucide-react';
import { useLocation } from 'wouter';
import { FloatingLights } from '@/components/CinematicBackground';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, BarChart, Bar, LineChart, Line } from 'recharts';

function AnimatedCounter({ value, duration = 2 }: { value: number; duration?: number }) {
  const [count, setCount] = useState(0);

  useEffect(() => {
    let start = 0;
    const startTime = performance.now();

    const animate = (time: number) => {
      const elapsed = (time - startTime) / 1000;
      const progress = Math.min(elapsed / duration, 1);
      const easeOutQuart = 1 - Math.pow(1 - progress, 4);
      
      setCount(Math.floor(easeOutQuart * value) + (progress === 1 ? (value % 1) : 0));
      
      if (progress < 1) {
        requestAnimationFrame(animate);
      } else {
        setCount(value);
      }
    };
    
    requestAnimationFrame(animate);
  }, [value, duration]);

  return <span>{typeof value === 'number' && value % 1 !== 0 ? count.toFixed(1) : count}</span>;
}

function LiveClock() {
  const [time, setTime] = useState(new Date());
  
  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="text-slate-300 text-sm font-medium tracking-wide">
      {time.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
      <span className="mx-2 opacity-50">|</span>
      {time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
    </div>
  );
}

const violationData = [
  { time: '6am', value: 12 },
  { time: '7am', value: 28 },
  { time: '8am', value: 45 },
  { time: '9am', value: 52 },
  { time: '10am', value: 38 },
  { time: '11am', value: 29 },
];

const congestionData = [
  { time: '6am', value: 42 },
  { time: '7am', value: 55 },
  { time: '8am', value: 68 },
  { time: '9am', value: 75 },
  { time: '10am', value: 81 },
  { time: '11am', value: 78 },
];

const responseTimeData = [
  { time: '6am', value: 4.2 },
  { time: '7am', value: 3.8 },
  { time: '8am', value: 3.5 },
  { time: '9am', value: 3.4 },
  { time: '10am', value: 3.2 },
  { time: '11am', value: 3.4 },
];

export default function CommandCenter() {
  const [collapsed, setCollapsed] = useState(false);
  const [, setLocation] = useLocation();

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.1 }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
  };

  const [mapAnimate, setMapAnimate] = useState(false);
  useEffect(() => {
    const t = setTimeout(() => setMapAnimate(true), 500);
    return () => clearTimeout(t);
  }, []);

  return (
    <div className="h-screen w-full bg-[#0B1120] text-white flex overflow-hidden font-sans">
      <FloatingLights />
      <style>{`
        @keyframes sonar-pulse {
          0% { r: 16px; opacity: 0.6; }
          100% { r: 60px; opacity: 0; }
        }
        @keyframes dash-flow {
          to { stroke-dashoffset: -20; }
        }
      `}</style>
      
      {/* Sidebar */}
      <aside className={`fixed top-0 left-0 h-full z-30 flex flex-col transition-all duration-300 border-r border-white/[0.06] bg-white/[0.03] backdrop-blur-xl ${collapsed ? 'w-16' : 'w-64'}`}>
        <div className="h-14 flex items-center justify-between px-4 border-b border-white/[0.06]">
          {!collapsed && (
            <span className="font-bold text-lg text-blue-400 drop-shadow-[0_0_8px_rgba(96,165,250,0.8)]" style={{ fontFamily: "'Orbitron', sans-serif", letterSpacing: "0.05em" }}>
              ParkSight
            </span>
          )}
          <button 
            onClick={() => setCollapsed(!collapsed)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors mx-auto"
            data-testid="btn-toggle-sidebar"
          >
            {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
          </button>
        </div>
        
        <nav className="flex-1 py-6 px-3 space-y-2">
          {[
            { icon: Globe, label: 'Command', active: true, path: '/command' },
            { icon: LayoutDashboard, label: 'Dashboard', active: false, path: '/dashboard' },
            { icon: AlertTriangle, label: 'Alerts', active: false, path: '/alerts' },
            { icon: BarChart2, label: 'Analytics', active: false, path: '/analytics' },
            { icon: CameraIcon, label: 'Cameras', active: false, path: '/cameras' },
            { icon: Radio, label: 'Dispatch', active: false, path: '/dispatch' },
            { icon: BrainCircuit, label: 'AI Insights', active: false, path: '/ai' },
            { icon: Settings, label: 'Settings', active: false, path: '/settings' },
          ].map((item, idx) => (
            <button
              key={idx}
              onClick={() => item.path !== '#' && setLocation(item.path)}
              className={`w-full flex items-center ${collapsed ? 'justify-center' : 'justify-start gap-3'} p-3 rounded-xl transition-all duration-200 group relative
                ${item.active 
                  ? 'bg-blue-500/10 text-blue-400 border-l-2 border-blue-500 shadow-[inset_2px_0_10px_rgba(59,130,246,0.1)]' 
                  : 'text-slate-400 hover:bg-white/[0.05] hover:text-slate-200'}`}
              title={collapsed ? item.label : undefined}
            >
              <item.icon size={20} className={item.active ? "drop-shadow-[0_0_8px_rgba(59,130,246,0.8)]" : ""} />
              {!collapsed && <span className="font-medium text-sm tracking-wide">{item.label}</span>}
            </button>
          ))}
        </nav>
      </aside>

      {/* Main Container */}
      <div className={`flex-1 flex flex-col transition-all duration-300 relative z-20 ${collapsed ? 'ml-16' : 'ml-64'}`}>
        
        {/* Top Navbar */}
        <header className="h-14 fixed top-0 right-0 z-20 flex items-center justify-between px-6 border-b border-white/[0.06] bg-[#0B1120]/80 backdrop-blur-lg transition-all duration-300" style={{ left: collapsed ? '4rem' : '16rem' }}>
          <div className="flex items-center gap-4 flex-1">
            <div className="flex flex-col">
              <h1 className="text-xl font-bold tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400 drop-shadow-[0_0_10px_rgba(59,130,246,0.5)]" style={{ fontFamily: "'Orbitron', sans-serif" }}>
                City Command Center
              </h1>
              <p className="text-[10px] text-slate-400 uppercase tracking-widest hidden md:block">Real-time city-wide parking intelligence and congestion monitoring.</p>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 bg-green-500/10 border border-green-500/20 rounded-full px-3 py-1 shadow-[0_0_10px_rgba(34,197,94,0.1)]">
              <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse shadow-[0_0_8px_rgba(34,197,94,0.8)]" />
              <span className="text-xs font-semibold text-green-400 tracking-wide uppercase">Live</span>
            </div>
            
            <LiveClock />
            
            <div className="flex items-center gap-2 bg-white/5 border border-white/10 rounded-full px-3 py-1">
              <Sun size={14} className="text-yellow-400" />
              <span className="text-xs font-semibold text-slate-300">28 degC Bangalore</span>
            </div>

            <div className="flex items-center gap-2 bg-orange-500/10 border border-orange-500/20 rounded-full px-3 py-1 shadow-[0_0_10px_rgba(249,115,22,0.1)]">
              <AlertTriangle size={14} className="text-orange-400" />
              <span className="text-xs font-semibold text-orange-400 tracking-wide uppercase">High Traffic</span>
            </div>
          </div>
        </header>

        {/* Scrollable Content */}
        <main className="flex-1 overflow-y-auto mt-14 p-6 custom-scrollbar">
          <motion.div 
            variants={containerVariants}
            initial="hidden"
            animate="show"
            className="max-w-[1400px] mx-auto space-y-4 pb-20"
          >
            {/* KPI Cards Row (Compact) */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
              {[
                { title: 'Active Violations', value: 127, icon: AlertTriangle, color: 'text-red-400', bg: 'bg-red-500/10', trend: '+12 this hour' },
                { title: 'Critical Zones', value: 4, icon: AlertOctagon, color: 'text-red-400', bg: 'bg-red-500/10', trend: 'Requires immediate action' },
                { title: 'Officers Deployed', value: 12, icon: Users, color: 'text-blue-400', bg: 'bg-blue-500/10', trend: '5 en route' },
                { title: 'Avg Response Time', value: 3.4, icon: Clock, color: 'text-purple-400', bg: 'bg-purple-500/10', trend: 'v 0.3 min', isFloat: true },
                { title: 'Congestion Score', value: 81, icon: Activity, color: 'text-orange-400', bg: 'bg-orange-500/10', trend: '^ 6pts today' },
                { title: 'Detection Accuracy', value: 94, icon: Target, color: 'text-green-400', bg: 'bg-green-500/10', trend: '^ 0.5%', isPercent: true },
              ].map((stat, i) => (
                <motion.div 
                  key={i} 
                  variants={itemVariants}
                  className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.07] rounded-xl p-3 flex flex-col hover:-translate-y-1 hover:border-white/20 transition-all duration-300"
                >
                  <div className="flex justify-between items-start mb-1">
                    <div className={`p-1.5 rounded-lg ${stat.bg}`}>
                      <stat.icon size={16} className={stat.color} />
                    </div>
                    <span className="text-[9px] font-semibold text-slate-400 bg-white/5 px-1.5 py-0.5 rounded uppercase tracking-wider">{stat.trend}</span>
                  </div>
                  <div className="mt-1">
                    <h3 className="text-slate-400 text-[10px] font-bold uppercase tracking-widest">{stat.title}</h3>
                    <p className="text-2xl font-black tracking-tight text-white drop-shadow-md leading-none mt-1">
                      <AnimatedCounter value={stat.value} />
                      {stat.isFloat && <span className="text-xs font-medium text-slate-500 ml-1">min</span>}
                      {stat.isPercent && <span className="text-xs font-medium text-slate-500 ml-1">%</span>}
                    </p>
                  </div>
                </motion.div>
              ))}
            </div>

            {/* MAIN MAP SECTION */}
            <motion.div variants={itemVariants} className="w-full h-[420px] bg-[#030812] rounded-2xl border border-white/[0.07] relative overflow-hidden shadow-[0_0_60px_rgba(59,130,246,0.12)] group">
              <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(59,130,246,0.05)_0%,transparent_70%)] pointer-events-none z-0" />
              
              <svg width="100%" height="100%" viewBox="0 0 1200 420" preserveAspectRatio="xMidYMid slice" className="absolute inset-0 z-0">
                {/* DISTRICT SHADING */}
                <polygon points="0,0 600,0 500,210 0,210" fill="rgba(59,130,246,0.04)" />
                <polygon points="600,0 1200,0 1200,210 500,210" fill="rgba(139,92,246,0.03)" />
                <polygon points="1200,210 1200,420 700,420 500,210" fill="rgba(16,185,129,0.03)" />
                <polygon points="0,210 500,210 700,420 0,420" fill="rgba(245,158,11,0.03)" />

                {/* GRID SYSTEM */}
                {/* Vertical Lines */}
                {Array.from({ length: 12 }).map((_, i) => (
                  <line key={`v-${i}`} x1={i * 100} y1="0" x2={i * 100} y2="420" stroke="white" strokeWidth="1" opacity="0.04" />
                ))}
                {/* Horizontal Lines */}
                {Array.from({ length: 12 }).map((_, i) => (
                  <line key={`h-${i}`} x1="0" y1={i * 35} x2="1200" y2={i * 35} stroke="white" strokeWidth="1" opacity="0.04" />
                ))}

                {/* Main Roads */}
                <line x1="0" y1="210" x2="1200" y2="210" stroke="white" strokeWidth="2" opacity="0.12" />
                <line x1="0" y1="140" x2="1200" y2="140" stroke="white" strokeWidth="2" opacity="0.12" />
                <line x1="600" y1="0" x2="600" y2="420" stroke="white" strokeWidth="2" opacity="0.12" />
                <line x1="900" y1="0" x2="900" y2="420" stroke="white" strokeWidth="2" opacity="0.12" />

                {/* Arterial Roads */}
                <polyline points="0,0 1200,420" stroke="white" strokeWidth="1" opacity="0.07" fill="none" />
                <polyline points="0,420 1200,0" stroke="white" strokeWidth="1" opacity="0.07" fill="none" />
                <polyline points="300,0 900,420" stroke="white" strokeWidth="1" opacity="0.07" fill="none" />
                <polyline points="0,210 600,420" stroke="white" strokeWidth="1" opacity="0.07" fill="none" />
                <polyline points="600,0 1200,210" stroke="white" strokeWidth="1" opacity="0.07" fill="none" />
                <polyline points="900,0 300,420" stroke="white" strokeWidth="1" opacity="0.07" fill="none" />

                {/* TRAFFIC FLOW LINES */}
                <path d="M 0 210 Q 300 210 600 210" fill="none" stroke="#22c55e" strokeWidth="3" strokeDasharray="10 10" style={{ animation: 'dash-flow 1s linear infinite' }} />
                <path d="M 600 210 Q 900 210 1200 210" fill="none" stroke="#f97316" strokeWidth="3" strokeDasharray="10 10" style={{ animation: 'dash-flow 1s linear infinite reverse' }} />
                <path d="M 600 0 Q 600 210 600 420" fill="none" stroke="#eab308" strokeWidth="3" strokeDasharray="10 10" style={{ animation: 'dash-flow 1s linear infinite' }} />
                <path d="M 0 0 L 1200 420" fill="none" stroke="#ef4444" strokeWidth="3" strokeDasharray="15 15" opacity="0.6" style={{ animation: 'dash-flow 0.8s linear infinite' }} />

                {/* CONGESTION HOTSPOTS */}
                {/* Railway Station */}
                <g transform="translate(300, 100)">
                  <circle cx="0" cy="0" r="40" fill="#EF4444" opacity="0.08" />
                  <circle cx="0" cy="0" r="28" fill="#EF4444" opacity="0.15" />
                  <circle cx="0" cy="0" r="16" fill="#EF4444" opacity="0.5" />
                  <circle cx="0" cy="0" r="16" fill="transparent" stroke="#EF4444" strokeWidth="2" style={{ animation: 'sonar-pulse 2s ease-out infinite' }} />
                  <circle cx="0" cy="0" r="16" fill="transparent" stroke="#EF4444" strokeWidth="2" style={{ animation: 'sonar-pulse 2s ease-out infinite 1s' }} />
                  <circle cx="0" cy="0" r="6" fill="#EF4444" />
                  <text x="25" y="-15" fill="white" fontSize="12" fontWeight="bold" className="drop-shadow-md font-sans">RAILWAY STATION</text>
                  <text x="25" y="0" fill="#EF4444" fontSize="10" fontWeight="bold" className="font-sans">SCORE 94</text>
                  <rect x="25" y="8" width="60" height="14" rx="2" fill="#EF4444" opacity="0.2" />
                  <text x="28" y="19" fill="#EF4444" fontSize="9" fontWeight="bold" className="font-sans">CRITICAL</text>
                </g>

                {/* Bus Stand */}
                <g transform="translate(200, 250)">
                  <circle cx="0" cy="0" r="35" fill="#F97316" opacity="0.08" />
                  <circle cx="0" cy="0" r="24" fill="#F97316" opacity="0.15" />
                  <circle cx="0" cy="0" r="14" fill="#F97316" opacity="0.5" />
                  <circle cx="0" cy="0" r="14" fill="transparent" stroke="#F97316" strokeWidth="2" style={{ animation: 'sonar-pulse 2.5s ease-out infinite' }} />
                  <circle cx="0" cy="0" r="6" fill="#F97316" />
                  <text x="20" y="-10" fill="white" fontSize="11" fontWeight="bold" className="drop-shadow-md font-sans">Bus Stand</text>
                  <text x="20" y="4" fill="#F97316" fontSize="10" fontWeight="bold" className="font-sans">Score 89</text>
                </g>

                {/* City Center */}
                <g transform="translate(600, 210)">
                  <circle cx="0" cy="0" r="50" fill="#EF4444" opacity="0.1" />
                  <circle cx="0" cy="0" r="35" fill="#EF4444" opacity="0.2" />
                  <circle cx="0" cy="0" r="20" fill="#EF4444" opacity="0.6" />
                  <circle cx="0" cy="0" r="20" fill="transparent" stroke="#EF4444" strokeWidth="2" style={{ animation: 'sonar-pulse 1.5s ease-out infinite' }} />
                  <circle cx="0" cy="0" r="20" fill="transparent" stroke="#EF4444" strokeWidth="2" style={{ animation: 'sonar-pulse 1.5s ease-out infinite 0.75s' }} />
                  <circle cx="0" cy="0" r="8" fill="#EF4444" className="drop-shadow-[0_0_10px_rgba(239,68,68,1)]" />
                  <text x="25" y="-15" fill="white" fontSize="14" fontWeight="bold" className="drop-shadow-md font-sans">CITY CENTER</text>
                  <text x="25" y="0" fill="#EF4444" fontSize="11" fontWeight="bold" className="font-sans">Score 86</text>
                </g>

                {/* Market Road */}
                <g transform="translate(850, 310)">
                  <circle cx="0" cy="0" r="30" fill="#F59E0B" opacity="0.1" />
                  <circle cx="0" cy="0" r="20" fill="#F59E0B" opacity="0.2" />
                  <circle cx="0" cy="0" r="12" fill="#F59E0B" opacity="0.5" />
                  <circle cx="0" cy="0" r="12" fill="transparent" stroke="#F59E0B" strokeWidth="2" style={{ animation: 'sonar-pulse 3s ease-out infinite' }} />
                  <circle cx="0" cy="0" r="5" fill="#F59E0B" />
                  <text x="18" y="-8" fill="white" fontSize="11" fontWeight="bold" className="font-sans">Market Road</text>
                  <text x="18" y="5" fill="#F59E0B" fontSize="10" fontWeight="bold" className="font-sans">Score 82</text>
                </g>

                {/* Hospital Circle */}
                <g transform="translate(980, 150)">
                  <circle cx="0" cy="0" r="25" fill="#3B82F6" opacity="0.1" />
                  <circle cx="0" cy="0" r="15" fill="#3B82F6" opacity="0.2" />
                  <circle cx="0" cy="0" r="10" fill="#3B82F6" opacity="0.5" />
                  <circle cx="0" cy="0" r="10" fill="transparent" stroke="#3B82F6" strokeWidth="2" style={{ animation: 'sonar-pulse 4s ease-out infinite' }} />
                  <circle cx="0" cy="0" r="4" fill="#3B82F6" />
                  <text x="16" y="-6" fill="white" fontSize="10" fontWeight="bold" className="font-sans">Hospital Circle</text>
                  <text x="16" y="6" fill="#3B82F6" fontSize="9" fontWeight="bold" className="font-sans">Score 75</text>
                </g>

                {/* OFFICER MARKERS */}
                {[
                  { id: 'O3', x: 280, y: 120, targetX: 300, targetY: 100 },
                  { id: 'O6', x: 620, y: 190, targetX: 600, targetY: 210 },
                  { id: 'O5', x: 170, y: 270, targetX: 200, targetY: 250 },
                  { id: 'O1', x: 400, y: 350 },
                  { id: 'O2', x: 750, y: 100 },
                  { id: 'O4', x: 1050, y: 300 },
                  { id: 'O7', x: 100, y: 150 },
                  { id: 'O8', x: 500, y: 50 },
                ].map((officer, i) => (
                  <g key={`off-${i}`}>
                    {officer.targetX && (
                      <line x1={officer.x} y1={officer.y} x2={officer.targetX} y2={officer.targetY} stroke="#3B82F6" strokeWidth="1" strokeDasharray="3 3" opacity="0.6" />
                    )}
                    <circle cx={officer.x} cy={officer.y} r="8" fill="#3B82F6" />
                    <text x={officer.x} y={officer.y + 3} fill="white" fontSize="9" fontWeight="bold" textAnchor="middle" className="font-sans">{officer.id}</text>
                  </g>
                ))}

                {/* CAMERA MARKERS */}
                {[
                  { id: '001', x: 350, y: 150 },
                  { id: '012', x: 250, y: 200 },
                  { id: '008', x: 650, y: 250 },
                  { id: '024', x: 800, y: 350 },
                  { id: '031', x: 1020, y: 120 },
                  { id: '019', x: 500, y: 280 },
                ].map((cam, i) => (
                  <g key={`cam-${i}`} transform={`translate(${cam.x}, ${cam.y})`}>
                    <polygon points="0,-6 6,0 0,6 -6,0" fill="#14B8A6" />
                    <text x="8" y="3" fill="#14B8A6" fontSize="8" fontWeight="bold" className="font-sans">CAM-{cam.id}</text>
                  </g>
                ))}
              </svg>

              {/* Map Overlay UI */}
              <div className="absolute top-4 left-4 bg-white/[0.04] backdrop-blur-md border border-white/[0.1] rounded-lg p-3 text-xs shadow-lg">
                <div className="font-bold text-slate-200 mb-2">Legend</div>
                <div className="flex flex-col gap-1.5">
                  <div className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-red-500"></span><span className="text-slate-300">Critical Zone</span></div>
                  <div className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-orange-500"></span><span className="text-slate-300">High Zone</span></div>
                  <div className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-amber-500"></span><span className="text-slate-300">Medium Zone</span></div>
                  <div className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-blue-500"></span><span className="text-slate-300">Officer</span></div>
                  <div className="flex items-center gap-2"><span className="w-2 h-2 rotate-45 bg-teal-500"></span><span className="text-slate-300">Camera</span></div>
                </div>
              </div>

              <div className="absolute top-4 right-4 bg-white/[0.04] backdrop-blur-md border border-white/[0.1] rounded-lg flex flex-col text-slate-400">
                <button className="p-2 hover:bg-white/10 hover:text-white transition-colors border-b border-white/[0.1]">+</button>
                <button className="p-2 hover:bg-white/10 hover:text-white transition-colors">-</button>
              </div>

              <div className="absolute bottom-4 left-4 text-xs font-mono text-slate-500 bg-[#030812]/50 px-2 py-1 rounded">
                12.9716 deg N, 77.5946 deg E
              </div>

              <div className="absolute bottom-4 right-4 text-xs font-bold text-slate-400 tracking-widest bg-[#030812]/50 px-2 py-1 rounded uppercase">
                Bangalore City Grid -- Live Feed
              </div>
            </motion.div>

            {/* THREE-COLUMN ROW */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              
              {/* Left -- Live Events Timeline */}
              <motion.div variants={itemVariants} className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.07] rounded-2xl p-5 flex flex-col h-[320px]">
                <h2 className="text-sm font-bold tracking-wide flex items-center gap-2 mb-4 text-slate-200">
                  <Activity size={16} className="text-slate-400" />
                  LIVE EVENTS
                  <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse ml-auto" />
                </h2>
                <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar space-y-4">
                  {[
                    { time: '10:45 AM', icon: AlertTriangle, color: 'text-red-400', text: 'Illegal parking detected -- CAM-012' },
                    { time: '10:43 AM', icon: Navigation, color: 'text-blue-400', text: 'Officer 3 dispatched to Railway Station' },
                    { time: '10:41 AM', icon: TrendingUp, color: 'text-orange-400', text: 'Congestion score increased to 94' },
                    { time: '10:39 AM', icon: CheckCircle, color: 'text-green-400', text: 'Zone resolved at Market Road' },
                    { time: '10:35 AM', icon: CameraIcon, color: 'text-teal-400', text: 'CAM-008 came back online' },
                    { time: '10:31 AM', icon: AlertOctagon, color: 'text-red-400', text: 'Critical alert -- City Center' },
                    { time: '10:27 AM', icon: CheckCircle, color: 'text-green-400', text: 'Violation resolved by Officer 2' },
                    { time: '10:22 AM', icon: Zap, color: 'text-purple-400', text: 'AI model retrained -- accuracy 94%' },
                  ].map((event, i) => (
                    <motion.div 
                      key={i} 
                      initial={{ opacity: 0, x: -10 }}
                      animate={mapAnimate ? { opacity: 1, x: 0 } : {}}
                      transition={{ delay: i * 0.1 }}
                      className="flex gap-3 items-start relative before:absolute before:left-2.5 before:top-6 before:bottom-[-16px] before:w-px before:bg-white/[0.1] last:before:hidden"
                    >
                      <div className={`p-1 rounded-full bg-white/5 border border-white/10 ${event.color} relative z-10`}>
                        <event.icon size={12} />
                      </div>
                      <div className="flex-1 pb-2">
                        <div className="text-[10px] font-bold text-slate-500 mb-0.5">{event.time}</div>
                        <div className="text-xs text-slate-300 font-medium">{event.text}</div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </motion.div>

              {/* Center -- AI Insight Panel */}
              <motion.div variants={itemVariants} className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.07] rounded-2xl p-6 flex flex-col relative overflow-hidden group shadow-[0_0_30px_rgba(139,92,246,0.05)]">
                <div className="absolute inset-0 border-2 border-transparent group-hover:border-purple-500/20 rounded-2xl transition-colors duration-500" />
                <div className="absolute -top-20 -right-20 w-40 h-40 bg-purple-500/10 blur-[50px] rounded-full pointer-events-none" />
                <div className="absolute -bottom-20 -left-20 w-40 h-40 bg-blue-500/10 blur-[50px] rounded-full pointer-events-none" />
                
                <h2 className="text-sm font-bold tracking-wide flex items-center gap-2 mb-4 text-slate-200 relative z-10">
                  <BrainCircuit size={18} className="text-purple-400 drop-shadow-[0_0_8px_rgba(168,85,247,0.8)]" />
                  AI COMMAND INSIGHT
                </h2>
                
                <div className="flex-1 flex flex-col justify-center relative z-10">
                  <p className="text-lg md:text-xl font-bold text-white italic text-center leading-snug drop-shadow-md mb-6">
                    "Railway Station congestion is expected to escalate within the next 30 minutes."
                  </p>
                  
                  <div className="mb-6">
                    <div className="flex justify-between items-end mb-2">
                      <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">Confidence</span>
                      <span className="text-sm font-black text-purple-400">91%</span>
                    </div>
                    <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden border border-white/10">
                      <motion.div 
                        initial={{ width: 0 }}
                        animate={mapAnimate ? { width: '91%' } : {}}
                        transition={{ duration: 1, delay: 0.5 }}
                        className="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full shadow-[0_0_10px_rgba(168,85,247,0.5)]"
                      />
                    </div>
                  </div>

                  <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-4 mb-6 shadow-[inset_0_0_15px_rgba(245,158,11,0.05)]">
                    <p className="text-sm font-bold text-amber-400 text-center">
                      Deploy 2 additional officers to Railway Station immediately.
                    </p>
                  </div>

                  <div className="flex gap-3 mb-4">
                    <button data-testid="btn-command-dispatch" className="flex-1 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold py-2.5 rounded-lg shadow-[0_0_15px_rgba(59,130,246,0.4)] transition-all text-sm">
                      Dispatch Officers
                    </button>
                    <button data-testid="btn-command-ai" onClick={() => setLocation('/ai')} className="flex-1 bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 text-white font-bold py-2.5 rounded-lg transition-all text-sm hover:shadow-[0_0_15px_rgba(255,255,255,0.1)]">
                      View AI Analysis
                    </button>
                  </div>

                  <div className="flex justify-between items-center text-[10px] font-bold text-slate-500 uppercase tracking-wider px-2">
                    <span>91% Confidence</span>
                    <span>18% Impact Reduction</span>
                    <span>4 min ETA</span>
                  </div>
                </div>
              </motion.div>

              {/* Right -- Priority Zones Ranking */}
              <motion.div variants={itemVariants} className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.07] rounded-2xl p-5 flex flex-col h-[320px]">
                <h2 className="text-sm font-bold tracking-wide flex items-center gap-2 mb-4 text-slate-200">
                  <Layers size={16} className="text-slate-400" />
                  PRIORITY ZONES
                </h2>
                <div className="flex-1 flex flex-col justify-between gap-2">
                  {[
                    { rank: 1, name: 'Railway Station', score: 94, conf: '97%', severity: 'CRITICAL', color: 'bg-red-500', text: 'text-red-400', bgFade: 'bg-red-500/20' },
                    { rank: 2, name: 'Bus Stand', score: 89, conf: '91%', severity: 'HIGH', color: 'bg-orange-500', text: 'text-orange-400', bgFade: 'bg-orange-500/20' },
                    { rank: 3, name: 'City Center', score: 86, conf: '88%', severity: 'HIGH', color: 'bg-orange-500', text: 'text-orange-400', bgFade: 'bg-orange-500/20' },
                    { rank: 4, name: 'Market Road', score: 82, conf: '85%', severity: 'HIGH', color: 'bg-amber-500', text: 'text-amber-400', bgFade: 'bg-amber-500/20' },
                    { rank: 5, name: 'Hospital Circle', score: 75, conf: '79%', severity: 'MEDIUM', color: 'bg-blue-500', text: 'text-blue-400', bgFade: 'bg-blue-500/20' },
                  ].map((zone, i) => (
                    <div key={i} className="flex items-center gap-3 p-2 rounded-lg bg-white/[0.02] border border-white/[0.05] hover:bg-white/[0.04] transition-colors">
                      <div className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold text-white ${zone.color} shadow-lg`}>{zone.rank}</div>
                      <div className="flex-1">
                        <div className="flex justify-between items-center mb-1">
                          <span className="text-xs font-bold text-slate-200">{zone.name} <span className="text-[9px] text-slate-500 font-normal ml-1">{zone.conf}</span></span>
                          <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${zone.bgFade} ${zone.text}`}>{zone.severity}</span>
                        </div>
                        <div className="h-1 w-full bg-white/10 rounded-full overflow-hidden">
                          <motion.div 
                            initial={{ width: 0 }}
                            animate={mapAnimate ? { width: `${zone.score}%` } : {}}
                            transition={{ duration: 1, delay: i * 0.1 }}
                            className={`h-full ${zone.color} rounded-full`}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
              
            </div>

            {/* BOTTOM MINI CHARTS ROW */}
            <motion.div variants={itemVariants} className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.07] rounded-2xl p-5 flex flex-col">
              <h2 className="text-sm font-bold tracking-wide flex items-center gap-2 mb-4 text-slate-200">
                <BarChart2 size={16} className="text-slate-400" />
                LIVE INTELLIGENCE FEED
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 h-[140px]">
                {/* Chart 1 */}
                <div className="flex flex-col relative">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest absolute top-0 left-0 z-10">Violations per Hour</span>
                  <div className="flex-1 pt-6">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={violationData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                        <XAxis dataKey="time" stroke="#64748b" fontSize={10} tickLine={false} axisLine={false} />
                        <RechartsTooltip cursor={{ fill: 'rgba(255,255,255,0.05)' }} contentStyle={{ backgroundColor: '#0f172a', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '8px', color: '#fff', fontSize: '12px' }} />
                        <Bar dataKey="value" fill="#3B82F6" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Chart 2 */}
                <div className="flex flex-col relative border-l border-white/[0.05] pl-6">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest absolute top-0 left-6 z-10">Congestion Score</span>
                  <div className="flex-1 pt-6">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={congestionData}>
                        <defs>
                          <linearGradient id="colorCongestion" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#F97316" stopOpacity={0.3}/>
                            <stop offset="95%" stopColor="#F97316" stopOpacity={0}/>
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                        <XAxis dataKey="time" stroke="#64748b" fontSize={10} tickLine={false} axisLine={false} />
                        <RechartsTooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '8px', color: '#fff', fontSize: '12px' }} />
                        <Area type="monotone" dataKey="value" stroke="#F97316" strokeWidth={2} fillOpacity={1} fill="url(#colorCongestion)" />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Chart 3 */}
                <div className="flex flex-col relative border-l border-white/[0.05] pl-6">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest absolute top-0 left-6 z-10">Response Time (min)</span>
                  <div className="flex-1 pt-6">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={responseTimeData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                        <XAxis dataKey="time" stroke="#64748b" fontSize={10} tickLine={false} axisLine={false} />
                        <RechartsTooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '8px', color: '#fff', fontSize: '12px' }} />
                        <Line type="monotone" dataKey="value" stroke="#22C55E" strokeWidth={2} dot={{ r: 3, fill: "#22C55E", strokeWidth: 0 }} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>
            </motion.div>

          </motion.div>
        </main>
      </div>
    </div>
  );
}
