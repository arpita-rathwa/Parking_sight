import { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Globe, LayoutDashboard, AlertTriangle, BarChart2, Camera as CameraIcon, Settings, Radio, BrainCircuit,
  Search, Bell, AlertOctagon, AlertCircle, CheckCircle, ChevronLeft, ChevronRight,
  Activity, UserCheck, Navigation, TrendingUp, Filter
} from 'lucide-react';
import { useLocation } from 'wouter';
import { FloatingLights } from '@/components/CinematicBackground';

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

const alertsData = [
  { id: 'CAM-008', severity: 'CRITICAL', zone: 'City Center', type: 'Lane Blocking', time: '10:11 AM', status: 'ACTIVE', officer: 'Officer 6' },
  { id: 'CAM-012', severity: 'HIGH', zone: 'Railway Station', type: 'Illegal Parking', time: '09:45 AM', status: 'ACTIVE', officer: 'Officer 3' },
  { id: 'CAM-019', severity: 'HIGH', zone: 'Bus Stand', type: 'No Parking Zone', time: '10:33 AM', status: 'ACTIVE', officer: 'Officer 5' },
  { id: 'CAM-027', severity: 'MEDIUM', zone: 'Bus Stand', type: 'Double Parking', time: '10:02 AM', status: 'ACTIVE', officer: 'Officer 1' },
  { id: 'CAM-031', severity: 'MEDIUM', zone: 'Market Road', type: 'Overstay Violation', time: '10:28 AM', status: 'ACTIVE', officer: 'Officer 4' },
  { id: 'CAM-044', severity: 'MEDIUM', zone: 'City Center', type: 'Footpath Parking', time: '10:40 AM', status: 'ACTIVE', officer: 'Officer 2' },
  { id: 'CAM-021', severity: 'LOW', zone: 'Market Road', type: 'Wrong Parking', time: '10:20 AM', status: 'RESOLVED', officer: 'Officer 2' },
  { id: 'CAM-015', severity: 'LOW', zone: 'Railway Station', type: 'Expired Permit', time: '09:58 AM', status: 'RESOLVED', officer: 'Officer 1' },
];

const timelineData = [
  { time: '10:41 AM', icon: UserCheck, color: 'text-green-400', bg: 'bg-green-500/20', text: 'Officer 2 resolved violation at Market Road' },
  { time: '10:38 AM', icon: AlertOctagon, color: 'text-red-400', bg: 'bg-red-500/20', text: 'CRITICAL alert triggered at City Center' },
  { time: '10:33 AM', icon: Navigation, color: 'text-blue-400', bg: 'bg-blue-500/20', text: 'Officer 5 dispatched to Bus Stand' },
  { time: '10:28 AM', icon: CameraIcon, color: 'text-amber-400', bg: 'bg-amber-500/20', text: 'CAM-031 detected Overstay at Market Road' },
  { time: '10:21 AM', icon: Navigation, color: 'text-blue-400', bg: 'bg-blue-500/20', text: 'Officer 3 dispatched to Railway Station' },
  { time: '10:18 AM', icon: CameraIcon, color: 'text-amber-400', bg: 'bg-amber-500/20', text: 'CAM-012 detected Illegal Parking' },
  { time: '10:12 AM', icon: TrendingUp, color: 'text-orange-400', bg: 'bg-orange-500/20', text: 'Congestion score increased to 89' },
  { time: '10:05 AM', icon: CheckCircle, color: 'text-green-400', bg: 'bg-green-500/20', text: 'Violation resolved by Officer 2' },
];

