import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Globe, LayoutDashboard, AlertTriangle, BarChart2, Camera as CameraIcon, Settings, Radio, BrainCircuit,
  Search, Bell, TrendingUp, Activity, Users, Clock, AlertOctagon, ChevronLeft, ChevronRight,
  ZoomIn, ZoomOut
} from 'lucide-react';
import { Link, useLocation } from 'wouter';
import { FloatingLights } from '@/components/CinematicBackground';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

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
  { day: 'Mon', value: 45 },
  { day: 'Tue', value: 52 },
  { day: 'Wed', value: 38 },
  { day: 'Thu', value: 67 },
  { day: 'Fri', value: 59 },
  { day: 'Sat', value: 81 },
  { day: 'Sun', value: 127 },
];

const congestionData = [
  { time: '6am', value: 22 },
  { time: '8am', value: 55 },
  { time: '10am', value: 71 },
  { time: '12pm', value: 68 },
  { time: '2pm', value: 48 },
  { time: '4pm', value: 75 },
  { time: '6pm', value: 81 },
  { time: '8pm', value: 63 },
];

export default function Dashboard() {
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
            { icon: LayoutDashboard, label: 'Dashboard', active: true, path: '/dashboard' },
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
            
            {/* Stats Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {[
                { title: 'Active Violations', value: 127, trend: '+12 today', icon: TrendingUp, color: 'text-red-400', bg: 'bg-red-500/10', border: 'hover:border-red-500/30' },
                { title: 'Congestion Score', value: 81, trend: 'High', icon: Activity, color: 'text-amber-400', bg: 'bg-amber-500/10', border: 'hover:border-amber-500/30' },
                { title: 'Officers Active', value: 12, trend: '4 en route', icon: Users, color: 'text-green-400', bg: 'bg-green-500/10', border: 'hover:border-green-500/30' },
                { title: 'Avg Response Time', value: 3.4, trend: '-0.3 from avg', icon: Clock, color: 'text-blue-400', bg: 'bg-blue-500/10', border: 'hover:border-blue-500/30', isFloat: true },
              ].map((stat, i) => (
                <motion.div 
                  key={i} 
                  variants={itemVariants}
                  className={`bg-white/[0.04] backdrop-blur-xl border border-white/[0.07] rounded-2xl p-5 transition-all duration-300 hover:-translate-y-1 ${stat.border}`}
                >
                  <div className="flex justify-between items-start mb-4">
                    <div className={`p-2.5 rounded-xl ${stat.bg}`}>
                      <stat.icon size={22} className={stat.color} />
                    </div>
                    <span className="text-xs font-semibold text-slate-400 bg-white/5 px-2 py-1 rounded-md">{stat.trend}</span>
                  </div>
                  <div className="space-y-1">
                    <h3 className="text-slate-400 text-sm font-medium tracking-wide">{stat.title}</h3>
                    <p className="text-3xl font-black tracking-tight text-white drop-shadow-md">
                      <AnimatedCounter value={stat.value} />
                      {stat.isFloat && <span className="text-lg font-medium text-slate-500 ml-1">min</span>}
                    </p>
                  </div>
                </motion.div>
              ))}
            </div>

            {/* Middle Section: Heatmap + Alerts */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[500px]">
              
              {/* Heatmap (Left, 65%) */}
              <motion.div variants={itemVariants} className="lg:col-span-2 bg-white/[0.04] backdrop-blur-xl border border-white/[0.07] rounded-2xl p-5 flex flex-col relative overflow-hidden group hover:border-white/10 transition-colors">
                <div className="flex justify-between items-center mb-4 relative z-10">
                  <h2 className="text-lg font-bold tracking-wide flex items-center gap-2">
                    Bangalore City <span className="text-slate-500 font-normal">— Live Traffic Intelligence</span>
                  </h2>
                  <div className="flex items-center gap-2">
                    <span className="flex items-center gap-1.5 text-xs font-bold text-red-400 bg-red-500/10 px-2 py-1 rounded-md border border-red-500/20 uppercase tracking-wider">
                      <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
                      Live
                    </span>
                    <div className="flex bg-white/5 rounded-lg border border-white/10 overflow-hidden">
                      <button className="p-1.5 hover:bg-white/10 text-slate-400 hover:text-white transition-colors"><ZoomIn size={16}/></button>
                      <div className="w-px bg-white/10" />
                      <button className="p-1.5 hover:bg-white/10 text-slate-400 hover:text-white transition-colors"><ZoomOut size={16}/></button>
                    </div>
                  </div>
                </div>
                
                <div className="flex-1 bg-[#060D1A] rounded-xl border border-white/5 relative overflow-hidden">
                  {/* Grid overlay */}
                  <div className="absolute inset-0 opacity-[0.03]" style={{ backgroundImage: 'linear-gradient(rgba(255,255,255,1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,1) 1px, transparent 1px)', backgroundSize: '40px 40px' }} />
                  
                  {/* Custom SVG Map Elements */}
                  <svg className="absolute inset-0 w-full h-full" viewBox="0 0 800 400" preserveAspectRatio="xMidYMid slice">
                    {/* Roads */}
                    <path d="M 100,0 C 120,150 200,200 400,250 C 600,300 700,350 800,400" fill="none" stroke="#1E293B" strokeWidth="8" />
                    <path d="M 0,200 C 150,220 300,180 400,250 C 450,280 500,400 550,400" fill="none" stroke="#1E293B" strokeWidth="12" />
                    <path d="M 300,0 L 400,250 L 500,0" fill="none" stroke="#1E293B" strokeWidth="6" />
                    <path d="M 600,0 C 580,100 650,200 750,250 L 800,260" fill="none" stroke="#1E293B" strokeWidth="6" />
                    
                    {/* Highlighted Routes */}
                    <path d="M 0,200 C 150,220 300,180 400,250" fill="none" stroke="#ef4444" strokeWidth="4" className="opacity-60" strokeDasharray="8 4" />
                    
                    {/* Hotspots */}
                    <g transform="translate(400, 250)">
                      <circle r="40" fill="#ef4444" opacity="0.1">
                        <animate attributeName="r" values="20;50;20" dur="2s" repeatCount="indefinite" />
                        <animate attributeName="opacity" values="0.2;0;0.2" dur="2s" repeatCount="indefinite" />
                      </circle>
                      <circle r="20" fill="#ef4444" opacity="0.3" />
                      <circle r="6" fill="#ef4444" className="drop-shadow-[0_0_10px_rgba(239,68,68,1)]" />
                      <text x="15" y="-10" fill="white" fontSize="12" fontWeight="bold" className="drop-shadow-md">City Center</text>
                    </g>
                    
                    <g transform="translate(200, 195)">
                      <circle r="30" fill="#f59e0b" opacity="0.1">
                        <animate attributeName="r" values="15;35;15" dur="3s" repeatCount="indefinite" />
                        <animate attributeName="opacity" values="0.2;0;0.2" dur="3s" repeatCount="indefinite" />
                      </circle>
                      <circle r="15" fill="#f59e0b" opacity="0.3" />
                      <circle r="5" fill="#f59e0b" className="drop-shadow-[0_0_10px_rgba(245,158,11,1)]" />
                      <text x="12" y="-8" fill="white" fontSize="11" fontWeight="bold">Bus Stand</text>
                    </g>
                    
                    <g transform="translate(620, 150)">
                      <circle r="45" fill="#ef4444" opacity="0.1">
                        <animate attributeName="r" values="25;55;25" dur="1.5s" repeatCount="indefinite" />
                        <animate attributeName="opacity" values="0.3;0;0.3" dur="1.5s" repeatCount="indefinite" />
                      </circle>
                      <circle r="25" fill="#ef4444" opacity="0.4" />
                      <circle r="6" fill="#ef4444" className="drop-shadow-[0_0_10px_rgba(239,68,68,1)]" />
                      <text x="15" y="-10" fill="white" fontSize="12" fontWeight="bold">Railway Station</text>
                    </g>
                    
                    <g transform="translate(480, 70)">
                      <circle r="25" fill="#eab308" opacity="0.1">
                        <animate attributeName="r" values="10;30;10" dur="2.5s" repeatCount="indefinite" />
                      </circle>
                      <circle r="12" fill="#eab308" opacity="0.3" />
                      <circle r="4" fill="#eab308" />
                      <text x="10" y="-6" fill="white" fontSize="10" fontWeight="bold">Market Road</text>
                    </g>
                  </svg>
                </div>
              </motion.div>

              {/* Right Sidebar Stack */}
              <div className="flex flex-col gap-6 h-full">
                
                {/* High Impact Zones */}
                <motion.div variants={itemVariants} className="flex-1 bg-white/[0.04] backdrop-blur-xl border border-white/[0.07] rounded-2xl p-5 hover:border-white/10 transition-colors flex flex-col">
                  <h2 className="text-sm font-bold tracking-wide flex items-center gap-2 mb-4 text-slate-200">
                    <AlertOctagon size={16} className="text-amber-400" />
                    HIGH IMPACT ZONES
                  </h2>
                  <div className="space-y-4 flex-1">
                    {[
                      { name: 'Railway Station', score: 94, color: 'bg-red-500', barColor: 'bg-red-500/20' },
                      { name: 'Bus Stand', score: 89, color: 'bg-orange-500', barColor: 'bg-orange-500/20' },
                      { name: 'Market Road', score: 85, color: 'bg-amber-500', barColor: 'bg-amber-500/20' },
                      { name: 'City Center', score: 82, color: 'bg-yellow-500', barColor: 'bg-yellow-500/20' },
                    ].map((zone, i) => (
                      <div key={i} className="space-y-1.5">
                        <div className="flex justify-between items-center text-xs">
                          <span className="font-medium text-slate-300"><span className="text-slate-500 mr-2">{i+1}.</span>{zone.name}</span>
                          <span className={`font-bold px-1.5 py-0.5 rounded text-[10px] ${zone.color} text-white`}>{zone.score}</span>
                        </div>
                        <div className={`h-1.5 w-full rounded-full overflow-hidden ${zone.barColor}`}>
                          <div className={`h-full ${zone.color} rounded-full`} style={{ width: `${zone.score}%` }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </motion.div>

                {/* Active Alerts */}
                <motion.div variants={itemVariants} className="flex-1 bg-white/[0.04] backdrop-blur-xl border border-white/[0.07] rounded-2xl p-5 hover:border-white/10 transition-colors flex flex-col">
                  <h2 className="text-sm font-bold tracking-wide flex items-center gap-2 mb-4 text-slate-200">
                    <Bell size={16} className="text-blue-400" />
                    ACTIVE ALERTS
                  </h2>
                  <div className="space-y-3 overflow-y-auto pr-1 flex-1">
                    {[
                      { cam: 'Cam 12', type: 'Illegal Parking', severity: 'HIGH', pulse: true, color: 'red' },
                      { cam: 'Cam 27', type: 'Double Parking', severity: 'MEDIUM', pulse: false, color: 'amber' },
                      { cam: 'Cam 08', type: 'Lane Blocking', severity: 'HIGH', pulse: true, color: 'red' },
                    ].map((alert, i) => (
                      <div key={i} className={`group flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/5 hover:bg-white/10 transition-colors ${alert.color === 'red' ? 'hover:border-red-500/30 hover:shadow-[0_0_15px_rgba(239,68,68,0.1)]' : ''}`}>
                        <div className="flex items-center gap-3">
                          <div className={`p-2 rounded-lg bg-\${alert.color}-500/10`}>
                            <CameraIcon size={14} className={`text-\${alert.color}-400`} />
                          </div>
                          <div>
                            <p className="text-xs font-bold text-slate-200">{alert.type}</p>
                            <p className="text-[10px] text-slate-500 uppercase tracking-wider">{alert.cam}</p>
                          </div>
                        </div>
                        <div className={`flex items-center gap-1.5 px-2 py-1 rounded border text-[10px] font-bold tracking-wider
                          ${alert.color === 'red' ? 'bg-red-500/10 border-red-500/20 text-red-400' : 'bg-amber-500/10 border-amber-500/20 text-amber-400'}
                        `}>
                          {alert.pulse && <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />}
                          {alert.severity}
                        </div>
                      </div>
                    ))}
                  </div>
                </motion.div>
                
              </div>
            </div>

            {/* Bottom Charts Section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[300px]">
              
              <motion.div variants={itemVariants} className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.07] rounded-2xl p-5 flex flex-col hover:border-white/10 transition-colors">
                <h2 className="text-sm font-bold tracking-wide text-slate-200 mb-6">VIOLATION TREND — LAST 7 DAYS</h2>
                <div className="flex-1 w-full relative">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={violationData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                      <defs>
                        <linearGradient id="colorViolations" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                      <XAxis dataKey="day" stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                      <YAxis stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#0f172a', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '8px', color: '#fff' }}
                        itemStyle={{ color: '#60A5FA' }}
                      />
                      <Area type="monotone" dataKey="value" stroke="#3B82F6" strokeWidth={3} fillOpacity={1} fill="url(#colorViolations)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </motion.div>

              <motion.div variants={itemVariants} className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.07] rounded-2xl p-5 flex flex-col hover:border-white/10 transition-colors">
                <h2 className="text-sm font-bold tracking-wide text-slate-200 mb-6">CONGESTION SCORE — TODAY</h2>
                <div className="flex-1 w-full relative">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={congestionData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                      <defs>
                        <linearGradient id="colorCongestion" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#7C3AED" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="#7C3AED" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                      <XAxis dataKey="time" stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                      <YAxis stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#0f172a', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '8px', color: '#fff' }}
                        itemStyle={{ color: '#A78BFA' }}
                      />
                      <Area type="monotone" dataKey="value" stroke="#7C3AED" strokeWidth={3} fillOpacity={1} fill="url(#colorCongestion)" />
                    </AreaChart>
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