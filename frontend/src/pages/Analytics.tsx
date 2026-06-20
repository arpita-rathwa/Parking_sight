import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Globe, LayoutDashboard, AlertTriangle, BarChart2, Camera as CameraIcon, Settings, Radio, BrainCircuit,
  Search, Bell, TrendingUp, Activity, Clock, CheckCircle, ChevronLeft, ChevronRight,
  MapPin, Zap, Target
} from 'lucide-react';
import { useLocation } from 'wouter';
import { FloatingLights } from '@/components/CinematicBackground';
import { useSummary, useTrends, usePriorityQueue, useCongestionHeat, useViolationTypes, useAnalyticsInsights, usePredictedHotspots } from '@/lib/hooks';
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell, BarChart, Bar, Legend
} from 'recharts';

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

const DAY_NAMES = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

export default function Analytics() {
  const [collapsed, setCollapsed] = useState(false);
  const [, setLocation] = useLocation();
  const [dateRange, setDateRange] = useState('This Week');
  const { data: summary } = useSummary();
  const { data: trends } = useTrends(30);
  const { data: priorityZones } = usePriorityQueue(5);
  const { data: congestionHeatData } = useCongestionHeat();
  const { data: violationTypesData } = useViolationTypes();
  const { data: insightsData } = useAnalyticsInsights();
  const { data: hotspotsData } = usePredictedHotspots();

  const heatData = congestionHeatData ?? [
    { time: '6am', morning: 30, afternoon: 0, evening: 0 },
    { time: '8am', morning: 85, afternoon: 10, evening: 0 },
    { time: '10am', morning: 65, afternoon: 30, evening: 0 },
    { time: '12pm', morning: 20, afternoon: 70, evening: 10 },
    { time: '2pm', morning: 10, afternoon: 85, evening: 20 },
    { time: '4pm', morning: 0, afternoon: 50, evening: 60 },
    { time: '6pm', morning: 0, afternoon: 20, evening: 95 },
    { time: '8pm', morning: 0, afternoon: 0, evening: 40 },
  ];

  const typesData = violationTypesData ?? [
    { name: 'Illegal Parking', value: 35, color: '#3B82F6' },
    { name: 'Double Parking', value: 22, color: '#8B5CF6' },
    { name: 'Lane Blocking', value: 18, color: '#EF4444' },
    { name: 'Wrong Parking', value: 15, color: '#F59E0B' },
    { name: 'No Parking Zone', value: 10, color: '#10B981' },
  ];

  // Animation states for progress bars
  const [zonesAnim, setZonesAnim] = useState(false);
  useEffect(() => {
    const t = setTimeout(() => setZonesAnim(true), 500);
    return () => clearTimeout(t);
  }, []);

  const violationTrendsData = trends?.trends?.map((t, i) => ({
    day: i + 1,
    violations: t.count,
  })) || [];

  const topZonesData = priorityZones?.slice(0, 5).map((z, i) => ({
    rank: i + 1,
    name: z.zone_name,
    score: z.average_impact,
    color: z.average_impact >= 70 ? 'bg-red-500' : z.average_impact >= 50 ? 'bg-orange-500' : 'bg-amber-500',
    barColor: z.average_impact >= 70 ? 'bg-red-500/20' : z.average_impact >= 50 ? 'bg-orange-500/20' : 'bg-amber-500/20',
  })) || [];

  const weeklyPerformanceData = trends?.trends?.slice(-7).map((t, i) => ({
    day: DAY_NAMES[new Date(t.date).getDay()] || `Day ${i + 1}`,
    violations: t.count,
    resolved: Math.round(t.count * 0.85),
    avgResponse: +(3 + Math.random() * 2).toFixed(1),
  })) || [];

  const kpis = [
    { title: 'Total Violations', value: summary?.total_violations ?? 0, icon: TrendingUp, color: 'text-red-400', bg: 'bg-red-500/10', trend: '+127 today', sparklineColors: 'bg-red-500' },
    { title: 'Avg Congestion Score', value: summary?.congestion_score ?? 0, icon: Activity, color: 'text-orange-400', bg: 'bg-orange-500/10', trend: '↑ 3pts', sparklineColors: 'bg-orange-500' },
    { title: 'Hotspot Zones', value: priorityZones?.length ?? 0, icon: MapPin, color: 'text-purple-400', bg: 'bg-purple-500/10', trend: '+2 this week', sparklineColors: 'bg-purple-500' },
    { title: 'Avg Response Time', value: summary?.avg_response_time_min ?? 0, icon: Clock, color: 'text-cyan-400', bg: 'bg-cyan-500/10', trend: '↓ 0.3 min', isFloat: true, sparklineColors: 'bg-cyan-500' },
    { title: 'Resolution Rate', value: summary?.resolution_rate ?? 0, icon: CheckCircle, color: 'text-green-400', bg: 'bg-green-500/10', trend: '↑ 2%', isPercent: true, sparklineColors: 'bg-green-500' },
    { title: 'Active Cameras', value: summary?.active_cameras ?? 0, icon: CameraIcon, color: 'text-blue-400', bg: 'bg-blue-500/10', trend: 'All operational', sparklineColors: 'bg-blue-500' },
  ];

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
            { icon: LayoutDashboard, label: 'Dashboard', active: false, path: '/dashboard' },
            { icon: AlertTriangle, label: 'Alerts', active: false, path: '/alerts' },
            { icon: BarChart2, label: 'Analytics', active: true, path: '/analytics' },
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
            {/* Page Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
              <div>
                <h1 className="text-4xl font-bold tracking-wider mb-2 text-blue-400 drop-shadow-[0_0_15px_rgba(59,130,246,0.6)]" style={{ fontFamily: "'Orbitron', sans-serif" }}>
                  Traffic Intelligence
                </h1>
                <p className="text-slate-400 text-sm font-medium">Analyze congestion patterns and parking violations across the city.</p>
              </div>
              <div className="flex bg-white/5 border border-white/10 p-1 rounded-xl shadow-[inset_0_2px_10px_rgba(0,0,0,0.2)]">
                {['Today', 'This Week', 'This Month', 'Custom'].map((range) => (
                  <button
                    key={range}
                    onClick={() => setDateRange(range)}
                    className={`px-4 py-1.5 rounded-lg text-sm font-semibold transition-all ${
                      dateRange === range 
                        ? 'bg-blue-600 text-white shadow-[0_0_15px_rgba(59,130,246,0.4)]' 
                        : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
                    }`}
                  >
                    {range}
                  </button>
                ))}
              </div>
            </div>

            {/* KPI Cards Row */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
              {kpis.map((stat, i) => (
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
                  <div className="mt-2 mb-4 z-10 relative">
                    <p className="text-3xl font-black tracking-tight text-white drop-shadow-md">
                      <AnimatedCounter value={stat.value} />
                      {stat.isFloat && <span className="text-sm font-medium text-slate-500 ml-1">min</span>}
                      {stat.isPercent && <span className="text-sm font-medium text-slate-500 ml-1">%</span>}
                    </p>
                    <h3 className="text-slate-400 text-[11px] font-bold uppercase tracking-wider mt-1">{stat.title}</h3>
                  </div>
                  
                  {/* Sparkline at bottom */}
                  <div className="absolute bottom-0 left-0 right-0 h-8 flex items-end justify-between px-4 pb-2 opacity-40">
                    {[40, 70, 45, 90, 60, 85, 50].map((h, j) => (
                      <div key={j} className={`w-1 rounded-t-sm ${stat.sparklineColors}`} style={{ height: `${h}%` }} />
                    ))}
                  </div>
                </motion.div>
              ))}
            </div>

            {/* Section 1: Violation Trends */}
            <motion.div variants={itemVariants} className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.07] rounded-2xl p-5 hover:border-white/10 transition-colors h-[340px] flex flex-col">
              <h2 className="text-sm font-bold tracking-wide text-slate-200 mb-6 flex items-center gap-2">
                <TrendingUp size={16} className="text-blue-400" />
                VIOLATION TRENDS — LAST 30 DAYS
              </h2>
              <div className="flex-1 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={violationTrendsData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" vertical={false} />
                    <XAxis dataKey="day" stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => `Day ${val}`} />
                    <YAxis stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                    <RechartsTooltip 
                      contentStyle={{ backgroundColor: 'rgba(15, 23, 42, 0.9)', backdropFilter: 'blur(8px)', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '8px', color: '#fff' }}
                      itemStyle={{ color: '#60A5FA', fontWeight: 'bold' }}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="violations" 
                      stroke="#3B82F6" 
                      strokeWidth={3} 
                      dot={{ r: 3, fill: '#0B1120', stroke: '#3B82F6', strokeWidth: 2 }}
                      activeDot={{ r: 6, fill: '#3B82F6', stroke: '#fff', strokeWidth: 2 }}
                      style={{ filter: 'drop-shadow(0px 4px 8px rgba(59,130,246,0.4))' }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </motion.div>

            {/* Section 2: Heat + Donut */}
            <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 h-[340px]">
              <motion.div variants={itemVariants} className="lg:col-span-3 bg-white/[0.04] backdrop-blur-xl border border-white/[0.07] rounded-2xl p-5 hover:border-white/10 transition-colors flex flex-col">
                <h2 className="text-sm font-bold tracking-wide text-slate-200 mb-6 flex items-center gap-2">
                  <Activity size={16} className="text-orange-400" />
                  CONGESTION HEAT ANALYSIS
                </h2>
                <div className="flex-1 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={heatData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                      <defs>
                        <linearGradient id="colorMorning" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.4}/>
                          <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
                        </linearGradient>
                        <linearGradient id="colorAfternoon" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#A855F7" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="#A855F7" stopOpacity={0}/>
                        </linearGradient>
                        <linearGradient id="colorEvening" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#EF4444" stopOpacity={0.4}/>
                          <stop offset="95%" stopColor="#EF4444" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                      <XAxis dataKey="time" stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                      <YAxis stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                      <RechartsTooltip 
                        contentStyle={{ backgroundColor: 'rgba(15, 23, 42, 0.9)', backdropFilter: 'blur(8px)', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '8px' }}
                      />
                      <Area type="monotone" dataKey="morning" stackId="1" stroke="#3B82F6" strokeWidth={2} fill="url(#colorMorning)" />
                      <Area type="monotone" dataKey="afternoon" stackId="2" stroke="#A855F7" strokeWidth={2} fill="url(#colorAfternoon)" />
                      <Area type="monotone" dataKey="evening" stackId="3" stroke="#EF4444" strokeWidth={2} fill="url(#colorEvening)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </motion.div>

              <motion.div variants={itemVariants} className="lg:col-span-2 bg-white/[0.04] backdrop-blur-xl border border-white/[0.07] rounded-2xl p-5 hover:border-white/10 transition-colors flex flex-col relative">
                <h2 className="text-sm font-bold tracking-wide text-slate-200 mb-2 flex items-center gap-2">
                  <PieChart size={16} className="text-purple-400" />
                  VIOLATION DISTRIBUTION
                </h2>
                <div className="flex-1 w-full flex items-center justify-center relative -mt-4">
                  <ResponsiveContainer width="100%" height={220}>
                    <PieChart>
                      <Pie
                        data={typesData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={80}
                        paddingAngle={5}
                        dataKey="value"
                        stroke="none"
                      >
                        {typesData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <RechartsTooltip 
                        contentStyle={{ backgroundColor: 'rgba(15, 23, 42, 0.9)', backdropFilter: 'blur(8px)', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '8px' }}
                        itemStyle={{ color: '#fff', fontWeight: 'bold' }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="absolute inset-0 flex items-center justify-center pointer-events-none mt-4">
                    <span className="text-2xl font-black text-white">{summary?.total_violations?.toLocaleString() ?? 0}</span>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-x-2 gap-y-2 mt-2">
                  {typesData.map((item, i) => (
                    <div key={i} className="flex items-center gap-2 text-xs">
                      <div className="w-2 h-2 rounded-full" style={{ backgroundColor: item.color }} />
                      <span className="text-slate-300 font-medium truncate">{item.name}</span>
                      <span className="text-slate-500 ml-auto font-bold">{item.value}%</span>
                    </div>
                  ))}
                </div>
              </motion.div>
            </div>

            {/* Section 3: Zones + Bar Chart */}
            <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 h-[360px]">
              
              <motion.div variants={itemVariants} className="lg:col-span-2 bg-white/[0.04] backdrop-blur-xl border border-white/[0.07] rounded-2xl p-5 hover:border-white/10 transition-colors flex flex-col">
                <h2 className="text-sm font-bold tracking-wide text-slate-200 mb-5 flex items-center gap-2">
                  <MapPin size={16} className="text-amber-400" />
                  TOP CONGESTION ZONES
                </h2>
                <div className="space-y-5 flex-1 flex flex-col justify-center">
                  {topZonesData.map((zone, i) => (
                    <motion.div 
                      key={i}
                      initial={{ opacity: 0, x: -20 }}
                      animate={zonesAnim ? { opacity: 1, x: 0 } : {}}
                      transition={{ delay: i * 0.1, duration: 0.5 }}
                      className="space-y-2"
                    >
                      <div className="flex justify-between items-center text-sm">
                        <span className="font-bold text-slate-200 flex items-center gap-3">
                          <span className="text-slate-500 font-mono text-xs w-4">{zone.rank}.</span>
                          {zone.name}
                        </span>
                        <span className={`font-black px-2 py-0.5 rounded text-xs ${zone.color} text-white shadow-sm`}>{zone.score}</span>
                      </div>
                      <div className={`h-2 w-full rounded-full overflow-hidden ${zone.barColor}`}>
                        <motion.div 
                          className={`h-full ${zone.color} rounded-full`}
                          initial={{ width: 0 }}
                          animate={zonesAnim ? { width: `${zone.score}%` } : {}}
                          transition={{ delay: i * 0.1 + 0.3, duration: 0.8, type: "spring" }}
                        />
                      </div>
                    </motion.div>
                  ))}
                </div>
              </motion.div>

              <motion.div variants={itemVariants} className="lg:col-span-3 bg-white/[0.04] backdrop-blur-xl border border-white/[0.07] rounded-2xl p-5 hover:border-white/10 transition-colors flex flex-col">
                <h2 className="text-sm font-bold tracking-wide text-slate-200 mb-6 flex items-center gap-2">
                  <BarChart2 size={16} className="text-green-400" />
                  WEEKLY PERFORMANCE
                </h2>
                <div className="flex-1 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={weeklyPerformanceData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                      <XAxis dataKey="day" stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                      <YAxis stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                      <RechartsTooltip 
                        contentStyle={{ backgroundColor: 'rgba(15, 23, 42, 0.9)', backdropFilter: 'blur(8px)', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '8px' }}
                        cursor={{ fill: 'rgba(255,255,255,0.04)' }}
                      />
                      <Legend iconType="circle" wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
                      <Bar dataKey="violations" name="Violations" fill="#3B82F6" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="resolved" name="Resolved" fill="#10B981" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="avgResponse" name="Response (min)" fill="#A855F7" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </motion.div>

            </div>

            {/* Section 4: AI Insights + Forecast */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[320px]">
              
              <motion.div variants={itemVariants} className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.07] shadow-[inset_0_0_40px_rgba(168,85,247,0.05)] hover:shadow-[inset_0_0_60px_rgba(168,85,247,0.1)] rounded-2xl p-6 transition-all relative overflow-hidden group">
                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-purple-500 to-blue-500" />
                <div className="flex flex-col h-full z-10 relative">
                  <div className="mb-6">
                    <h2 className="text-lg font-bold tracking-wide text-white flex items-center gap-2 drop-shadow-md">
                      <Zap size={20} className="text-purple-400 fill-purple-400/20" />
                      AI Insights
                    </h2>
                    <p className="text-xs text-slate-400 mt-1 uppercase tracking-wider font-semibold">Powered by ParkSight Intelligence Engine</p>
                  </div>
                  
                  <div className="space-y-4 flex-1 flex flex-col justify-center">
                    {insightsData?.slice(0, 5).map((text, i) => (
                      <motion.div 
                        key={i}
                        initial={{ opacity: 0, x: 20 }}
                        animate={zonesAnim ? { opacity: 1, x: 0 } : {}}
                        transition={{ delay: i * 0.15 + 0.4 }}
                        className="flex items-start gap-4 p-3 rounded-xl bg-white/5 border border-white/5 hover:bg-white/10 transition-colors"
                      >
                        <div className="mt-0.5 w-6 h-6 rounded-full flex items-center justify-center shrink-0 bg-blue-500/20 text-blue-400">
                          <Zap size={12} />
                        </div>
                        <p className="text-sm font-medium text-slate-200 leading-snug">{text}</p>
                      </motion.div>
                    )) || (
                      <p className="text-sm text-slate-500">No insights available.</p>
                    )}
                  </div>
                </div>
              </motion.div>

              <motion.div variants={itemVariants} className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.07] shadow-[inset_0_0_40px_rgba(6,182,212,0.05)] hover:shadow-[inset_0_0_60px_rgba(6,182,212,0.1)] rounded-2xl p-6 transition-all relative overflow-hidden group">
                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-cyan-500 to-blue-500" />
                <div className="flex flex-col h-full z-10 relative">
                  <div className="mb-6">
                    <h2 className="text-lg font-bold tracking-wide text-white flex items-center gap-2 drop-shadow-md">
                      <Target size={20} className="text-cyan-400" />
                      Predicted Hotspots
                    </h2>
                    <p className="text-xs text-slate-400 mt-1 uppercase tracking-wider font-semibold">Forecast for Tomorrow — Confidence Intervals</p>
                  </div>
                  
                  <div className="space-y-6 flex-1 flex flex-col justify-center">
                    {(hotspotsData ?? [
                      { name: 'Railway Station', confidence: 94 },
                      { name: 'Bus Stand', confidence: 87 },
                      { name: 'Market Road', confidence: 76 },
                    ]).map((spot, i) => {
                      const colors = ['bg-red-500', 'bg-orange-500', 'bg-amber-500', 'bg-yellow-500', 'bg-rose-500'];
                      const glows = [
                        'shadow-[0_0_10px_rgba(239,68,68,0.8)]',
                        'shadow-[0_0_10px_rgba(249,115,22,0.8)]',
                        'shadow-[0_0_10px_rgba(245,158,11,0.8)]',
                        'shadow-[0_0_10px_rgba(234,179,8,0.8)]',
                        'shadow-[0_0_10px_rgba(244,63,94,0.8)]',
                      ];
                      const c = colors[i % colors.length];
                      const g = glows[i % glows.length];
                      return (
                        <motion.div 
                          key={i}
                          initial={{ opacity: 0, y: 10 }}
                          animate={zonesAnim ? { opacity: 1, y: 0 } : {}}
                          transition={{ delay: i * 0.1 + 0.5 }}
                          className="space-y-2"
                        >
                          <div className="flex justify-between items-center">
                            <span className="font-bold text-sm text-slate-200 flex items-center gap-2">
                              <span className={`w-2 h-2 rounded-full ${c} animate-pulse ${g}`} />
                              {spot.name}
                            </span>
                            <span className="text-xs font-bold text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20">{spot.confidence}% confidence</span>
                          </div>
                          <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                            <motion.div 
                              className={`h-full ${c} rounded-full opacity-80`}
                              initial={{ width: 0 }}
                              animate={zonesAnim ? { width: `${spot.confidence}%` } : {}}
                              transition={{ delay: i * 0.1 + 0.8, duration: 1 }}
                            />
                          </div>
                        </motion.div>
                      );
                    })}
                  </div>
                </div>
              </motion.div>

            </div>

            {/* Section 5: City Heatmap */}
            <motion.div variants={itemVariants} className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.07] rounded-2xl p-5 flex flex-col overflow-hidden relative group">
              <h2 className="text-sm font-bold tracking-wide flex items-center gap-2 mb-4 text-slate-200 relative z-10">
                CITY-WIDE ALERT HEATMAP — BANGALORE
              </h2>
              
              <div className="flex-1 h-[300px] bg-[#060D1A] rounded-xl border border-white/5 relative overflow-hidden">
                {/* Grid overlay */}
                <div className="absolute inset-0 opacity-[0.05]" style={{ backgroundImage: 'linear-gradient(rgba(255,255,255,1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,1) 1px, transparent 1px)', backgroundSize: '30px 30px' }} />
                
                {/* Custom SVG Map Elements */}
                <svg className="absolute inset-0 w-full h-full" viewBox="0 0 1000 300" preserveAspectRatio="xMidYMid slice">
                  {/* Thin decorative roads/lines */}
                  <polyline points="100,50 300,100 500,80 800,150 950,120" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="2" />
                  <polyline points="50,200 200,250 450,220 600,280 900,200" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="2" />
                  <polyline points="300,100 200,250" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="2" />
                  <polyline points="500,80 600,280" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="2" />
                  
                  {/* Railway Station (top-center) */}
                  <g transform="translate(500, 80)">
                    <circle r="60" fill="#ef4444" opacity="0.05">
                      <animate attributeName="r" values="30;80;30" dur="2s" repeatCount="indefinite" />
                    </circle>
                    <circle r="30" fill="#ef4444" opacity="0.2" />
                    <circle r="8" fill="#ef4444" className="drop-shadow-[0_0_15px_rgba(239,68,68,1)]" />
                    <rect x="15" y="-12" width="70" height="20" fill="rgba(239,68,68,0.15)" rx="4" stroke="rgba(239,68,68,0.3)" />
                    <text x="22" y="2" fill="#fca5a5" fontSize="10" fontWeight="bold">CRITICAL</text>
                    <text x="-40" y="30" fill="white" fontSize="12" fontWeight="bold">Railway Station</text>
                  </g>
                  
                  {/* Bus Stand (left-center) */}
                  <g transform="translate(250, 150)">
                    <circle r="40" fill="#f97316" opacity="0.08">
                      <animate attributeName="r" values="20;50;20" dur="2.5s" repeatCount="indefinite" />
                    </circle>
                    <circle r="20" fill="#f97316" opacity="0.2" />
                    <circle r="6" fill="#f97316" className="drop-shadow-[0_0_10px_rgba(249,115,22,1)]" />
                    <rect x="12" y="-10" width="40" height="16" fill="rgba(249,115,22,0.15)" rx="3" stroke="rgba(249,115,22,0.3)" />
                    <text x="16" y="2" fill="#fdba74" fontSize="9" fontWeight="bold">HIGH</text>
                    <text x="-30" y="25" fill="white" fontSize="11" fontWeight="bold">Bus Stand</text>
                  </g>

                  {/* City Center (center) */}
                  <g transform="translate(450, 200)">
                    <circle r="45" fill="#ef4444" opacity="0.08">
                      <animate attributeName="r" values="25;55;25" dur="2.2s" repeatCount="indefinite" />
                    </circle>
                    <circle r="22" fill="#ef4444" opacity="0.2" />
                    <circle r="6" fill="#ef4444" className="drop-shadow-[0_0_10px_rgba(239,68,68,1)]" />
                    <rect x="12" y="-10" width="40" height="16" fill="rgba(239,68,68,0.15)" rx="3" stroke="rgba(239,68,68,0.3)" />
                    <text x="16" y="2" fill="#fca5a5" fontSize="9" fontWeight="bold">HIGH</text>
                    <text x="-30" y="25" fill="white" fontSize="11" fontWeight="bold">City Center</text>
                  </g>

                  {/* Market Road (bottom-right) */}
                  <g transform="translate(700, 240)">
                    <circle r="30" fill="#f59e0b" opacity="0.1">
                      <animate attributeName="r" values="15;35;15" dur="3s" repeatCount="indefinite" />
                    </circle>
                    <circle r="15" fill="#f59e0b" opacity="0.3" />
                    <circle r="5" fill="#f59e0b" />
                    <rect x="10" y="-8" width="50" height="14" fill="rgba(245,158,11,0.15)" rx="2" stroke="rgba(245,158,11,0.3)" />
                    <text x="14" y="2" fill="#fcd34d" fontSize="8" fontWeight="bold">MEDIUM</text>
                    <text x="-35" y="20" fill="white" fontSize="10" fontWeight="bold">Market Road</text>
                  </g>

                  {/* Hospital Circle (right) */}
                  <g transform="translate(850, 140)">
                    <circle r="30" fill="#f59e0b" opacity="0.1">
                      <animate attributeName="r" values="15;35;15" dur="3.5s" repeatCount="indefinite" />
                    </circle>
                    <circle r="15" fill="#f59e0b" opacity="0.3" />
                    <circle r="5" fill="#f59e0b" />
                    <rect x="10" y="-8" width="50" height="14" fill="rgba(245,158,11,0.15)" rx="2" stroke="rgba(245,158,11,0.3)" />
                    <text x="14" y="2" fill="#fcd34d" fontSize="8" fontWeight="bold">MEDIUM</text>
                    <text x="-35" y="20" fill="white" fontSize="10" fontWeight="bold">Hospital Circle</text>
                  </g>
                </svg>
              </div>
            </motion.div>

          </motion.div>
        </main>
      </div>
    </div>
  );
}