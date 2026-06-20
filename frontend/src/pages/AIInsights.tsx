import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Globe, LayoutDashboard, AlertTriangle, BarChart2, Camera as CameraIcon, Settings, Radio, BrainCircuit,
  Search, Bell, TrendingUp, ChevronLeft, ChevronRight,
  MapPin, Target, AlertOctagon, CheckCircle, Zap, Shield, Lightbulb, Clock, TrendingDown
} from 'lucide-react';
import { useLocation } from 'wouter';
import { FloatingLights } from '@/components/CinematicBackground';
import { useSummary, useTrends, usePriorityQueue, useRadarData, useFactorWeights, useAnalyticsInsights } from '@/lib/hooks';
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
  LineChart, Line, RadarChart, PolarGrid, PolarAngleAxis, Radar, Legend
} from 'recharts';

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



export default function AIInsights() {
  const [collapsed, setCollapsed] = useState(false);
  const [, setLocation] = useLocation();
  const { data: summary } = useSummary();
  const { data: trends } = useTrends(24);
  const { data: priorityZones } = usePriorityQueue(1);
  const { data: radarResponse } = useRadarData();
  const { data: factorWeights } = useFactorWeights();
  const { data: insights } = useAnalyticsInsights();

  const radarChartData = radarResponse ? radarResponse.factors.map(factor => {
    const entry: Record<string, string | number> = { factor };
    radarResponse.zones.forEach(zone => {
      entry[zone.zone_name] = zone.factors[factor] ?? 50;
    });
    return entry;
  }) : [];

  const factorWeightsList = factorWeights?.weights ? Object.entries(factorWeights.weights).map(([name, pct], i) => ({
    name,
    value: `—`,
    weight: `${pct}%`,
    pct,
    color: ['bg-blue-500', 'bg-orange-500', 'bg-amber-500', 'bg-red-500', 'bg-cyan-500'][i % 5],
  })) : [
    { name: 'Violation Count', value: '—', weight: '35%', pct: 35, color: 'bg-blue-500' },
    { name: 'Traffic Speed Reduction', value: '—', weight: '25%', pct: 25, color: 'bg-orange-500' },
    { name: 'Rush Hour Factor', value: '—', weight: '15%', pct: 15, color: 'bg-amber-500' },
    { name: 'Historical Pattern', value: '—', weight: '15%', pct: 15, color: 'bg-red-500' },
    { name: 'Weather Impact', value: '—', weight: '10%', pct: 10, color: 'bg-cyan-500' },
  ];

  const insightTexts = insights ?? [
    'Railway Station congestion increased 12% this week.',
    'Peak traffic occurs between 5 PM and 7 PM.',
    'Bus Stand has the highest violation frequency.',
    'Average officer response improved by 18%.',
  ];

  const scoreTimelineData = trends?.trends?.slice(-10).map((t, i) => ({
    time: new Date(t.date).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
    score: t.count,
  })) ?? [];

  const topZone = priorityZones?.[0];
  const topZoneName = topZone?.zone_name ?? 'Railway Station';
  const topZoneScore = topZone?.average_impact ?? 94;

  const [mountAnimate, setMountAnimate] = useState(false);
  useEffect(() => {
    const t = setTimeout(() => setMountAnimate(true), 100);
    return () => clearTimeout(t);
  }, []);

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

  const circ = 2 * Math.PI * 54;
  const targetOffset = circ * (1 - topZoneScore / 100);
  
  const circSmall = 2 * Math.PI * 44;
  const targetOffsetSmall = circSmall * (1 - Math.min(topZoneScore + 2, 100) / 100);

  return (
    <div className="h-screen w-full bg-[#0B1120] text-white flex overflow-hidden font-sans">
      <FloatingLights />
      
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
            { icon: Globe, label: 'Command', active: false, path: '/command' },
            { icon: LayoutDashboard, label: 'Dashboard', active: false, path: '/dashboard' },
            { icon: AlertTriangle, label: 'Alerts', active: false, path: '/alerts' },
            { icon: BarChart2, label: 'Analytics', active: false, path: '/analytics' },
            { icon: CameraIcon, label: 'Cameras', active: false, path: '/cameras' },
            { icon: Radio, label: 'Dispatch', active: false, path: '/dispatch' },
            { icon: BrainCircuit, label: 'AI Insights', active: true, path: '/ai' },
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
            <div className="relative w-72 group">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 w-4 h-4 group-focus-within:text-blue-400 transition-colors" />
              <input 
                type="text" 
                placeholder="Search zones, cameras..." 
                className="w-full bg-white/[0.04] border border-white/[0.08] rounded-full py-1.5 pl-10 pr-4 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500/50 focus:bg-white/[0.06] transition-all"
              />
            </div>
          </div>
          
          <div className="flex items-center gap-6">
            <LiveClock />
            
            <div className="flex items-center gap-2 bg-green-500/10 border border-green-500/20 rounded-full px-3 py-1">
              <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse shadow-[0_0_8px_rgba(34,197,94,0.8)]" />
              <span className="text-xs font-semibold text-green-400 tracking-wide uppercase">System Online</span>
            </div>
            
            <button className="relative p-2 text-slate-400 hover:text-white transition-colors">
              <Bell size={20} />
              <span className="absolute top-1.5 right-1.5 w-4 h-4 bg-red-500 rounded-full text-[9px] font-bold flex items-center justify-center text-white border-2 border-[#0B1120]">
                3
              </span>
            </button>
            
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center text-xs font-bold shadow-[0_0_15px_rgba(59,130,246,0.4)] border border-white/10 cursor-pointer">
              AK
            </div>
          </div>
        </header>

        {/* Scrollable Content */}
        <main className="flex-1 overflow-y-auto mt-14 p-6 custom-scrollbar">
          <motion.div 
            variants={containerVariants}
            initial="hidden"
            animate="show"
            className="max-w-7xl mx-auto space-y-6 pb-20"
          >
            {/* Page Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
              <div>
                <h1 className="text-4xl font-bold tracking-wider mb-2 text-blue-400 drop-shadow-[0_0_15px_rgba(59,130,246,0.6)]" style={{ fontFamily: "'Orbitron', sans-serif" }}>
                  Explainable AI
                </h1>
                <p className="text-slate-400 text-sm font-medium">Understand why ParkSight prioritizes congestion hotspots.</p>
              </div>
              <div className="flex items-center gap-2 bg-white/5 border border-white/10 px-4 py-2 rounded-xl shadow-[inset_0_2px_10px_rgba(0,0,0,0.2)]">
                <div className="w-2.5 h-2.5 rounded-full bg-green-500 animate-pulse shadow-[0_0_10px_rgba(34,197,94,0.8)]" />
                <span className="text-sm font-bold text-green-400 tracking-wide">● AI Engine Active</span>
              </div>
            </div>

            {/* KPI Cards Row */}
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
              {[
                { title: 'Current Priority Zone', value: topZoneName, icon: MapPin, color: 'text-purple-400', bg: 'bg-purple-500/10', trend: `Score ${topZoneScore}` },
                { title: 'AI Confidence', value: `${Math.round(topZoneScore)}%`, icon: Target, color: 'text-blue-400', bg: 'bg-blue-500/10', trend: 'From congestion model' },
                { title: 'Critical Zones', value: `${priorityZones?.filter(z => z.average_impact > 70).length ?? 0}`, icon: AlertOctagon, color: 'text-red-400', bg: 'bg-red-500/10', trend: 'Requires attention' },
                { title: 'Total Violations', value: `${summary?.total_violations ?? 0}`, icon: TrendingUp, color: 'text-orange-400', bg: 'bg-orange-500/10', trend: 'This period' },
                { title: 'Resolution Rate', value: `${summary?.resolution_rate ?? 91}%`, icon: CheckCircle, color: 'text-emerald-400', bg: 'bg-emerald-500/10', trend: `↑ ${summary?.resolution_rate ? '1.2%' : '—'}` },
              ].map((stat, i) => (
                <motion.div 
                  key={i} 
                  variants={itemVariants}
                  className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.07] rounded-2xl p-4 flex flex-col hover:-translate-y-1 hover:border-white/20 transition-all duration-300 relative overflow-hidden"
                >
                  <div className="flex justify-between items-start mb-2">
                    <div className={`p-2 rounded-xl ${stat.bg}`}>
                      <stat.icon size={18} className={stat.color} />
                    </div>
                  </div>
                  <div className="mt-1 relative z-10">
                    <h3 className="text-slate-400 text-[11px] font-bold uppercase tracking-wider">{stat.title}</h3>
                    <p className="text-xl font-black tracking-tight text-white drop-shadow-md mt-1 mb-2">
                      {stat.value}
                    </p>
                    <span className="text-[10px] font-semibold text-slate-400 bg-white/5 px-2 py-0.5 rounded-md whitespace-nowrap">{stat.trend}</span>
                  </div>
                </motion.div>
              ))}
            </div>

            {/* Main Priority Zone Analysis Card */}
            <motion.div variants={itemVariants} className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.07] rounded-2xl overflow-hidden shadow-[0_0_30px_rgba(0,0,0,0.5)]">
              <div className="grid grid-cols-1 md:grid-cols-2">
                {/* Left side */}
                <div className="p-8 border-b md:border-b-0 md:border-r border-white/[0.07] flex flex-col items-center justify-center text-center relative overflow-hidden">
                  <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 to-transparent pointer-events-none" />
                  <div className="relative z-10 flex flex-col items-center w-full">
                    <h2 className="text-sm font-bold tracking-wide flex items-center gap-2 mb-6 text-slate-200">
                      <Zap size={16} className="text-purple-400" />
                      PRIORITY ZONE ANALYSIS
                    </h2>
                    
                    <h3 className="text-3xl font-black tracking-widest text-white drop-shadow-[0_0_15px_rgba(239,68,68,0.5)] mb-3" style={{ fontFamily: "'Orbitron', sans-serif" }}>
                      {topZoneName}
                    </h3>
                    
                    <div className="bg-red-500/10 border border-red-500/30 rounded-full px-4 py-1 mb-8 shadow-[0_0_15px_rgba(239,68,68,0.2)]">
                      <span className="text-xs font-bold text-red-400 tracking-widest">#1 PRIORITY</span>
                    </div>

                    <div className="relative w-[140px] h-[140px] flex items-center justify-center">
                      <svg width="140" height="140" viewBox="0 0 140 140" className="absolute inset-0 drop-shadow-[0_0_10px_rgba(239,68,68,0.4)]">
                        <circle cx="70" cy="70" r="54" fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="8" />
                        <motion.circle 
                          cx="70" cy="70" r="54" fill="none" stroke="#EF4444" strokeWidth="8"
                          strokeLinecap="round" transform="rotate(-90 70 70)"
                          strokeDasharray={circ}
                          initial={{ strokeDashoffset: circ }}
                          animate={{ strokeDashoffset: mountAnimate ? targetOffset : circ }}
                          transition={{ duration: 1.5, ease: "easeOut" }}
                        />
                      </svg>
                      <div className="flex flex-col items-center justify-center">
                        <span className="text-4xl font-black text-white">{Math.round(topZoneScore)}</span>
                        <span className="text-[10px] font-bold text-slate-400 tracking-wider">SCORE</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Right side */}
                <div className="p-8 relative">
                  <h2 className="text-sm font-bold tracking-wide mb-1 text-slate-200">FACTOR ANALYSIS</h2>
                  <p className="text-xs font-medium text-slate-400 mb-6">What drives this score?</p>
                  
                  <div className="space-y-5">
                    {[
                      { name: 'Violation Count', value: '38 violations', weight: '35%', pct: 35, color: 'bg-blue-500' },
                      { name: 'Traffic Speed Reduction', value: '22% slower', weight: '25%', pct: 25, color: 'bg-orange-500' },
                      { name: 'Rush Hour Factor', value: 'High', weight: '15%', pct: 15, color: 'bg-amber-500' },
                      { name: 'Historical Pattern', value: 'Severe', weight: '15%', pct: 15, color: 'bg-red-500' },
                      { name: 'Weather Impact', value: 'Medium', weight: '10%', pct: 10, color: 'bg-cyan-500' }
                    ].map((factor, i) => (
                      <div key={i} className="space-y-1.5">
                        <div className="flex justify-between items-center text-xs">
                          <span className="font-semibold text-slate-300">
                            {factor.name} <span className="text-slate-500 font-normal ml-1">| {factor.value}</span>
                          </span>
                          <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-white/5 border border-white/10 text-slate-300">
                            Weight {factor.weight}
                          </span>
                        </div>
                        <div className="h-2 w-full rounded-full overflow-hidden bg-white/5">
                          <motion.div 
                            initial={{ width: 0 }}
                            animate={{ width: mountAnimate ? `${factor.pct}%` : 0 }}
                            transition={{ duration: 1, delay: 0.2 + i * 0.1 }}
                            className={`h-full ${factor.color} rounded-full shadow-[0_0_10px_rgba(255,255,255,0.2)]`} 
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </motion.div>

            {/* Second Row */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              
              {/* Confidence Panel */}
              <motion.div variants={itemVariants} className="bg-white/[0.04] backdrop-blur-xl border border-blue-500/20 rounded-2xl p-6 shadow-[inset_0_0_30px_rgba(59,130,246,0.05)] relative overflow-hidden flex flex-col">
                <div className="absolute -top-20 -right-20 w-40 h-40 bg-blue-500/10 blur-[50px] rounded-full pointer-events-none" />
                <h2 className="text-sm font-bold tracking-wide flex items-center gap-2 mb-6 text-slate-200">
                  <Shield size={16} className="text-blue-400" />
                  AI CONFIDENCE
                </h2>
                
                <div className="flex-1 flex flex-col items-center justify-center">
                  <div className="relative w-[100px] h-[100px] flex items-center justify-center mb-4">
                    <svg width="100" height="100" viewBox="0 0 100 100" className="absolute inset-0 drop-shadow-[0_0_8px_rgba(59,130,246,0.4)]">
                      <circle cx="50" cy="50" r="44" fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="6" />
                      <motion.circle 
                        cx="50" cy="50" r="44" fill="none" stroke="#3B82F6" strokeWidth="6"
                        strokeLinecap="round" transform="rotate(-90 50 50)"
                        strokeDasharray={circSmall}
                        initial={{ strokeDashoffset: circSmall }}
                        animate={{ strokeDashoffset: mountAnimate ? targetOffsetSmall : circSmall }}
                        transition={{ duration: 1.5, ease: "easeOut" }}
                      />
                    </svg>
                    <span className="text-2xl font-black text-white">94%</span>
                  </div>
                  <h3 className="text-sm font-bold text-green-400 tracking-wider mb-2">HIGH CONFIDENCE</h3>
                  <div className="bg-green-500/10 border border-green-500/20 text-green-400 text-[11px] font-semibold px-3 py-1.5 rounded-lg text-center leading-snug mb-3">
                    HIGH CONFIDENCE — Recommendation can be trusted
                  </div>
                  <p className="text-[10px] text-slate-500 font-medium">Based on 847 historical data points</p>
                </div>
              </motion.div>

              {/* AI Recommendation Panel */}
              <motion.div variants={itemVariants} className="bg-white/[0.04] backdrop-blur-xl border border-amber-500/20 rounded-2xl p-6 shadow-[inset_0_0_30px_rgba(245,158,11,0.05)] relative overflow-hidden flex flex-col">
                <div className="absolute -top-20 -right-20 w-40 h-40 bg-amber-500/10 blur-[50px] rounded-full pointer-events-none" />
                <h2 className="text-sm font-bold tracking-wide flex items-center gap-2 mb-6 text-slate-200">
                  <Lightbulb size={16} className="text-amber-400" />
                  AI RECOMMENDATION
                </h2>
                
                <div className="flex-1 flex flex-col">
                  <p className="text-lg font-medium text-white italic leading-relaxed mb-6">
                    "Deploy 2 officers immediately to Railway Station to prevent congestion spillover into adjacent roads."
                  </p>
                  
                  <div className="space-y-3 mb-6">
                    <div className="flex items-center gap-3 bg-white/5 p-3 rounded-xl border border-white/5">
                      <div className="p-1.5 rounded-lg bg-green-500/10 text-green-400"><TrendingDown size={16} /></div>
                      <div>
                        <p className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Estimated Impact Reduction</p>
                        <p className="text-sm font-bold text-white">18%</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 bg-white/5 p-3 rounded-xl border border-white/5">
                      <div className="p-1.5 rounded-lg bg-blue-500/10 text-blue-400"><Clock size={16} /></div>
                      <div>
                        <p className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Expected Response Time</p>
                        <p className="text-sm font-bold text-white">4 minutes</p>
                      </div>
                    </div>
                  </div>
                  
                  <button data-testid="btn-dispatch-now" className="w-full mt-auto bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold py-3 px-4 rounded-xl shadow-[0_0_15px_rgba(59,130,246,0.4)] transition-all">
                    Dispatch Now
                  </button>
                </div>
              </motion.div>

              {/* Zone Comparison Leaderboard */}
              <motion.div variants={itemVariants} className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.07] rounded-2xl p-6 flex flex-col">
                <h2 className="text-sm font-bold tracking-wide mb-6 text-slate-200">ZONE PRIORITY RANKING</h2>
                
                <div className="flex-1 flex flex-col justify-center space-y-5">
                  {[
                    { rank: '#1', name: 'Railway Station', score: 94, color: 'bg-red-500', barColor: 'bg-red-500/20' },
                    { rank: '#2', name: 'Bus Stand', score: 89, color: 'bg-orange-500', barColor: 'bg-orange-500/20' },
                    { rank: '#3', name: 'City Center', score: 86, color: 'bg-amber-500', barColor: 'bg-amber-500/20' },
                    { rank: '#4', name: 'Market Road', score: 82, color: 'bg-yellow-500', barColor: 'bg-yellow-500/20' }
                  ].map((zone, i) => (
                    <div key={i} className="space-y-1.5">
                      <div className="flex justify-between items-center text-xs">
                        <span className="font-semibold text-slate-300">
                          <span className="text-slate-500 mr-2">{zone.rank}</span>{zone.name}
                        </span>
                        <span className={`font-bold px-1.5 py-0.5 rounded text-[10px] ${zone.color} text-white`}>
                          {zone.score}
                        </span>
                      </div>
                      <div className={`h-1.5 w-full rounded-full overflow-hidden ${zone.barColor}`}>
                        <motion.div 
                          initial={{ width: 0 }}
                          animate={{ width: mountAnimate ? `${zone.score}%` : 0 }}
                          transition={{ duration: 1, delay: i * 0.1 }}
                          className={`h-full ${zone.color} rounded-full`} 
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
              
            </div>

            {/* Third Row: Score Timeline Chart */}
            <motion.div variants={itemVariants} className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.07] rounded-2xl p-6 h-[320px] flex flex-col relative">
              <h2 className="text-sm font-bold tracking-wide text-slate-200 mb-6">PRIORITY SCORE EVOLUTION — TODAY</h2>
              
              <div className="absolute top-12 right-10 z-10 bg-red-500/10 border border-red-500/30 text-red-400 px-3 py-1 rounded-lg text-xs font-bold tracking-wider shadow-[0_0_15px_rgba(239,68,68,0.2)]">
                CRITICAL
              </div>

              <div className="flex-1 w-full relative">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={scoreTimelineData} margin={{ top: 20, right: 30, left: -20, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#EF4444" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#EF4444" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                    <XAxis dataKey="time" stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                    <YAxis stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} domain={[50, 100]} />
                    <RechartsTooltip 
                      contentStyle={{ backgroundColor: 'rgba(15, 23, 42, 0.9)', backdropFilter: 'blur(12px)', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '12px', color: '#fff' }}
                      itemStyle={{ color: '#EF4444', fontWeight: 'bold' }}
                    />
                    <Line type="monotone" dataKey="score" stroke="#EF4444" strokeWidth={3} dot={{ fill: '#EF4444', r: 6, strokeWidth: 2, stroke: '#0B1120' }} activeDot={{ r: 8, strokeWidth: 0 }} />
                    <Area type="monotone" dataKey="score" fill="url(#colorScore)" stroke="none" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </motion.div>

            {/* Bottom Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              {/* Why Not Bus Stand? */}
              <motion.div variants={itemVariants} className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.07] rounded-2xl p-6">
                <h2 className="text-sm font-bold tracking-wide text-slate-200 mb-6">COMPARATIVE ANALYSIS — RAILWAY STATION VS BUS STAND</h2>
                <div className="space-y-6">
                  {[
                    { factor: 'Violation Count', rVal: '38', bVal: '31', rPct: 94, bPct: 78 },
                    { factor: 'Speed Reduction', rVal: '22%', bVal: '15%', rPct: 88, bPct: 60 },
                    { factor: 'Rush Hour', rVal: 'High', bVal: 'Medium', rPct: 85, bPct: 60 },
                    { factor: 'Historical Pattern', rVal: 'Severe', bVal: 'High', rPct: 90, bPct: 75 },
                    { factor: 'Weather Impact', rVal: 'Medium', bVal: 'Low', rPct: 50, bPct: 30 }
                  ].map((row, i) => (
                    <div key={i} className="grid grid-cols-12 gap-4 items-center">
                      <div className="col-span-4 text-xs font-semibold text-slate-300">{row.factor}</div>
                      <div className="col-span-8 flex flex-col gap-2">
                        {/* Railway */}
                        <div className="flex items-center gap-2">
                          <div className="w-10 text-right text-[10px] font-bold text-red-400">{row.rVal}</div>
                          <div className="flex-1 h-1.5 bg-white/5 rounded-full overflow-hidden">
                            <motion.div initial={{ width: 0 }} animate={{ width: mountAnimate ? `${row.rPct}%` : 0 }} transition={{ duration: 1 }} className="h-full bg-red-500 rounded-full" />
                          </div>
                        </div>
                        {/* Bus Stand */}
                        <div className="flex items-center gap-2">
                          <div className="w-10 text-right text-[10px] font-bold text-blue-400">{row.bVal}</div>
                          <div className="flex-1 h-1.5 bg-white/5 rounded-full overflow-hidden">
                            <motion.div initial={{ width: 0 }} animate={{ width: mountAnimate ? `${row.bPct}%` : 0 }} transition={{ duration: 1 }} className="h-full bg-blue-500 rounded-full" />
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>

              {/* Radar Chart Comparison */}
              <motion.div variants={itemVariants} className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.07] rounded-2xl p-6 flex flex-col min-h-[350px]">
                <h2 className="text-sm font-bold tracking-wide text-slate-200 mb-2">FACTOR RADAR — ZONE COMPARISON</h2>
                <div className="flex-1 w-full relative min-h-[250px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarChartData}>
                      <PolarGrid stroke="rgba(255,255,255,0.1)" />
                      <PolarAngleAxis dataKey="factor" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                      {(radarResponse?.zones ?? []).map((zone, i) => {
                        const colors = ['#EF4444', '#3B82F6', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899'];
                        const c = colors[i % colors.length];
                        return <Radar key={zone.zone_id} name={zone.zone_name} dataKey={zone.zone_name} stroke={c} fill={c} fillOpacity={0.3 - i * 0.05} />;
                      })}
                      <Legend wrapperStyle={{ fontSize: '12px', color: '#cbd5e1' }} />
                      <RechartsTooltip 
                        contentStyle={{ backgroundColor: 'rgba(15, 23, 42, 0.9)', backdropFilter: 'blur(12px)', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '12px', color: '#fff' }}
                      />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>
              </motion.div>

            </div>

          </motion.div>
        </main>
      </div>
    </div>
  );
}
