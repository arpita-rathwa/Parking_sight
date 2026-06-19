import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Globe, LayoutDashboard, AlertTriangle, BarChart2, Camera as CameraIcon, Settings, Radio, BrainCircuit,
  Search, Bell, Activity, Target, Zap, HardDrive, Filter, 
  WifiOff, Wrench, Info, Eye, CameraOff, ChevronLeft, ChevronRight,
  MapPin
} from 'lucide-react';
import { useLocation } from 'wouter';
import { FloatingLights } from '@/components/CinematicBackground';

function AnimatedCounter({ value, duration = 2 }: { value: number; duration?: number }) {
  const [count, setCount] = useState(0);

  useEffect(() => {
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

const cameraData = [
  { id: 'CAM-001', zone: 'Railway Station', status: 'ONLINE', health: 98, detections: 142, coords: '12.9781° N, 77.5695° E', installed: 'Jan 10, 2024' },
  { id: 'CAM-002', zone: 'Railway Station', status: 'ONLINE', health: 95, detections: 138, coords: '12.9784° N, 77.5702° E', installed: 'Jan 10, 2024' },
  { id: 'CAM-003', zone: 'Bus Stand', status: 'ONLINE', health: 97, detections: 96, coords: '12.9796° N, 77.5732° E', installed: 'Feb 05, 2024' },
  { id: 'CAM-004', zone: 'Bus Stand', status: 'ONLINE', health: 91, detections: 87, coords: '12.9801° N, 77.5738° E', installed: 'Feb 05, 2024' },
  { id: 'CAM-005', zone: 'City Center', status: 'ONLINE', health: 99, detections: 203, coords: '12.9716° N, 77.5946° E', installed: 'Jan 15, 2024' },
  { id: 'CAM-006', zone: 'City Center', status: 'ONLINE', health: 88, detections: 167, coords: '12.9721° N, 77.5939° E', installed: 'Jan 15, 2024' },
  { id: 'CAM-007', zone: 'Market Road', status: 'ONLINE', health: 93, detections: 54, coords: '12.9654° N, 77.5841° E', installed: 'Mar 12, 2024' },
  { id: 'CAM-008', zone: 'City Center', status: 'OFFLINE', health: 0, detections: 0, coords: '12.9730° N, 77.5952° E', installed: 'Jan 15, 2024' },
  { id: 'CAM-009', zone: 'Hospital Circle', status: 'MAINTENANCE', health: 45, detections: 12, coords: '12.9845° N, 77.5896° E', installed: 'Apr 02, 2024' },
  { id: 'CAM-010', zone: 'Market Road', status: 'ONLINE', health: 96, detections: 78, coords: '12.9660° N, 77.5855° E', installed: 'Mar 12, 2024' },
];

const detectionEvents = [
  { time: '10:41 AM', violation: 'Illegal Parking', confidence: 96, color: 'red' },
  { time: '10:39 AM', violation: 'Lane Blocking', confidence: 92, color: 'orange' },
  { time: '10:34 AM', violation: 'Double Parking', confidence: 88, color: 'amber' },
  { time: '10:28 AM', violation: 'Illegal Parking', confidence: 95, color: 'red' },
  { time: '10:22 AM', violation: 'Wrong Parking', confidence: 79, color: 'blue' },
];

export default function Cameras() {
  const [collapsed, setCollapsed] = useState(false);
  const [, setLocation] = useLocation();
  const [searchTerm, setSearchTerm] = useState('');
  const [zoneFilter, setZoneFilter] = useState('All');
  const [statusFilter, setStatusFilter] = useState('All');
  const [selectedCameraId, setSelectedCameraId] = useState('CAM-008');

  const filteredCameras = cameraData.filter(cam => {
    const matchesSearch = cam.id.toLowerCase().includes(searchTerm.toLowerCase()) || cam.zone.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesZone = zoneFilter === 'All' || cam.zone === zoneFilter;
    const matchesStatus = statusFilter === 'All' || cam.status === statusFilter.toUpperCase();
    return matchesSearch && matchesZone && matchesStatus;
  });

  const selectedCamera = cameraData.find(c => c.id === selectedCameraId) || cameraData[0];

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

  const kpis = [
    { title: 'Online Cameras', value: 62, icon: CameraIcon, color: 'text-green-400', bg: 'bg-green-500/10', trend: 'All operational' },
    { title: 'Offline Cameras', value: 3, icon: CameraOff, color: 'text-red-400', bg: 'bg-red-500/10', trend: '↑ 1 since yesterday' },
    { title: 'Frames Processed', value: 1.8, suffix: 'M', icon: Activity, color: 'text-blue-400', bg: 'bg-blue-500/10', trend: '+0.2M today', isFloat: true },
    { title: 'Detection Accuracy', value: 94, suffix: '%', icon: Target, color: 'text-cyan-400', bg: 'bg-cyan-500/10', trend: '↑ 0.5%' },
    { title: 'Average Latency', value: 0.8, suffix: ' sec', icon: Zap, color: 'text-purple-400', bg: 'bg-purple-500/10', trend: 'Stable', isFloat: true },
    { title: 'Storage Used', value: 72, suffix: '%', icon: HardDrive, color: 'text-amber-400', bg: 'bg-amber-500/10', trend: '↑ 3% today' },
  ];

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
            { icon: CameraIcon, label: 'Cameras', active: true, path: '/cameras' },
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
                  Camera Network
                </h1>
                <p className="text-slate-400 text-sm font-medium">Monitor city-wide surveillance infrastructure and traffic activity.</p>
              </div>
              <div className="flex items-center gap-2 bg-white/5 border border-white/10 px-4 py-2 rounded-xl shadow-[inset_0_2px_10px_rgba(0,0,0,0.2)]">
                <div className="w-2.5 h-2.5 rounded-full bg-green-500 animate-pulse shadow-[0_0_10px_rgba(34,197,94,0.8)]" />
                <span className="text-sm font-bold text-green-400 tracking-wide">62 Cameras Online</span>
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
                  <div className="mt-2 relative z-10">
                    <p className="text-3xl font-black tracking-tight text-white drop-shadow-md">
                      <AnimatedCounter value={stat.value} />
                      {stat.suffix && <span className="text-sm font-medium text-slate-500 ml-1">{stat.suffix}</span>}
                    </p>
                    <h3 className="text-slate-400 text-[11px] font-bold uppercase tracking-wider mt-1">{stat.title}</h3>
                  </div>
                </motion.div>
              ))}
            </div>

            {/* Three-Column Layout */}
            <div className="grid grid-cols-1 lg:grid-cols-10 gap-6">
              
              {/* Left Column (30%) - Camera Grid */}
              <motion.div variants={itemVariants} className="lg:col-span-3 flex flex-col gap-4">
                <div className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.07] rounded-2xl p-4 flex flex-col h-[600px]">
                  <div className="flex justify-between items-center mb-4">
                    <h2 className="text-sm font-bold tracking-wide flex items-center gap-2 text-slate-200">
                      <Filter size={16} className="text-blue-400" />
                      CAMERA GRID
                    </h2>
                  </div>
                  
                  {/* Filters */}
                  <div className="space-y-3 mb-4">
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 w-4 h-4" />
                      <input 
                        type="text" 
                        placeholder="Search cameras..." 
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full bg-white/5 border border-white/10 rounded-lg py-1.5 pl-9 pr-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500/50 transition-colors"
                      />
                    </div>
                    <div className="flex gap-2">
                      <select 
                        value={zoneFilter}
                        onChange={(e) => setZoneFilter(e.target.value)}
                        className="flex-1 bg-white/5 border border-white/10 rounded-lg py-1.5 px-2 text-xs text-slate-300 focus:outline-none focus:border-blue-500/50 transition-colors appearance-none"
                      >
                        <option value="All">All Zones</option>
                        <option value="Railway Station">Railway Station</option>
                        <option value="Bus Stand">Bus Stand</option>
                        <option value="Market Road">Market Road</option>
                        <option value="City Center">City Center</option>
                        <option value="Hospital Circle">Hospital Circle</option>
                      </select>
                      <select 
                        value={statusFilter}
                        onChange={(e) => setStatusFilter(e.target.value)}
                        className="w-24 bg-white/5 border border-white/10 rounded-lg py-1.5 px-2 text-xs text-slate-300 focus:outline-none focus:border-blue-500/50 transition-colors appearance-none"
                      >
                        <option value="All">Status</option>
                        <option value="Online">Online</option>
                        <option value="Offline">Offline</option>
                        <option value="Maintenance">Maint.</option>
                      </select>
                    </div>
                  </div>

                  {/* List */}
                  <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar space-y-2">
                    {filteredCameras.map((cam) => {
                      const isOnline = cam.status === 'ONLINE';
                      const isOffline = cam.status === 'OFFLINE';
                      const isSelected = selectedCameraId === cam.id;
                      
                      return (
                        <div 
                          key={cam.id}
                          onClick={() => setSelectedCameraId(cam.id)}
                          className={`flex items-center gap-3 p-2 rounded-xl cursor-pointer transition-all duration-200
                            ${isSelected 
                              ? 'bg-blue-500/10 border border-blue-500/50 shadow-[0_0_15px_rgba(59,130,246,0.15)]' 
                              : 'bg-white/5 border border-white/5 hover:bg-white/10 hover:border-white/10'}
                          `}
                        >
                          <div className="relative w-12 h-12 rounded-lg overflow-hidden bg-gradient-to-br from-slate-800 to-slate-900 border border-white/10 flex-shrink-0 flex items-center justify-center">
                            {isOnline ? <CameraIcon size={16} className="text-slate-600" /> : 
                             isOffline ? <CameraOff size={16} className="text-red-500/50" /> : 
                             <Wrench size={16} className="text-orange-500/50" />}
                            <div className={`absolute top-1 right-1 w-2 h-2 rounded-full 
                              ${isOnline ? 'bg-green-500 shadow-[0_0_5px_rgba(34,197,94,0.8)]' : 
                                isOffline ? 'bg-red-500' : 'bg-orange-500'}
                            `} />
                          </div>
                          
                          <div className="flex-1 min-w-0">
                            <div className="flex justify-between items-start mb-1">
                              <span className={`text-xs font-bold ${isSelected ? 'text-blue-400' : 'text-slate-200'}`}>{cam.id}</span>
                              <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border
                                ${isOnline ? 'bg-green-500/10 border-green-500/20 text-green-400' : 
                                  isOffline ? 'bg-red-500/10 border-red-500/20 text-red-400' : 
                                  'bg-orange-500/10 border-orange-500/20 text-orange-400'}
                              `}>
                                {cam.status}
                              </span>
                            </div>
                            <div className="text-[10px] text-slate-400 truncate mb-1">{cam.zone}</div>
                            <div className="flex items-center gap-3 text-[9px] text-slate-500 font-medium">
                              <span className="flex items-center gap-1"><Target size={10} /> {cam.health}%</span>
                              <span className="flex items-center gap-1"><Activity size={10} /> {cam.detections} det</span>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </motion.div>

              {/* Center Column (40%) - Feed Viewer */}
              <motion.div variants={itemVariants} className="lg:col-span-4 flex flex-col h-[600px]">
                <div className="bg-[#060D1A] rounded-2xl border border-white/10 flex-1 relative overflow-hidden shadow-2xl flex flex-col">
                  {/* Grid Overlay */}
                  <div className="absolute inset-0 opacity-5 pointer-events-none" style={{ backgroundImage: 'linear-gradient(rgba(255,255,255,1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,1) 1px, transparent 1px)', backgroundSize: '40px 40px' }} />
                  
                  {/* Brackets */}
                  <div className="absolute top-4 left-4 w-8 h-8 border-t-2 border-l-2 border-green-500/30 rounded-tl pointer-events-none" />
                  <div className="absolute top-4 right-4 w-8 h-8 border-t-2 border-r-2 border-green-500/30 rounded-tr pointer-events-none" />
                  <div className="absolute bottom-4 left-4 w-8 h-8 border-b-2 border-l-2 border-green-500/30 rounded-bl pointer-events-none" />
                  <div className="absolute bottom-4 right-4 w-8 h-8 border-b-2 border-r-2 border-green-500/30 rounded-br pointer-events-none" />

                  {/* Top Bar Overlay */}
                  <div className="absolute top-0 left-0 right-0 bg-black/60 backdrop-blur-sm p-3 flex justify-between items-center z-10 border-b border-white/5">
                    <div className="flex items-center gap-3">
                      {selectedCamera.status === 'ONLINE' && (
                        <div className="flex items-center gap-1.5 text-[10px] font-bold text-red-500 tracking-widest bg-red-500/10 px-2 py-0.5 rounded border border-red-500/20">
                          <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" /> REC
                        </div>
                      )}
                      <span className="font-mono text-sm font-bold text-white drop-shadow-md">{selectedCamera.id}</span>
                    </div>
                    <div className="flex items-center gap-4 text-[10px] font-mono text-slate-300 tracking-wider">
                      <span>FPS: {selectedCamera.status === 'ONLINE' ? '30' : '0'}</span>
                      <span>CONGESTION: {selectedCamera.status === 'ONLINE' ? '86' : '--'}</span>
                      <span className="text-white"><LiveClock /></span>
                    </div>
                  </div>

                  {/* Content Area */}
                  <div className="flex-1 relative flex items-center justify-center">
                    <AnimatePresence mode="wait">
                      <motion.div 
                        key={selectedCamera.id}
                        initial={{ opacity: 0, scale: 1.05 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.3 }}
                        className="absolute inset-0 w-full h-full flex items-center justify-center"
                      >
                        {selectedCamera.status === 'ONLINE' ? (
                          <>
                            {/* Fake Detection Boxes */}
                            <motion.div 
                              animate={{ y: [0, -2, 0] }} 
                              transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }}
                              className="absolute top-[30%] left-[20%] w-32 h-24 border-2 border-dashed border-green-500/80 bg-green-500/5 shadow-[0_0_15px_rgba(34,197,94,0.2)]"
                            >
                              <div className="absolute -top-6 left-[-2px] bg-green-500 text-black text-[9px] font-bold px-1.5 py-0.5 whitespace-nowrap">CAR 95%</div>
                            </motion.div>
                            
                            <motion.div 
                              animate={{ y: [0, 3, 0] }} 
                              transition={{ repeat: Infinity, duration: 2.5, ease: "easeInOut" }}
                              className="absolute top-[45%] right-[25%] w-48 h-32 border-2 border-dashed border-blue-500/80 bg-blue-500/5 shadow-[0_0_15px_rgba(59,130,246,0.2)]"
                            >
                              <div className="absolute -top-6 left-[-2px] bg-blue-500 text-white text-[9px] font-bold px-1.5 py-0.5 whitespace-nowrap">BUS 91%</div>
                            </motion.div>

                            <motion.div 
                              animate={{ y: [0, 1, 0] }} 
                              transition={{ repeat: Infinity, duration: 1.5, ease: "easeInOut" }}
                              className="absolute bottom-[20%] left-[40%] w-20 h-20 border-2 border-dashed border-purple-500/80 bg-purple-500/5 shadow-[0_0_15px_rgba(168,85,247,0.2)]"
                            >
                              <div className="absolute -top-6 left-[-2px] bg-purple-500 text-white text-[9px] font-bold px-1.5 py-0.5 whitespace-nowrap">BIKE 87%</div>
                            </motion.div>
                          </>
                        ) : selectedCamera.status === 'OFFLINE' ? (
                          <div className="flex flex-col items-center gap-3 text-red-500/80 drop-shadow-[0_0_10px_rgba(239,68,68,0.5)]">
                            <WifiOff size={48} />
                            <span className="font-mono text-xl font-bold tracking-widest">SIGNAL LOST</span>
                          </div>
                        ) : (
                          <div className="flex flex-col items-center gap-3 text-orange-500/80 drop-shadow-[0_0_10px_rgba(249,115,22,0.5)]">
                            <Wrench size={48} />
                            <span className="font-mono text-xl font-bold tracking-widest">UNDER MAINTENANCE</span>
                          </div>
                        )}
                      </motion.div>
                    </AnimatePresence>
                  </div>

                  {/* Bottom Bar Overlay */}
                  <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4 flex justify-between items-end z-10">
                    <div className="text-white drop-shadow-md">
                      <div className="text-lg font-bold tracking-wide">{selectedCamera.zone}</div>
                      <div className="text-[10px] font-mono text-slate-400 tracking-widest">{selectedCamera.coords}</div>
                    </div>
                    {selectedCamera.status === 'ONLINE' && (
                      <div className="w-48 h-12">
                        {/* Fake mini waveform */}
                        <div className="flex items-end justify-between h-full gap-0.5 opacity-50">
                          {Array.from({ length: 20 }).map((_, i) => (
                            <motion.div 
                              key={i} 
                              className="w-full bg-green-500 rounded-t-sm"
                              animate={{ height: [`${20 + Math.random() * 80}%`, `${20 + Math.random() * 80}%`] }}
                              transition={{ repeat: Infinity, duration: 0.5 + Math.random(), ease: "linear" }}
                            />
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </motion.div>

              {/* Right Column (30%) - Info & Events */}
              <motion.div variants={itemVariants} className="lg:col-span-3 flex flex-col gap-6 h-[600px]">
                
                {/* Camera Details */}
                <div className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.07] rounded-2xl p-5 flex flex-col">
                  <h2 className="text-sm font-bold tracking-wide flex items-center gap-2 text-slate-200 mb-4">
                    <Info size={16} className="text-cyan-400" />
                    CAMERA DETAILS
                  </h2>
                  <div className="space-y-3 text-sm">
                    <div className="flex justify-between py-1.5 border-b border-white/5">
                      <span className="text-slate-400">Name</span>
                      <span className="font-medium text-slate-200">{selectedCamera.id} — {selectedCamera.zone}</span>
                    </div>
                    <div className="flex justify-between py-1.5 border-b border-white/5">
                      <span className="text-slate-400">Coordinates</span>
                      <span className="font-mono text-xs text-slate-300">{selectedCamera.coords}</span>
                    </div>
                    <div className="flex justify-between py-1.5 border-b border-white/5">
                      <span className="text-slate-400">Installed</span>
                      <span className="font-medium text-slate-200">{selectedCamera.installed}</span>
                    </div>
                    <div className="flex justify-between py-1.5 border-b border-white/5">
                      <span className="text-slate-400">Resolution</span>
                      <span className="font-mono text-xs text-slate-300">1920 × 1080</span>
                    </div>
                    <div className="flex justify-between py-1.5 border-b border-white/5">
                      <span className="text-slate-400">Network</span>
                      <div className="flex items-end gap-0.5 h-3">
                        <div className={`w-1.5 h-1.5 ${selectedCamera.status === 'ONLINE' ? 'bg-green-500' : 'bg-slate-600'}`} />
                        <div className={`w-1.5 h-2 ${selectedCamera.status === 'ONLINE' ? 'bg-green-500' : 'bg-slate-600'}`} />
                        <div className={`w-1.5 h-3 ${selectedCamera.status === 'ONLINE' ? 'bg-green-500' : 'bg-slate-600'}`} />
                      </div>
                    </div>
                    <div className="flex justify-between py-1.5 items-center">
                      <span className="text-slate-400">Storage</span>
                      <div className="flex flex-col items-end gap-1 w-32">
                        <span className="text-[10px] text-slate-300">28 GB of 100 GB</span>
                        <div className="w-full h-1.5 bg-white/10 rounded-full overflow-hidden">
                          <div className="h-full bg-blue-500 w-[28%]" />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Detection Events */}
                <div className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.07] rounded-2xl p-5 flex flex-col flex-1 overflow-hidden">
                  <h2 className="text-sm font-bold tracking-wide flex items-center gap-2 text-slate-200 mb-4">
                    <Eye size={16} className="text-purple-400" />
                    DETECTION EVENTS
                  </h2>
                  <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
                    {selectedCamera.status === 'ONLINE' ? (
                      <div className="space-y-4 relative before:absolute before:inset-0 before:ml-[11px] before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-white/10 before:to-transparent">
                        {detectionEvents.map((event, i) => (
                          <motion.div 
                            key={i}
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: i * 0.1 }}
                            className="relative flex items-start pl-8 group"
                          >
                            <div className={`absolute left-0 top-1.5 w-6 h-6 rounded-full bg-white/5 border border-white/10 flex items-center justify-center z-10 group-hover:bg-${event.color}-500/20 group-hover:border-${event.color}-500/50 transition-colors`}>
                              <div className={`w-2 h-2 rounded-full bg-${event.color}-500`} />
                            </div>
                            <div className="bg-white/5 border border-white/5 rounded-xl p-3 flex-1 group-hover:bg-white/10 transition-colors">
                              <div className="flex justify-between items-start mb-1">
                                <span className="text-xs font-bold text-slate-200">{event.violation}</span>
                                <span className="text-[10px] text-slate-400 font-mono">{event.time}</span>
                              </div>
                              <div className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-bold tracking-wider
                                bg-${event.color}-500/10 text-${event.color}-400 border border-${event.color}-500/20
                              `}>
                                CONFIDENCE {event.confidence}%
                              </div>
                            </div>
                          </motion.div>
                        ))}
                      </div>
                    ) : (
                      <div className="h-full flex items-center justify-center text-slate-500 text-sm font-medium italic">
                        No events — camera offline
                      </div>
                    )}
                  </div>
                </div>

              </motion.div>

            </div>

            {/* Bottom Section - Camera Health Map */}
            <motion.div variants={itemVariants} className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.07] rounded-2xl p-5 flex flex-col h-[340px] relative overflow-hidden group hover:border-white/10 transition-colors">
              <div className="flex justify-between items-center mb-4 relative z-10">
                <h2 className="text-sm font-bold tracking-wide flex items-center gap-2 text-slate-200">
                  <MapPin size={16} className="text-blue-400" />
                  CAMERA NETWORK MAP — BANGALORE CITY
                </h2>
                <div className="flex gap-4 text-xs font-medium bg-black/40 px-3 py-1.5 rounded-lg border border-white/5">
                  <span className="flex items-center gap-1.5 text-slate-300"><span className="w-2 h-2 rounded-full bg-green-500" /> Online</span>
                  <span className="flex items-center gap-1.5 text-slate-300"><span className="w-2 h-2 rounded-full bg-red-500" /> Offline</span>
                  <span className="flex items-center gap-1.5 text-slate-300"><span className="w-2 h-2 rounded-full bg-orange-500" /> Maintenance</span>
                </div>
              </div>
              
              <div className="flex-1 bg-[#060D1A] rounded-xl border border-white/5 relative overflow-hidden">
                <div className="absolute inset-0 opacity-[0.03]" style={{ backgroundImage: 'linear-gradient(rgba(255,255,255,1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,1) 1px, transparent 1px)', backgroundSize: '40px 40px' }} />
                
                <svg className="absolute inset-0 w-full h-full" viewBox="0 0 1000 280" preserveAspectRatio="xMidYMid slice">
                  {/* Roads */}
                  <path d="M 50,0 C 100,100 300,150 500,150 C 700,150 900,200 1000,250" fill="none" stroke="#1E293B" strokeWidth="6" />
                  <path d="M 0,100 C 200,120 400,80 600,180 C 700,220 800,280 900,280" fill="none" stroke="#1E293B" strokeWidth="8" />
                  <path d="M 300,0 L 400,150 L 600,0" fill="none" stroke="#1E293B" strokeWidth="4" />
                  <path d="M 700,0 C 650,80 750,150 850,200 L 950,220" fill="none" stroke="#1E293B" strokeWidth="5" />
                  
                  {/* Camera Pins */}
                  {[
                    { id: 'CAM-001', x: 750, y: 120, status: 'ONLINE' },
                    { id: 'CAM-002', x: 780, y: 140, status: 'ONLINE' },
                    { id: 'CAM-003', x: 350, y: 130, status: 'ONLINE' },
                    { id: 'CAM-004', x: 380, y: 160, status: 'ONLINE' },
                    { id: 'CAM-005', x: 500, y: 150, status: 'ONLINE' },
                    { id: 'CAM-006', x: 540, y: 170, status: 'ONLINE' },
                    { id: 'CAM-007', x: 600, y: 60, status: 'ONLINE' },
                    { id: 'CAM-008', x: 460, y: 130, status: 'OFFLINE' },
                    { id: 'CAM-009', x: 200, y: 110, status: 'MAINTENANCE' },
                    { id: 'CAM-010', x: 640, y: 80, status: 'ONLINE' },
                  ].map((pin, i) => (
                    <g key={i} transform={`translate(${pin.x}, ${pin.y})`} className="cursor-pointer" onClick={() => setSelectedCameraId(pin.id)}>
                      {pin.status === 'ONLINE' && (
                        <circle r="12" fill="#22c55e" opacity="0.2">
                          <animate attributeName="r" values="6;16;6" dur="2s" repeatCount="indefinite" />
                          <animate attributeName="opacity" values="0.4;0;0.4" dur="2s" repeatCount="indefinite" />
                        </circle>
                      )}
                      {pin.status === 'MAINTENANCE' && (
                        <circle r="12" fill="#f97316" opacity="0.2">
                          <animate attributeName="r" values="6;14;6" dur="3s" repeatCount="indefinite" />
                        </circle>
                      )}
                      <circle r="5" fill={pin.status === 'ONLINE' ? '#22c55e' : pin.status === 'OFFLINE' ? '#ef4444' : '#f97316'} 
                        className={`drop-shadow-[0_0_5px_rgba(${pin.status === 'ONLINE' ? '34,197,94' : pin.status === 'OFFLINE' ? '239,68,68' : '249,115,22'},0.8)]`} 
                      />
                      <rect x="-24" y="-22" width="48" height="14" rx="2" fill="rgba(0,0,0,0.6)" />
                      <text x="0" y="-12" fill="white" fontSize="8" fontWeight="bold" textAnchor="middle" className="font-mono">{pin.id}</text>
                    </g>
                  ))}
                </svg>
              </div>
            </motion.div>

          </motion.div>
        </main>
      </div>
    </div>
  );
}