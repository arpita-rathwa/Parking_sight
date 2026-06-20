import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Globe, LayoutDashboard, AlertTriangle, BarChart2, Camera as CameraIcon, Settings, Radio, BrainCircuit,
  Search, Bell, Users, UserCheck, Navigation, MapPin, Clock, CheckCircle, 
  AlertOctagon, ChevronLeft, ChevronRight, UserPlus, Route as RouteIcon, RefreshCw,
  ClipboardList, Activity
} from 'lucide-react';
import { useLocation } from 'wouter';
import { FloatingLights } from '@/components/CinematicBackground';
import { useSummary, usePriorityQueue, useDispatchOverview } from '@/lib/hooks';

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

const ICON_MAP: Record<string, React.ComponentType<{ size?: number; className?: string }>> = {
  dispatch: Navigation,
  map: MapPin,
  check: CheckCircle,
};

const COLOR_CLASSES: Record<string, { bg: string; text: string; border: string; bgLight: string; borderLight: string }> = {
  green: { bg: 'bg-green-500/20', text: 'text-green-400', border: 'border-green-500/30', bgLight: 'bg-green-500/10', borderLight: 'border-green-500/20' },
  blue: { bg: 'bg-blue-500/20', text: 'text-blue-400', border: 'border-blue-500/30', bgLight: 'bg-blue-500/10', borderLight: 'border-blue-500/20' },
  orange: { bg: 'bg-orange-500/20', text: 'text-orange-400', border: 'border-orange-500/30', bgLight: 'bg-orange-500/10', borderLight: 'border-orange-500/20' },
  purple: { bg: 'bg-purple-500/20', text: 'text-purple-400', border: 'border-purple-500/30', bgLight: 'bg-purple-500/10', borderLight: 'border-purple-500/20' },
};

