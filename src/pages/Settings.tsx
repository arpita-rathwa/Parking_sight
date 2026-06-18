import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Globe, LayoutDashboard, AlertTriangle, BarChart2, Camera as CameraIcon, Settings as SettingsIcon, Radio, BrainCircuit,
  Search, Bell, ChevronLeft, ChevronRight, Cpu, Users, Sliders, Link2, Shield, Palette, ScrollText,
  CheckCircle2, XCircle
} from 'lucide-react';
import { useLocation } from 'wouter';
import { FloatingLights } from '@/components/CinematicBackground';

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

function ToggleSwitch({ enabled, onChange }: { enabled: boolean; onChange: () => void }) {
  return (
    <button onClick={onChange} data-testid='toggle'
      className={`relative w-11 h-6 rounded-full transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50 ${enabled ? 'bg-green-500' : 'bg-slate-700'}`}>
      <span className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform duration-200 ${enabled ? 'translate-x-5' : 'translate-x-0'}`} />
    </button>
  );
}

function SettingRow({ label, description, children }: { label: string; description?: string; children: React.ReactNode }) {
  return (
    <div className="flex justify-between items-center py-4 border-b border-white/[0.05] last:border-0">
      <div className="flex flex-col gap-1 pr-4">
        <span className="text-sm font-bold text-slate-200">{label}</span>
        {description && <span className="text-xs text-slate-400">{description}</span>}
      </div>
      <div className="flex-shrink-0">
        {children}
      </div>
    </div>
  );
}

function SectionCard({ title, icon: Icon, children }: { title: string; icon: React.ElementType; children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.07] rounded-2xl p-6"
    >
      <div className="flex items-center gap-3 mb-6 border-b border-white/[0.05] pb-4">
        <div className="p-2 bg-blue-500/10 rounded-lg">
          <Icon className="text-blue-400" size={20} />
        </div>
        <h2 className="text-lg font-bold text-white tracking-wide">{title}</h2>
      </div>
      <div className="space-y-1">
        {children}
      </div>
    </motion.div>
  );
}

const SECTIONS = [
  { id: 'general', label: 'General', icon: SettingsIcon },
  { id: 'notifications', label: 'Notifications', icon: Bell },
  { id: 'ai', label: 'AI Detection', icon: Cpu },
  { id: 'cameras', label: 'Camera Settings', icon: CameraIcon },
  { id: 'officers', label: 'Officer Management', icon: Users },
  { id: 'thresholds', label: 'Thresholds', icon: Sliders },
  { id: 'integrations', label: 'Integrations', icon: Link2 },
  { id: 'security', label: 'Security', icon: Shield },
  { id: 'appearance', label: 'Appearance', icon: Palette },
  { id: 'logs', label: 'System Logs', icon: ScrollText },
];

export default function Settings() {
  const [collapsed, setCollapsed] = useState(false);
  const [, setLocation] = useLocation();
  const [selectedSection, setSelectedSection] = useState('general');

  // Form states
  const [autoSave, setAutoSave] = useState(true);
  
  const [pushNotif, setPushNotif] = useState(true);
  const [emailNotif, setEmailNotif] = useState(true);
  const [criticalOnly, setCriticalOnly] = useState(false);
  const [alertSound, setAlertSound] = useState(true);
  const [desktopNotif, setDesktopNotif] = useState(true);
  const [smsNotif, setSmsNotif] = useState(false);

  const [aiConfidence, setAiConfidence] = useState(90);
  const [autoRetrain, setAutoRetrain] = useState(true);
  const [explainableAi, setExplainableAi] = useState(true);

  const [autoHealth, setAutoHealth] = useState(true);

  const [autoDispatch, setAutoDispatch] = useState(true);
  const [manualApproval, setManualApproval] = useState(false);

  const [hpZone, setHpZone] = useState(80);
  const [critZone, setCritZone] = useState(90);
  const [congThresh, setCongThresh] = useState(75);
  const [emerEscal, setEmerEscal] = useState(95);

  const [mfa, setMfa] = useState(true);
  const [auditLog, setAuditLog] = useState(true);

  const [darkTheme, setDarkTheme] = useState(true);
  const [blueAccent, setBlueAccent] = useState(true);
  const [compactLayout, setCompactLayout] = useState(false);
  const [animations, setAnimations] = useState(true);
  const [glassmorphism, setGlassmorphism] = useState(true);
  const [particles, setParticles] = useState(true);

  const renderSection = () => {
    switch (selectedSection) {
      case 'general':
        return (
          <SectionCard title="General Settings" icon={SettingsIcon}>
            <SettingRow label="Organization Name" description="The official name of your management entity.">
              <input type="text" defaultValue="Smart City Authority" data-testid="input-org" className="w-64 bg-white/[0.06] border border-white/[0.10] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500/50" />
            </SettingRow>
            <SettingRow label="Timezone" description="System-wide time reference for logs and alerts.">
              <select defaultValue="Asia/Kolkata" data-testid="select-timezone" className="w-64 bg-white/[0.06] border border-white/[0.10] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500/50 appearance-none">
                <option value="Asia/Kolkata">Asia/Kolkata</option>
                <option value="UTC">UTC</option>
                <option value="US/Eastern">US/Eastern</option>
              </select>
            </SettingRow>
            <SettingRow label="Language" description="Primary interface language.">
              <select defaultValue="English" data-testid="select-lang" className="w-64 bg-white/[0.06] border border-white/[0.10] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500/50 appearance-none">
                <option value="English">English</option>
                <option value="Hindi">Hindi</option>
                <option value="Kannada">Kannada</option>
              </select>
            </SettingRow>
            <SettingRow label="Theme" description="Default color scheme for new users.">
              <select defaultValue="Dark Mode" data-testid="select-theme" className="w-64 bg-white/[0.06] border border-white/[0.10] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500/50 appearance-none">
                <option value="Dark Mode">Dark Mode</option>
                <option value="Light Mode">Light Mode</option>
                <option value="System">System</option>
              </select>
            </SettingRow>
            <SettingRow label="Auto Save" description="Automatically save changes as they are made.">
              <ToggleSwitch enabled={autoSave} onChange={() => setAutoSave(!autoSave)} />
            </SettingRow>
            <div className="pt-6 flex justify-end">
              <button data-testid="btn-save" className="px-6 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-500 hover:from-blue-500 hover:to-indigo-400 text-white font-bold rounded-lg shadow-[0_0_15px_rgba(59,130,246,0.4)] hover:shadow-[0_0_20px_rgba(59,130,246,0.6)] transition-all">
                Save Changes
              </button>
            </div>
          </SectionCard>
        );
      case 'notifications':
        return (
          <SectionCard title="Notification Preferences" icon={Bell}>
            <SettingRow label="Enable Push Notifications" description="Receive alerts on mobile devices."><ToggleSwitch enabled={pushNotif} onChange={() => setPushNotif(!pushNotif)} /></SettingRow>
            <SettingRow label="Enable Email Alerts" description="Daily digests and critical incident reports."><ToggleSwitch enabled={emailNotif} onChange={() => setEmailNotif(!emailNotif)} /></SettingRow>
            <SettingRow label="Critical Alerts Only" description="Mute warnings and low-priority events."><ToggleSwitch enabled={criticalOnly} onChange={() => setCriticalOnly(!criticalOnly)} /></SettingRow>
            <SettingRow label="Alert Sound" description="Play a sound when a new alert appears."><ToggleSwitch enabled={alertSound} onChange={() => setAlertSound(!alertSound)} /></SettingRow>
            <SettingRow label="Desktop Notifications" description="Show browser-level notifications."><ToggleSwitch enabled={desktopNotif} onChange={() => setDesktopNotif(!desktopNotif)} /></SettingRow>
            <SettingRow label="SMS Alerts" description="Text messages for emergency escalations."><ToggleSwitch enabled={smsNotif} onChange={() => setSmsNotif(!smsNotif)} /></SettingRow>
          </SectionCard>
        );
      case 'ai':
        return (
          <SectionCard title="AI Detection Parameters" icon={Cpu}>
            <SettingRow label="Detection Confidence Threshold" description="Minimum certainty required to trigger an alert.">
              <div className="flex items-center gap-4 w-64">
                <input type="range" min="60" max="100" value={aiConfidence} onChange={(e) => setAiConfidence(Number(e.target.value))} className="w-full accent-blue-500" data-testid="slider-ai" />
                <span className="text-sm font-bold text-blue-400 bg-blue-500/10 px-2 py-1 rounded border border-blue-500/20 shadow-[0_0_8px_rgba(59,130,246,0.5)]">{aiConfidence}%</span>
              </div>
            </SettingRow>
            <SettingRow label="Illegal Parking Sensitivity"><select defaultValue="High" className="w-48 bg-white/[0.06] border border-white/[0.10] rounded-lg px-3 py-2 text-sm text-white appearance-none"><option>Low</option><option>Medium</option><option>High</option></select></SettingRow>
            <SettingRow label="Double Parking Sensitivity"><select defaultValue="Medium" className="w-48 bg-white/[0.06] border border-white/[0.10] rounded-lg px-3 py-2 text-sm text-white appearance-none"><option>Low</option><option>Medium</option><option>High</option></select></SettingRow>
            <SettingRow label="Lane Blocking Sensitivity"><select defaultValue="High" className="w-48 bg-white/[0.06] border border-white/[0.10] rounded-lg px-3 py-2 text-sm text-white appearance-none"><option>Low</option><option>Medium</option><option>High</option></select></SettingRow>
            <SettingRow label="Auto-Retrain Model" description="Periodically improve accuracy using verified data."><ToggleSwitch enabled={autoRetrain} onChange={() => setAutoRetrain(!autoRetrain)} /></SettingRow>
            <SettingRow label="Show Explainable AI Results" description="Overlay bounding boxes and reasons on feeds."><ToggleSwitch enabled={explainableAi} onChange={() => setExplainableAi(!explainableAi)} /></SettingRow>
          </SectionCard>
        );
      case 'cameras':
        return (
          <SectionCard title="Camera Configuration" icon={CameraIcon}>
            <SettingRow label="Frame Capture Rate"><select defaultValue="5 seconds" className="w-48 bg-white/[0.06] border border-white/[0.10] rounded-lg px-3 py-2 text-sm text-white appearance-none"><option>1 second</option><option>5 seconds</option><option>10 seconds</option><option>30 seconds</option></select></SettingRow>
            <SettingRow label="Video Quality"><select defaultValue="1080p" className="w-48 bg-white/[0.06] border border-white/[0.10] rounded-lg px-3 py-2 text-sm text-white appearance-none"><option>720p</option><option>1080p</option><option>4K</option></select></SettingRow>
            <SettingRow label="Storage Retention"><select defaultValue="30 Days" className="w-48 bg-white/[0.06] border border-white/[0.10] rounded-lg px-3 py-2 text-sm text-white appearance-none"><option>7 Days</option><option>14 Days</option><option>30 Days</option><option>90 Days</option></select></SettingRow>
            <SettingRow label="Auto Health Check" description="Ping cameras every minute for uptime."><ToggleSwitch enabled={autoHealth} onChange={() => setAutoHealth(!autoHealth)} /></SettingRow>
            <SettingRow label="Offline Alert Delay" description="Wait before marking as disconnected."><select defaultValue="60 Seconds" className="w-48 bg-white/[0.06] border border-white/[0.10] rounded-lg px-3 py-2 text-sm text-white appearance-none"><option>30 Seconds</option><option>60 Seconds</option><option>5 Minutes</option></select></SettingRow>
          </SectionCard>
        );
      case 'officers':
        return (
          <SectionCard title="Officer Management" icon={Users}>
            <SettingRow label="Active Officers" description="Currently on-duty personnel."><div className="text-xl font-black text-white bg-white/5 px-4 py-1 rounded-lg border border-white/10">12</div></SettingRow>
            <SettingRow label="Max Assignments Per Officer" description="Limit concurrent active cases."><input type="number" defaultValue={5} className="w-24 bg-white/[0.06] border border-white/[0.10] rounded-lg px-3 py-2 text-sm text-white appearance-none" /></SettingRow>
            <SettingRow label="Auto Dispatch" description="Automatically assign nearest officer to high-priority alerts."><ToggleSwitch enabled={autoDispatch} onChange={() => setAutoDispatch(!autoDispatch)} /></SettingRow>
            <SettingRow label="Manual Approval Required" description="Dispatcher must approve AI assignments."><ToggleSwitch enabled={manualApproval} onChange={() => setManualApproval(!manualApproval)} /></SettingRow>
            <SettingRow label="Response Timeout" description="Mark assignment as missed after."><select defaultValue="15 Minutes" className="w-48 bg-white/[0.06] border border-white/[0.10] rounded-lg px-3 py-2 text-sm text-white appearance-none"><option>5 Minutes</option><option>10 Minutes</option><option>15 Minutes</option><option>30 Minutes</option></select></SettingRow>
          </SectionCard>
        );
      case 'thresholds':
        return (
          <SectionCard title="Alert Thresholds" icon={Sliders}>
            {[
              { label: 'High Priority Zone Score', val: hpZone, set: setHpZone, color: 'amber' },
              { label: 'Critical Zone Score', val: critZone, set: setCritZone, color: 'red' },
              { label: 'Congestion Threshold', val: congThresh, set: setCongThresh, color: 'orange' },
              { label: 'Emergency Escalation', val: emerEscal, set: setEmerEscal, color: 'red' }
            ].map((t, i) => (
              <SettingRow key={i} label={t.label}>
                <div className="flex items-center gap-4 w-64">
                  <input type="range" min="0" max="100" value={t.val} onChange={(e) => t.set(Number(e.target.value))} className={`w-full accent-${t.color}-500`} />
                  <span className={`text-sm font-bold text-${t.color}-400 bg-${t.color}-500/10 px-2 py-1 rounded border border-${t.color}-500/20 shadow-[0_0_8px_var(--tw-shadow-color)] shadow-${t.color}-500/50 min-w-[3rem] text-center`}>{t.val}</span>
                </div>
              </SettingRow>
            ))}
          </SectionCard>
        );
      case 'integrations':
        return (
          <SectionCard title="External Integrations" icon={Link2}>
            {[
              { name: 'Google Maps API', connected: true, color: 'bg-blue-500' },
              { name: 'Firebase Notifications', connected: true, color: 'bg-amber-500' },
              { name: 'AWS S3 Storage', connected: true, color: 'bg-orange-500' },
              { name: 'Kafka Streaming', connected: true, color: 'bg-slate-800' },
              { name: 'PostgreSQL Database', connected: true, color: 'bg-indigo-500' },
              { name: 'Redis Cache', connected: false, color: 'bg-red-500' },
            ].map((int, i) => (
              <div key={i} className="flex justify-between items-center py-4 border-b border-white/[0.05] last:border-0">
                <div className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-white font-bold ${int.color}`}>
                    {int.name.charAt(0)}
                  </div>
                  <span className="text-sm font-bold text-slate-200">{int.name}</span>
                </div>
                <div className="flex items-center gap-4">
                  {int.connected ? (
                    <div className="flex items-center gap-1.5 text-xs font-bold text-green-400 bg-green-500/10 px-2.5 py-1 rounded border border-green-500/20">
                      <CheckCircle2 size={14} /> Connected
                    </div>
                  ) : (
                    <div className="flex items-center gap-1.5 text-xs font-bold text-red-400 bg-red-500/10 px-2.5 py-1 rounded border border-red-500/20">
                      <XCircle size={14} /> Disconnected
                    </div>
                  )}
                  <button className="text-xs font-bold px-3 py-1.5 rounded-md border border-white/20 hover:border-blue-500 hover:text-blue-400 transition-colors">
                    Configure
                  </button>
                </div>
              </div>
            ))}
          </SectionCard>
        );
      case 'security':
        return (
          <SectionCard title="Security Settings" icon={Shield}>
            <SettingRow label="Multi-Factor Authentication" description="Require 2FA for all admin accounts."><ToggleSwitch enabled={mfa} onChange={() => setMfa(!mfa)} /></SettingRow>
            <SettingRow label="JWT Expiration"><select defaultValue="15 Minutes" className="w-48 bg-white/[0.06] border border-white/[0.10] rounded-lg px-3 py-2 text-sm text-white appearance-none"><option>5 Minutes</option><option>15 Minutes</option><option>1 Hour</option><option>24 Hours</option></select></SettingRow>
            <SettingRow label="Password Policy"><select defaultValue="Strong" className="w-48 bg-white/[0.06] border border-white/[0.10] rounded-lg px-3 py-2 text-sm text-white appearance-none"><option>Basic</option><option>Strong</option><option>Very Strong</option></select></SettingRow>
            <SettingRow label="Audit Logging" description="Record all settings changes."><ToggleSwitch enabled={auditLog} onChange={() => setAuditLog(!auditLog)} /></SettingRow>
            <SettingRow label="API Key Rotation"><select defaultValue="Automatic" className="w-48 bg-white/[0.06] border border-white/[0.10] rounded-lg px-3 py-2 text-sm text-white appearance-none"><option>Manual</option><option>Automatic</option><option>Weekly</option></select></SettingRow>
          </SectionCard>
        );
      case 'appearance':
        return (
          <SectionCard title="Appearance & Display" icon={Palette}>
            <SettingRow label="Dark Theme"><ToggleSwitch enabled={darkTheme} onChange={() => setDarkTheme(!darkTheme)} /></SettingRow>
            <SettingRow label="Blue Accent Color"><ToggleSwitch enabled={blueAccent} onChange={() => setBlueAccent(!blueAccent)} /></SettingRow>
            <SettingRow label="Compact Layout"><ToggleSwitch enabled={compactLayout} onChange={() => setCompactLayout(!compactLayout)} /></SettingRow>
            <SettingRow label="Enable Animations"><ToggleSwitch enabled={animations} onChange={() => setAnimations(!animations)} /></SettingRow>
            <SettingRow label="Enable Glassmorphism"><ToggleSwitch enabled={glassmorphism} onChange={() => setGlassmorphism(!glassmorphism)} /></SettingRow>
            <SettingRow label="Show Particle Effects"><ToggleSwitch enabled={particles} onChange={() => setParticles(!particles)} /></SettingRow>
          </SectionCard>
        );
      case 'logs':
        return (
          <SectionCard title="System Audit Log" icon={ScrollText}>
            <div className="space-y-6 pt-2">
              {[
                { time: '01:44 PM', event: 'AI confidence threshold updated to 90%', actor: 'Admin' },
                { time: '01:38 PM', event: 'Officer permissions modified for Officer 3', actor: 'Admin' },
                { time: '01:22 PM', event: 'Camera CAM-012 settings updated', actor: 'System' },
                { time: '01:15 PM', event: 'Notification preferences changed', actor: 'Admin' },
                { time: '12:58 PM', event: 'Auto-dispatch enabled for Zone B', actor: 'Admin' },
                { time: '12:44 PM', event: 'New camera CAM-011 registered', actor: 'System' },
                { time: '12:31 PM', event: 'Redis Cache integration disconnected', actor: 'System' },
                { time: '12:10 PM', event: 'System health check completed — all OK', actor: 'System' },
              ].map((log, i) => (
                <motion.div 
                  initial={{ opacity: 0, x: -10 }} 
                  animate={{ opacity: 1, x: 0 }} 
                  transition={{ delay: i * 0.05 }}
                  key={i} 
                  className="flex gap-4 relative"
                >
                  <div className="absolute left-[5px] top-6 bottom-[-24px] w-px bg-white/10 last:hidden" />
                  <div className="w-3 h-3 rounded-full bg-blue-500/50 border border-blue-400 mt-1.5 z-10" />
                  <div className="flex-1 pb-2">
                    <div className="flex items-center gap-3 mb-1">
                      <span className="text-xs font-mono text-slate-400">{log.time}</span>
                      <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border uppercase tracking-wider
                        ${log.actor === 'Admin' ? 'bg-blue-500/10 border-blue-500/20 text-blue-400' : 'bg-purple-500/10 border-purple-500/20 text-purple-400'}
                      `}>
                        {log.actor}
                      </span>
                    </div>
                    <p className="text-sm text-slate-200">{log.event}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </SectionCard>
        );
      default:
        return null;
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
            { icon: LayoutDashboard, label: 'Dashboard', active: false, path: '/dashboard' },
            { icon: AlertTriangle, label: 'Alerts', active: false, path: '/alerts' },
            { icon: BarChart2, label: 'Analytics', active: false, path: '/analytics' },
            { icon: CameraIcon, label: 'Cameras', active: false, path: '/cameras' },
            { icon: Radio, label: 'Dispatch', active: false, path: '/dispatch' },
            { icon: SettingsIcon, label: 'Settings', active: true, path: '/settings' },
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
              <span className="text-xs font-semibold text-green-400 tracking-wide uppercase">System Healthy</span>
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
        <main className="flex-1 overflow-y-auto mt-14 p-8 custom-scrollbar">
          <div className="max-w-7xl mx-auto">
            {/* Page Header */}
            <div className="mb-8">
              <h1 className="text-4xl font-bold tracking-wider mb-2 text-blue-400 drop-shadow-[0_0_15px_rgba(59,130,246,0.6)]" style={{ fontFamily: "'Orbitron', sans-serif" }}>
                System Configuration
              </h1>
              <p className="text-slate-400 text-sm font-medium">Manage ParkSight settings, AI parameters and operational preferences.</p>
            </div>

            {/* Layout: Left Nav + Right Content */}
            <div className="flex gap-8 pb-20 items-start">
              
              {/* Left Settings Nav */}
              <div className="w-[260px] flex-shrink-0 sticky top-4">
                <div className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.07] rounded-2xl p-3 flex flex-col gap-1">
                  {SECTIONS.map((sec) => (
                    <button
                      key={sec.id}
                      onClick={() => setSelectedSection(sec.id)}
                      className={`flex items-center gap-3 w-full px-4 py-3 rounded-xl transition-all duration-200 text-sm font-bold
                        ${selectedSection === sec.id 
                          ? 'bg-blue-500/10 text-blue-400 border border-blue-500/30 shadow-[inset_2px_0_10px_rgba(59,130,246,0.1)]' 
                          : 'text-slate-400 hover:bg-white/[0.05] hover:text-slate-200 border border-transparent'}
                      `}
                    >
                      <sec.icon size={18} className={selectedSection === sec.id ? "drop-shadow-[0_0_8px_rgba(59,130,246,0.8)]" : ""} />
                      {sec.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Right Panel */}
              <div className="flex-1 min-w-0 relative">
                <AnimatePresence mode="wait">
                  {renderSection()}
                </AnimatePresence>
              </div>

            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