export default function Alerts() {
  const [collapsed, setCollapsed] = useState(false);
  const [, setLocation] = useLocation();

  const [searchTerm, setSearchTerm] = useState('');
  const [severityFilter, setSeverityFilter] = useState('All');
  const [zoneFilter, setZoneFilter] = useState('All');
  const [statusFilter, setStatusFilter] = useState('All');

  useEffect(() => {
    document.title = 'Live Alerts | ParkSight';
  }, []);

  const filteredAlerts = useMemo(() => {
    return alertsData.filter((alert) => {
      const matchesSearch = 
        alert.id.toLowerCase().includes(searchTerm.toLowerCase()) || 
        alert.type.toLowerCase().includes(searchTerm.toLowerCase()) ||
        alert.officer.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesSeverity = severityFilter === 'All' || alert.severity === severityFilter.toUpperCase();
      const matchesZone = zoneFilter === 'All' || alert.zone === zoneFilter;
      const matchesStatus = statusFilter === 'All' || alert.status === statusFilter.toUpperCase();

      return matchesSearch && matchesSeverity && matchesZone && matchesStatus;
    });
  }, [searchTerm, severityFilter, zoneFilter, statusFilter]);

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

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
        return (
          <span className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-bold tracking-wider">
            <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
            {severity}
          </span>
        );
      case 'HIGH':
        return (
          <span className="px-2.5 py-1 rounded bg-orange-500/10 border border-orange-500/20 text-orange-400 text-xs font-bold tracking-wider">
            {severity}
          </span>
        );
      case 'MEDIUM':
        return (
          <span className="px-2.5 py-1 rounded bg-amber-500/10 border border-amber-500/20 text-amber-400 text-xs font-bold tracking-wider">
            {severity}
          </span>
        );
      case 'LOW':
        return (
          <span className="px-2.5 py-1 rounded bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-bold tracking-wider">
            {severity}
          </span>
        );
      default:
        return <span>{severity}</span>;
    }
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
            { icon: AlertTriangle, label: 'Alerts', active: true, path: '/alerts' },
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
            {/* Page Header */}
            <div className="flex items-center justify-between mb-2">
              <div>
                <h1 className="text-4xl font-bold tracking-wider mb-2 text-white drop-shadow-[0_0_10px_rgba(255,255,255,0.1)]" style={{ fontFamily: "'Orbitron', sans-serif" }}>
                  Live Alerts
                </h1>
                <p className="text-slate-400 text-sm font-medium">Monitor and respond to active parking violations across the city.</p>
              </div>
              <div className="flex items-center gap-2 bg-green-500/10 border border-green-500/20 rounded-lg px-4 py-2">
                <div className="w-2.5 h-2.5 rounded-full bg-green-500 animate-pulse shadow-[0_0_10px_rgba(34,197,94,0.8)]" />
                <span className="text-sm font-bold text-green-400 tracking-wider uppercase">LIVE</span>
              </div>
            </div>
            
            {/* Stats Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {[
                { title: 'Critical Alerts', value: 12, trend: '+2 in last hour', icon: AlertOctagon, color: 'text-red-400', bg: 'bg-red-500/10', border: 'hover:border-red-500/30' },
                { title: 'High Alerts', value: 28, trend: '+5 today', icon: AlertTriangle, color: 'text-orange-400', bg: 'bg-orange-500/10', border: 'hover:border-orange-500/30' },
                { title: 'Medium Alerts', value: 43, trend: 'Steady', icon: AlertCircle, color: 'text-amber-400', bg: 'bg-amber-500/10', border: 'hover:border-amber-500/30' },
                { title: 'Resolved Today', value: 145, trend: '+12 this hour', icon: CheckCircle, color: 'text-green-400', bg: 'bg-green-500/10', border: 'hover:border-green-500/30' },
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
                    </p>
                  </div>
                </motion.div>
              ))}
            </div>

            {/* Filters Row */}
            <motion.div variants={itemVariants} className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.07] rounded-xl p-3 flex flex-wrap items-center gap-4">
              <div className="flex items-center gap-2 text-slate-400 pl-2">
                <Filter size={18} />
                <span className="text-sm font-semibold uppercase tracking-wider">Filters</span>
              </div>
              <div className="w-px h-6 bg-white/10 mx-2" />
              
              <div className="relative flex-1 min-w-[200px]">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 w-4 h-4" />
                <input 
                  type="text" 
                  placeholder="Search alerts..." 
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-lg py-1.5 pl-9 pr-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500/50 transition-colors"
                  data-testid="filter-search"
                />
              </div>

              <select 
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value)}
                className="bg-white/5 border border-white/10 rounded-lg py-1.5 px-3 text-sm text-slate-200 focus:outline-none focus:border-blue-500/50 transition-colors [&>option]:bg-[#0B1120]"
                data-testid="filter-severity"
              >
                <option value="All">All Severities</option>
                <option value="Critical">Critical</option>
                <option value="High">High</option>
                <option value="Medium">Medium</option>
                <option value="Low">Low</option>
              </select>

              <select 
                value={zoneFilter}
                onChange={(e) => setZoneFilter(e.target.value)}
                className="bg-white/5 border border-white/10 rounded-lg py-1.5 px-3 text-sm text-slate-200 focus:outline-none focus:border-blue-500/50 transition-colors [&>option]:bg-[#0B1120]"
                data-testid="filter-zone"
              >
                <option value="All">All Zones</option>
                <option value="City Center">City Center</option>
                <option value="Railway Station">Railway Station</option>
                <option value="Bus Stand">Bus Stand</option>
                <option value="Market Road">Market Road</option>
              </select>

              <select 
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="bg-white/5 border border-white/10 rounded-lg py-1.5 px-3 text-sm text-slate-200 focus:outline-none focus:border-blue-500/50 transition-colors [&>option]:bg-[#0B1120]"
                data-testid="filter-status"
              >
                <option value="All">All Statuses</option>
                <option value="Active">Active</option>
                <option value="Resolved">Resolved</option>
              </select>
            </motion.div>

            {/* Main Content Split */}
            <div className="grid grid-cols-1 lg:grid-cols-10 gap-6 h-[500px]">
              
              {/* Left Column: Alerts Table (70%) */}
              <motion.div variants={itemVariants} className="lg:col-span-7 bg-white/[0.04] backdrop-blur-xl border border-white/[0.07] rounded-2xl flex flex-col overflow-hidden">
                <div className="overflow-x-auto flex-1 custom-scrollbar">
                  <table className="w-full text-left border-collapse">
                    <thead className="sticky top-0 bg-[#0B1120]/90 backdrop-blur-md border-b border-white/[0.08] z-10">
                      <tr>
                        <th className="py-4 px-5 text-xs font-semibold text-slate-400 uppercase tracking-wider">Severity</th>
                        <th className="py-4 px-5 text-xs font-semibold text-slate-400 uppercase tracking-wider">Camera ID</th>
                        <th className="py-4 px-5 text-xs font-semibold text-slate-400 uppercase tracking-wider">Zone</th>
                        <th className="py-4 px-5 text-xs font-semibold text-slate-400 uppercase tracking-wider">Violation Type</th>
                        <th className="py-4 px-5 text-xs font-semibold text-slate-400 uppercase tracking-wider">Timestamp</th>
                        <th className="py-4 px-5 text-xs font-semibold text-slate-400 uppercase tracking-wider">Status</th>
                        <th className="py-4 px-5 text-xs font-semibold text-slate-400 uppercase tracking-wider">Officer</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/[0.04]">
                      <AnimatePresence>
                        {filteredAlerts.length > 0 ? (
                          filteredAlerts.map((alert, i) => (
                            <motion.tr 
                              key={alert.id + i}
                              initial={{ opacity: 0, y: 10 }}
                              animate={{ opacity: 1, y: 0 }}
                              exit={{ opacity: 0, scale: 0.95 }}
                              transition={{ duration: 0.2, delay: i * 0.05 }}
                              className={`group hover:bg-blue-500/[0.03] transition-colors ${alert.status === 'RESOLVED' ? 'opacity-60' : ''}`}
                              data-testid="table-row-alert"
                            >
                              <td className="py-3 px-5">{getSeverityBadge(alert.severity)}</td>
                              <td className={`py-3 px-5 text-sm font-medium ${alert.status === 'RESOLVED' ? 'line-through text-slate-500' : 'text-slate-200'}`}>{alert.id}</td>
                              <td className={`py-3 px-5 text-sm ${alert.status === 'RESOLVED' ? 'line-through text-slate-500' : 'text-slate-300'}`}>{alert.zone}</td>
                              <td className={`py-3 px-5 text-sm ${alert.status === 'RESOLVED' ? 'line-through text-slate-500' : 'text-slate-300'}`}>{alert.type}</td>
                              <td className={`py-3 px-5 text-sm ${alert.status === 'RESOLVED' ? 'text-slate-500' : 'text-slate-400'}`}>{alert.time}</td>
                              <td className="py-3 px-5">
                                <span className={`text-xs font-bold tracking-wider ${alert.status === 'ACTIVE' ? 'text-green-400' : 'text-slate-500'}`}>
                                  {alert.status}
                                </span>
                              </td>
                              <td className={`py-3 px-5 text-sm ${alert.status === 'RESOLVED' ? 'text-slate-500' : 'text-slate-300'}`}>{alert.officer}</td>
                            </motion.tr>
                          ))
                        ) : (
                          <tr>
                            <td colSpan={7} className="py-12 text-center text-slate-500">
                              No alerts matching filters.
                            </td>
                          </tr>
                        )}
                      </AnimatePresence>
                    </tbody>
                  </table>
                </div>
              </motion.div>

              {/* Right Column: Timeline (30%) */}
              <motion.div variants={itemVariants} className="lg:col-span-3 bg-white/[0.04] backdrop-blur-xl border border-white/[0.07] rounded-2xl flex flex-col overflow-hidden">
                <div className="p-5 border-b border-white/[0.08] bg-white/[0.02]">
                  <h2 className="text-base font-bold tracking-wide flex items-center gap-2 text-slate-200">
                    <Activity size={18} className="text-blue-400" />
                    Recent Activity
                  </h2>
                </div>
                <div className="flex-1 overflow-y-auto p-5 custom-scrollbar relative">
                  {/* Timeline vertical line */}
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
                          <p className="text-[11px] font-bold text-slate-500 mb-0.5">{item.time}</p>
                          <p className="text-sm text-slate-300 leading-snug">{item.text}</p>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </div>
              </motion.div>

            </div>

            {/* Bottom Mini-Map */}
            <motion.div variants={itemVariants} className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.07] rounded-2xl p-5 flex flex-col h-[280px]">
              <h2 className="text-sm font-bold tracking-wide text-slate-200 mb-4">ALERT HOTSPOT MAP — BANGALORE CITY</h2>
              <div className="flex-1 bg-[#060D1A] rounded-xl border border-white/5 relative overflow-hidden">
                <div className="absolute inset-0 opacity-[0.03]" style={{ backgroundImage: 'linear-gradient(rgba(255,255,255,1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,1) 1px, transparent 1px)', backgroundSize: '40px 40px' }} />
                
                <svg className="absolute inset-0 w-full h-full" viewBox="0 0 800 200" preserveAspectRatio="xMidYMid slice">
                  {/* Simplified Roads */}
                  <path d="M 50,0 C 120,80 200,100 400,120 C 600,140 700,180 800,200" fill="none" stroke="#1E293B" strokeWidth="6" />
                  <path d="M 0,100 C 150,110 300,90 400,120 C 450,140 500,200 550,200" fill="none" stroke="#1E293B" strokeWidth="10" />
                  <path d="M 300,0 L 400,120 L 500,0" fill="none" stroke="#1E293B" strokeWidth="4" />
                  <path d="M 600,0 C 580,50 650,100 750,120 L 800,130" fill="none" stroke="#1E293B" strokeWidth="4" />
                  
                  {/* City Center - Critical */}
                  <g transform="translate(400, 120)">
                    <circle r="40" fill="#ef4444" opacity="0.1">
                      <animate attributeName="r" values="20;50;20" dur="2s" repeatCount="indefinite" />
                      <animate attributeName="opacity" values="0.2;0;0.2" dur="2s" repeatCount="indefinite" />
                    </circle>
                    <circle r="20" fill="#ef4444" opacity="0.3" />
                    <circle r="6" fill="#ef4444" className="drop-shadow-[0_0_10px_rgba(239,68,68,1)]" />
                    <text x="15" y="-10" fill="white" fontSize="12" fontWeight="bold" className="drop-shadow-md">City Center</text>
                  </g>
                  
                  {/* Bus Stand - High */}
                  <g transform="translate(200, 100)">
                    <circle r="30" fill="#f97316" opacity="0.1">
                      <animate attributeName="r" values="15;35;15" dur="3s" repeatCount="indefinite" />
                      <animate attributeName="opacity" values="0.2;0;0.2" dur="3s" repeatCount="indefinite" />
                    </circle>
                    <circle r="15" fill="#f97316" opacity="0.3" />
                    <circle r="5" fill="#f97316" className="drop-shadow-[0_0_10px_rgba(249,115,22,1)]" />
                    <text x="12" y="-8" fill="white" fontSize="11" fontWeight="bold">Bus Stand</text>
                  </g>
                  
                  {/* Railway Station - High */}
                  <g transform="translate(620, 80)">
                    <circle r="45" fill="#f97316" opacity="0.1">
                      <animate attributeName="r" values="25;55;25" dur="1.5s" repeatCount="indefinite" />
                      <animate attributeName="opacity" values="0.3;0;0.3" dur="1.5s" repeatCount="indefinite" />
                    </circle>
                    <circle r="25" fill="#f97316" opacity="0.4" />
                    <circle r="6" fill="#f97316" className="drop-shadow-[0_0_10px_rgba(249,115,22,1)]" />
                    <text x="15" y="-10" fill="white" fontSize="12" fontWeight="bold">Railway Station</text>
                  </g>
                  
                  {/* Market Road - Medium */}
                  <g transform="translate(480, 40)">
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

          </motion.div>
        </main>
      </div>
    </div>
  );
}