export default function Dispatch() {
  const [collapsed, setCollapsed] = useState(false);
  const [, setLocation] = useLocation();
  const { data: summary } = useSummary();
  const { data: priorityZones } = usePriorityQueue(5);
  const { data: dispatch } = useDispatchOverview();

  const officerData = dispatch?.officers ?? [];
  const assignmentsData = dispatch?.assignments ?? [];
  const timelineData = dispatch?.timeline?.map(t => ({
    time: t.time,
    icon: ICON_MAP[t.icon] || Navigation,
    color: 'text-blue-400',
    bg: 'bg-blue-500/20',
    text: t.text,
  })) ?? [];

  const highPriorityZones = priorityZones?.slice(0, 5).map(z => ({
    name: z.zone_name,
    score: z.average_impact,
    color: z.average_impact >= 70 ? 'bg-red-500' : z.average_impact >= 50 ? 'bg-orange-500' : 'bg-amber-500',
    barColor: z.average_impact >= 70 ? 'bg-red-500/20' : z.average_impact >= 50 ? 'bg-orange-500/20' : 'bg-amber-500/20',
    label: z.recommendation === 'IMMEDIATE' ? 'Critical' : z.recommendation === 'HIGH' ? 'High' : 'Medium',
    labelColor: z.average_impact >= 70 ? 'text-red-400' : z.average_impact >= 50 ? 'text-orange-400' : 'text-amber-400',
  })) ?? [];

  const availableCount = officerData.filter(o => o.status === 'Available').length;
  const enRouteCount = officerData.filter(o => o.status === 'En Route').length;
  const onSceneCount = officerData.filter(o => o.status === 'On Scene').length;

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

  const [zonesAnim, setZonesAnim] = useState(false);
  useEffect(() => {
    const t = setTimeout(() => setZonesAnim(true), 500);
    return () => clearTimeout(t);
  }, []);

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
            { icon: Radio, label: 'Dispatch', active: true, path: '/dispatch' },
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
                  Officer Dispatch Center
                </h1>
                <p className="text-slate-400 text-sm font-medium">Coordinate and monitor field officers responding to parking violations.</p>
              </div>
              <div className="flex items-center gap-2 bg-white/5 border border-white/10 px-4 py-2 rounded-xl shadow-[inset_0_2px_10px_rgba(0,0,0,0.2)]">
                <div className="w-2.5 h-2.5 rounded-full bg-green-500 animate-pulse shadow-[0_0_10px_rgba(34,197,94,0.8)]" />
                <span className="text-sm font-bold text-green-400 tracking-wide">● {officerData.length} Officers Active</span>
              </div>
            </div>

            {/* KPI Cards Row */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
              {[
                { title: 'Active Officers', value: officerData.length, icon: Users, color: 'text-blue-400', bg: 'bg-blue-500/10', trend: 'All shifts covered' },
                { title: 'Available Officers', value: availableCount, icon: UserCheck, color: 'text-green-400', bg: 'bg-green-500/10', trend: 'Ready to dispatch' },
                { title: 'En Route', value: enRouteCount, icon: Navigation, color: 'text-cyan-400', bg: 'bg-cyan-500/10', trend: `${assignmentsData.filter(a => a.status === 'EN ROUTE').length} active assignments` },
                { title: 'On Scene', value: onSceneCount, icon: MapPin, color: 'text-orange-400', bg: 'bg-orange-500/10', trend: 'Handling violations' },
                { title: 'Avg Response Time', value: summary?.avg_response_time_min ?? 0, icon: Clock, color: 'text-purple-400', bg: 'bg-purple-500/10', trend: '↓ 0.3 min improved', isFloat: true },
                { title: 'Resolved Today', value: summary?.total_violations ?? 0, icon: CheckCircle, color: 'text-emerald-400', bg: 'bg-emerald-500/10', trend: 'This period' },
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
                    <span className="text-[10px] font-semibold text-slate-400 bg-white/5 px-2 py-0.5 rounded-md whitespace-nowrap">{stat.trend}</span>
                  </div>
                  <div className="mt-2 relative z-10">
                    <p className="text-3xl font-black tracking-tight text-white drop-shadow-md">
                      <AnimatedCounter value={stat.value} />
                      {stat.isFloat && <span className="text-sm font-medium text-slate-500 ml-1">min</span>}
                    </p>
                    <h3 className="text-slate-400 text-[11px] font-bold uppercase tracking-wider mt-1">{stat.title}</h3>
                  </div>
                </motion.div>
              ))}
            </div>

            {/* Three-Column Layout */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              
              {/* Left Column (25%) - High Priority Zones & Quick Actions */}
              <motion.div variants={itemVariants} className="lg:col-span-3 flex flex-col gap-6">
                <div className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.07] rounded-2xl p-5 hover:border-white/10 transition-colors flex flex-col">
                  <h2 className="text-sm font-bold tracking-wide flex items-center gap-2 mb-4 text-slate-200">
                    <AlertOctagon size={16} className="text-red-400" />
                    HIGH PRIORITY ZONES
                  </h2>
                  <div className="space-y-4">
                    {highPriorityZones.map((zone, i) => (
                      <div key={i} className="space-y-1.5">
                        <div className="flex justify-between items-center text-xs">
                          <span className="font-medium text-slate-300 flex items-center gap-2">
                            <span className={`w-4 h-4 rounded-full flex items-center justify-center text-[9px] font-bold text-white ${zone.color}`}>{i+1}</span>
                            {zone.name}
                          </span>
                          <span className={`font-bold px-1.5 py-0.5 rounded text-[10px] bg-white/5 border border-white/10 ${zone.labelColor}`}>{zone.label}</span>
                        </div>
                        <div className={`h-1.5 w-full rounded-full overflow-hidden ${zone.barColor}`}>
                          <motion.div 
                            initial={{ width: 0 }}
                            animate={zonesAnim ? { width: `${zone.score}%` } : {}}
                            transition={{ duration: 1, delay: i * 0.1 }}
                            className={`h-full ${zone.color} rounded-full`} 
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.07] rounded-2xl p-5 hover:border-white/10 transition-colors flex flex-col">
                  <h2 className="text-sm font-bold tracking-wide flex items-center gap-2 mb-4 text-slate-200">
                    <Activity size={16} className="text-blue-400" />
                    QUICK ACTIONS
                  </h2>
                  <div className="space-y-3">
                    <button className="w-full bg-white/[0.04] border border-white/[0.08] rounded-xl px-4 py-3 flex items-center gap-3 hover:bg-white/[0.08] hover:border-blue-500/40 transition-all text-left group" data-testid="btn-assign">
                      <UserPlus size={18} className="text-blue-400 group-hover:drop-shadow-[0_0_8px_rgba(96,165,250,0.8)]" />
                      <span className="text-sm font-semibold text-slate-200 group-hover:text-white">Assign Officer</span>
                    </button>
                    <button className="w-full bg-white/[0.04] border border-white/[0.08] rounded-xl px-4 py-3 flex items-center gap-3 hover:bg-white/[0.08] hover:border-cyan-500/40 transition-all text-left group" data-testid="btn-route">
                      <RouteIcon size={18} className="text-cyan-400 group-hover:drop-shadow-[0_0_8px_rgba(34,211,238,0.8)]" />
                      <span className="text-sm font-semibold text-slate-200 group-hover:text-white">View Route</span>
                    </button>
                    <button className="w-full bg-white/[0.04] border border-white/[0.08] rounded-xl px-4 py-3 flex items-center gap-3 hover:bg-white/[0.08] hover:border-purple-500/40 transition-all text-left group" data-testid="btn-reassign">
                      <RefreshCw size={18} className="text-purple-400 group-hover:drop-shadow-[0_0_8px_rgba(192,132,252,0.8)]" />
                      <span className="text-sm font-semibold text-slate-200 group-hover:text-white">Reassign Zone</span>
                    </button>
                    <button className="w-full bg-white/[0.04] border border-white/[0.08] rounded-xl px-4 py-3 flex items-center gap-3 hover:bg-white/[0.08] hover:border-green-500/40 transition-all text-left group" data-testid="btn-resolve">
                      <CheckCircle size={18} className="text-green-400 group-hover:drop-shadow-[0_0_8px_rgba(74,222,128,0.8)]" />
                      <span className="text-sm font-semibold text-slate-200 group-hover:text-white">Mark Resolved</span>
                    </button>
                    <button className="w-full bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3 flex items-center gap-3 hover:bg-red-500/20 hover:border-red-500/50 transition-all text-left group shadow-[0_0_15px_rgba(239,68,68,0.1)] hover:shadow-[0_0_20px_rgba(239,68,68,0.2)] animate-pulse" data-testid="btn-emergency">
                      <AlertOctagon size={18} className="text-red-400 drop-shadow-[0_0_8px_rgba(248,113,113,0.8)]" />
                      <span className="text-sm font-bold text-red-200 group-hover:text-white">Emergency Escalation</span>
                    </button>
                  </div>
                </div>
              </motion.div>

              {/* Center Column (40%) - Live City Map */}
              <motion.div variants={itemVariants} className="lg:col-span-5 bg-white/[0.04] backdrop-blur-xl border border-white/[0.07] rounded-2xl p-5 flex flex-col relative overflow-hidden group hover:border-white/10 transition-colors h-[650px] lg:h-auto">
                <div className="flex justify-between items-center mb-4 relative z-10">
                  <h2 className="text-sm font-bold tracking-wide flex items-center gap-2 text-slate-200">
                    <MapPin size={16} className="text-blue-400" />
                    LIVE CITY MAP — BANGALORE
                  </h2>
                  <div className="flex items-center gap-2">
                    <span className="flex items-center gap-1.5 text-xs font-bold text-green-400 bg-green-500/10 px-2 py-1 rounded-md border border-green-500/20 uppercase tracking-wider">
                      <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
                      Active
                    </span>
                  </div>
                </div>
                
                <div className="flex-1 bg-[#060D1A] rounded-xl border border-white/5 relative overflow-hidden">
                  <div className="absolute inset-0 opacity-[0.05]" style={{ backgroundImage: 'linear-gradient(rgba(255,255,255,1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,1) 1px, transparent 1px)', backgroundSize: '40px 40px' }} />
                  
                  <svg className="absolute inset-0 w-full h-full" viewBox="0 0 800 500" preserveAspectRatio="xMidYMid slice">
                    {/* Roads */}
                    <path d="M 100,0 C 120,200 200,250 400,300 C 600,350 700,400 800,500" fill="none" stroke="#1E293B" strokeWidth="8" />
                    <path d="M 0,250 C 150,270 300,220 400,300 C 450,340 500,500 550,500" fill="none" stroke="#1E293B" strokeWidth="12" />
                    <path d="M 300,0 L 400,300 L 500,0" fill="none" stroke="#1E293B" strokeWidth="6" />
                    <path d="M 600,0 C 580,150 650,250 750,300 L 800,310" fill="none" stroke="#1E293B" strokeWidth="6" />
                    <path d="M 200,500 L 300,350 L 400,300" fill="none" stroke="#1E293B" strokeWidth="6" />
                    
                    {/* Zones */}
                    {/* Railway Station */}
                    <g transform="translate(420, 100)">
                      <circle r="60" fill="#ef4444" opacity="0.1">
                        <animate attributeName="r" values="40;70;40" dur="1.5s" repeatCount="indefinite" />
                        <animate attributeName="opacity" values="0.3;0;0.3" dur="1.5s" repeatCount="indefinite" />
                      </circle>
                      <circle r="30" fill="#ef4444" opacity="0.4" />
                      <circle r="8" fill="#ef4444" className="drop-shadow-[0_0_12px_rgba(239,68,68,1)]" />
                      <text x="18" y="-12" fill="white" fontSize="12" fontWeight="bold">Railway Station</text>
                      <text x="18" y="2" fill="#ef4444" fontSize="10" fontWeight="bold">CRITICAL</text>
                    </g>

                    {/* Bus Stand */}
                    <g transform="translate(180, 240)">
                      <circle r="45" fill="#f97316" opacity="0.1">
                        <animate attributeName="r" values="30;55;30" dur="2s" repeatCount="indefinite" />
                        <animate attributeName="opacity" values="0.2;0;0.2" dur="2s" repeatCount="indefinite" />
                      </circle>
                      <circle r="25" fill="#f97316" opacity="0.3" />
                      <circle r="6" fill="#f97316" />
                      <text x="14" y="-10" fill="white" fontSize="12" fontWeight="bold">Bus Stand</text>
                      <text x="14" y="2" fill="#f97316" fontSize="10" fontWeight="bold">HIGH</text>
                    </g>

                    {/* City Center */}
                    <g transform="translate(400, 300)">
                      <circle r="50" fill="#ef4444" opacity="0.1">
                        <animate attributeName="r" values="35;60;35" dur="1.8s" repeatCount="indefinite" />
                        <animate attributeName="opacity" values="0.2;0;0.2" dur="1.8s" repeatCount="indefinite" />
                      </circle>
                      <circle r="25" fill="#ef4444" opacity="0.3" />
                      <circle r="6" fill="#ef4444" />
                      <text x="16" y="-10" fill="white" fontSize="12" fontWeight="bold">City Center</text>
                      <text x="16" y="2" fill="#ef4444" fontSize="10" fontWeight="bold">CRITICAL</text>
                    </g>

                    {/* Market Road */}
                    <g transform="translate(680, 280)">
                      <circle r="35" fill="#f59e0b" opacity="0.1">
                        <animate attributeName="r" values="20;45;20" dur="2.5s" repeatCount="indefinite" />
                      </circle>
                      <circle r="18" fill="#f59e0b" opacity="0.3" />
                      <circle r="5" fill="#f59e0b" />
                      <text x="12" y="-8" fill="white" fontSize="11" fontWeight="bold">Market Road</text>
                      <text x="12" y="4" fill="#f59e0b" fontSize="9" fontWeight="bold">HIGH</text>
                    </g>

                    {/* Hospital Circle */}
                    <g transform="translate(580, 180)">
                      <circle r="30" fill="#f59e0b" opacity="0.1">
                        <animate attributeName="r" values="15;35;15" dur="3s" repeatCount="indefinite" />
                      </circle>
                      <circle r="15" fill="#f59e0b" opacity="0.2" />
                      <circle r="4" fill="#f59e0b" />
                      <text x="10" y="-6" fill="white" fontSize="10" fontWeight="bold">Hospital Circle</text>
                      <text x="10" y="4" fill="#f59e0b" fontSize="8" fontWeight="bold">MEDIUM</text>
                    </g>

                    {/* Officer Markers */}
                    {/* Available */}
                    <g transform="translate(120, 150)">
                      <circle r="10" fill="#22c55e" opacity="0.2" />
                      <circle r="4" fill="#22c55e" />
                      <text x="10" y="3" fill="#22c55e" fontSize="9" fontWeight="bold">O1</text>
                    </g>
                    <g transform="translate(600, 380)">
                      <circle r="10" fill="#22c55e" opacity="0.2" />
                      <circle r="4" fill="#22c55e" />
                      <text x="10" y="3" fill="#22c55e" fontSize="9" fontWeight="bold">O2</text>
                    </g>

                    {/* On Scene */}
                    <g transform="translate(415, 310)">
                      <circle r="12" fill="#f97316" opacity="0.3" />
                      <circle r="5" fill="#f97316" />
                      <text x="-18" y="4" fill="#f97316" fontSize="9" fontWeight="bold">O6</text>
                    </g>
                    <g transform="translate(410, 95)">
                      <circle r="12" fill="#f97316" opacity="0.3" />
                      <circle r="5" fill="#f97316" />
                      <text x="-18" y="4" fill="#f97316" fontSize="9" fontWeight="bold">O7</text>
                    </g>

                    {/* En Route (Animated) */}
                    <g>
                      <path id="route-o3" d="M 300,50 Q 350,70 410,95" fill="none" stroke="#3b82f6" strokeWidth="2" strokeDasharray="4 4" opacity="0.5" />
                      <g>
                        <animateMotion dur="4s" repeatCount="indefinite" path="M 300,50 Q 350,70 410,95" />
                        <circle r="10" fill="#3b82f6" opacity="0.3" />
                        <circle r="4" fill="#3b82f6" />
                        <text x="8" y="-8" fill="#3b82f6" fontSize="9" fontWeight="bold">O3</text>
                      </g>
                    </g>

                    <g>
                      <path id="route-o4" d="M 550,450 Q 500,400 415,310" fill="none" stroke="#3b82f6" strokeWidth="2" strokeDasharray="4 4" opacity="0.5" />
                      <g>
                        <animateMotion dur="6s" repeatCount="indefinite" path="M 550,450 Q 500,400 415,310" />
                        <circle r="10" fill="#3b82f6" opacity="0.3" />
                        <circle r="4" fill="#3b82f6" />
                        <text x="8" y="12" fill="#3b82f6" fontSize="9" fontWeight="bold">O4</text>
                      </g>
                    </g>

                    <g>
                      <path id="route-o5" d="M 50,350 Q 120,300 170,250" fill="none" stroke="#3b82f6" strokeWidth="2" strokeDasharray="4 4" opacity="0.5" />
                      <g>
                        <animateMotion dur="3s" repeatCount="indefinite" path="M 50,350 Q 120,300 170,250" />
                        <circle r="10" fill="#3b82f6" opacity="0.3" />
                        <circle r="4" fill="#3b82f6" />
                        <text x="-15" y="-8" fill="#3b82f6" fontSize="9" fontWeight="bold">O5</text>
                      </g>
                    </g>
                  </svg>

                  {/* Legend */}
                  <div className="absolute bottom-4 right-4 bg-[#0B1120]/90 backdrop-blur-md border border-white/10 rounded-lg p-3 text-[10px] font-medium text-slate-300 space-y-2">
                    <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-blue-500" /> Officer</div>
                    <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-red-500" /> Critical Zone</div>
                    <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-orange-500" /> High Zone</div>
                    <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-green-500" /> Resolved</div>
                  </div>
                </div>
              </motion.div>

              {/* Right Column (35%) - Officer Status Panel */}
              <motion.div variants={itemVariants} className="lg:col-span-4 bg-white/[0.04] backdrop-blur-xl border border-white/[0.07] rounded-2xl flex flex-col overflow-hidden h-[650px] lg:h-auto">
                <div className="p-5 border-b border-white/[0.08] flex items-center justify-between">
                  <h2 className="text-sm font-bold tracking-wide flex items-center gap-2 text-slate-200">
                    <Radio size={16} className="text-purple-400" />
                    OFFICER STATUS
                  </h2>
                  <span className="text-xs font-semibold text-slate-400">{officerData.length} Active</span>
                </div>
                <div className="flex-1 overflow-y-auto p-3 space-y-3 custom-scrollbar">
                  <AnimatePresence>
                    {officerData.map((officer, i) => {
                      const cc = COLOR_CLASSES[officer.color] || COLOR_CLASSES.green;
                      const initials = officer.name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();
                      return (
                      <motion.div 
                        key={officer.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.05 }}
                        className="bg-white/5 border border-white/5 rounded-xl p-3 flex items-center justify-between hover:bg-white/10 hover:border-white/10 transition-all duration-300 group hover:scale-[1.01]"
                      >
                        <div className="flex items-center gap-3">
                          <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm ${cc.bg} ${cc.text} ${cc.border}`}>
                            {initials}
                          </div>
                          <div>
                            <h4 className="text-sm font-bold text-slate-200">{officer.name}</h4>
                            <p className="text-xs text-slate-400 mt-0.5"><span className="text-slate-500">Zone:</span> {officer.zone}</p>
                          </div>
                        </div>
                        <div className="text-right flex flex-col items-end gap-1.5">
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded border uppercase tracking-wider ${cc.bgLight} ${cc.borderLight} ${cc.text}`}>
                            {officer.status}
                          </span>
                          <span className="text-xs font-semibold text-slate-300"><span className="text-slate-500 font-normal mr-1">{officer.statLabel}:</span>{officer.statVal}</span>
                        </div>
                      </motion.div>
                      );
                    })}
                  </AnimatePresence>
                </div>
              </motion.div>
              
            </div>

            {/* Bottom Section - Tables & Timeline */}
            <div className="grid grid-cols-1 lg:grid-cols-10 gap-6 h-[400px]">
              
              {/* Assignments Table (60%) */}
              <motion.div variants={itemVariants} className="lg:col-span-6 bg-white/[0.04] backdrop-blur-xl border border-white/[0.07] rounded-2xl flex flex-col overflow-hidden">
                <div className="p-5 border-b border-white/[0.08] flex items-center justify-between bg-white/[0.02]">
                  <h2 className="text-sm font-bold tracking-wide flex items-center gap-2 text-slate-200">
                    <ClipboardList size={16} className="text-blue-400" />
                    CURRENT ASSIGNMENTS
                  </h2>
                </div>
                <div className="overflow-x-auto flex-1 custom-scrollbar">
                  <table className="w-full text-left border-collapse">
                    <thead className="sticky top-0 bg-[#0B1120]/90 backdrop-blur-md border-b border-white/[0.08] z-10">
                      <tr>
                        <th className="py-3 px-4 text-[10px] font-bold text-slate-400 uppercase tracking-wider">Officer</th>
                        <th className="py-3 px-4 text-[10px] font-bold text-slate-400 uppercase tracking-wider">Zone</th>
                        <th className="py-3 px-4 text-[10px] font-bold text-slate-400 uppercase tracking-wider">Violation</th>
                        <th className="py-3 px-4 text-[10px] font-bold text-slate-400 uppercase tracking-wider">Priority</th>
                        <th className="py-3 px-4 text-[10px] font-bold text-slate-400 uppercase tracking-wider">ETA</th>
                        <th className="py-3 px-4 text-[10px] font-bold text-slate-400 uppercase tracking-wider">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/[0.04]">
                      {assignmentsData.map((row, i) => {
                        let prioColor = '';
                        if (row.priority === 'CRITICAL') prioColor = 'text-red-400 bg-red-500/10 border-red-500/20';
                        else if (row.priority === 'HIGH') prioColor = 'text-orange-400 bg-orange-500/10 border-orange-500/20';
                        else if (row.priority === 'MEDIUM') prioColor = 'text-amber-400 bg-amber-500/10 border-amber-500/20';
                        else prioColor = 'text-blue-400 bg-blue-500/10 border-blue-500/20';

                        return (
                          <motion.tr 
                            key={i}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.2, delay: i * 0.05 }}
                            className="group hover:bg-blue-500/[0.03] transition-colors"
                          >
                            <td className="py-3 px-4 text-xs font-bold text-slate-200">{row.officer}</td>
                            <td className="py-3 px-4 text-xs text-slate-300">{row.zone}</td>
                            <td className="py-3 px-4 text-xs text-slate-400">{row.violation}</td>
                            <td className="py-3 px-4">
                              <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border uppercase tracking-wider ${prioColor}`}>
                                {row.priority}
                              </span>
                            </td>
                            <td className="py-3 px-4 text-xs font-medium text-slate-300">{row.eta}</td>
                            <td className="py-3 px-4">
                              <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border uppercase tracking-wider ${(COLOR_CLASSES[row.color] || COLOR_CLASSES.green).bgLight} ${(COLOR_CLASSES[row.color] || COLOR_CLASSES.green).borderLight} ${(COLOR_CLASSES[row.color] || COLOR_CLASSES.green).text}`}>
                                {row.status}
                              </span>
                            </td>
                          </motion.tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </motion.div>

              {/* Activity Timeline (40%) */}
              <motion.div variants={itemVariants} className="lg:col-span-4 bg-white/[0.04] backdrop-blur-xl border border-white/[0.07] rounded-2xl flex flex-col overflow-hidden">
                <div className="p-5 border-b border-white/[0.08] flex items-center justify-between bg-white/[0.02]">
                  <h2 className="text-sm font-bold tracking-wide flex items-center gap-2 text-slate-200">
                    <Activity size={16} className="text-emerald-400" />
                    DISPATCH ACTIVITY
                  </h2>
                </div>
                <div className="flex-1 overflow-y-auto p-5 custom-scrollbar relative">
                  <div className="absolute left-[35px] top-6 bottom-6 w-px bg-white/10" />
                  <div className="space-y-6">
                    {timelineData.map((item, i) => (
                      <motion.div 
                        key={i}
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: i * 0.1 + 0.3 }}
                        className="relative flex items-start gap-4 z-10"
                      >
                        <div className={`mt-0.5 shrink-0 w-8 h-8 rounded-full flex items-center justify-center border border-white/10 shadow-lg ${item.bg}`}>
                          <item.icon size={14} className={item.color} />
                        </div>
                        <div className="pt-1">
                          <p className="text-[10px] font-bold text-slate-500 mb-0.5">{item.time}</p>
                          <p className="text-xs text-slate-300 leading-snug">{item.text}</p>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </div>
              </motion.div>

            </div>
          </motion.div>
        </main>
      </div>
    </div>
  );
}
