import React, { useState, useEffect, createContext, useContext } from "react";
import {
  Eye, ShieldAlert, AlertTriangle, Info, Activity, LayoutDashboard, Terminal,
  Server, BellRing, Search, FileText, Bot, Settings, Send, Sun, Moon,
  CheckCircle2, Radio, HardDrive, Router as RouterIcon, Laptop, Sparkles,
  Filter, Download, RefreshCw, Clock, Bell, ArrowUpRight, ShieldCheck,
  KeyRound, Mail, Database, Users, Building2, Wifi, XCircle, ChevronRight,
  Plus, Trash2, Save, WifiOff, Globe, Loader2, Palette,
} from "lucide-react";
import {
  AreaChart, Area, XAxis, ResponsiveContainer, PieChart, Pie, Cell,
} from "recharts";

/* ---------------------------------------------------------------
   Palette — Dark Cybersecurity Dashboard
--------------------------------------------------------------- */
const ACCENT = {
  turquoise: "#00D4FF", green: "#00E38C", blue: "#3B82F6",
  violet: "#7C5CFF", red: "#FF4D57", orange: "#F5A623", amber: "#FFD166",
};

const PALETTES = {
  dark: {
    bg: "#07111F", bgAlt: "#0B1220", bgAlt2: "#101826",
    panel: "rgba(18,27,46,0.75)", panel2: "rgba(24,35,56,0.8)",
    border: "#27415E", borderSoft: "rgba(255,255,255,0.08)",
    text: "#EAF0FA", textDim: "#93A4BF", textFaint: "#5B6B85",
    shadow: "0 10px 30px rgba(0,0,0,0.4)", ...ACCENT,
  },
  light: {
    bg: "#EEF2F8", bgAlt: "#F5F7FB", bgAlt2: "#FFFFFF",
    panel: "rgba(255,255,255,0.82)", panel2: "rgba(255,255,255,0.94)",
    border: "#D6DEEA", borderSoft: "rgba(15,23,42,0.08)",
    text: "#101826", textDim: "#4C5768", textFaint: "#8794A8",
    shadow: "0 10px 30px rgba(15,23,42,0.10)", ...ACCENT,
  },
};

const ThemeCtx = createContext(PALETTES.dark);
const useTheme = () => useContext(ThemeCtx);

/* ---------------------------------------------------------------
   Connexion au backend ARGUS (Phase 1 : FastAPI + PostgreSQL)
   L'URL est configurable depuis Paramètres > Connexion API.
--------------------------------------------------------------- */
const ApiCtx = createContext({ apiBase: "http://localhost:8000", setApiBase: () => {}, connected: false });
const useApiCtx = () => useContext(ApiCtx);

function useApi(path, deps = []) {
  const { apiBase, connected } = useApiCtx();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    fetch(`${apiBase}${path}`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((d) => {
        if (!cancelled) { setData(d); setLoading(false); }
      })
      .catch((e) => {
        if (!cancelled) { setError(e.message || "Requête échouée"); setLoading(false); }
      });
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [apiBase, connected, ...deps]);

  return { data, loading, error };
}

function ApiStateBanner({ error, loading }) {
  const C = useTheme();
  if (loading) return (
    <div className="flex items-center gap-2 text-[11px] mb-3" style={{ color: C.textFaint, ...bodyFont }}>
      <Loader2 size={12} className="animate-spin" /> Chargement depuis l'API ARGUS…
    </div>
  );
  if (error) return (
    <div className="flex items-center gap-2 text-[11px] mb-3 px-3 py-2 rounded-lg" style={{ color: C.orange, background: `${C.orange}14`, ...bodyFont }}>
      <WifiOff size={12} /> Backend injoignable ({error}) — données de démonstration affichées. Vérifiez l'URL dans Paramètres.
    </div>
  );
  return null;
}

const titleFont = { fontFamily: "'Poppins','Manrope',sans-serif" };
const bodyFont = { fontFamily: "'Manrope','Inter',sans-serif" };
const monoFont = { fontFamily: "'JetBrains Mono',ui-monospace,monospace" };

const glass = (C, radius = 16) => ({
  background: C.panel, border: `1px solid ${C.borderSoft}`, borderRadius: radius,
  boxShadow: C.shadow, backdropFilter: "blur(8px)", WebkitBackdropFilter: "blur(8px)",
});

/* ---------------------------------------------------------------
   Fake data (partagée par plusieurs pages)
--------------------------------------------------------------- */
const SOURCES = [
  { id: "fortigate", name: "FortiGate", full: "FortiGate 600E", color: ACCENT.red },
  { id: "eset", name: "ESET", full: "ESET PROTECT", color: ACCENT.orange },
  { id: "synology", name: "Synology", full: "Synology DS1821+", color: ACCENT.blue },
  { id: "windows", name: "Windows", full: "WIN-DC01", color: ACCENT.green },
  { id: "linux", name: "Linux/EDR", full: "Serveurs Ubuntu (EDR)", color: ACCENT.amber },
  { id: "network", name: "Réseau", full: "Switch / Routeur", color: ACCENT.violet },
];

const PULSE_DATA = Array.from({ length: 24 }, (_, h) => ({
  h: `${String(h).padStart(2, "0")}h`,
  fortigate: Math.round(18 + Math.sin(h / 2) * 10 + (h === 13 ? 48 : 0) + Math.random() * 6),
  eset: Math.round(6 + Math.cos(h / 3) * 4 + Math.random() * 3),
  synology: Math.round(4 + Math.random() * 3),
  windows: Math.round(9 + Math.sin(h / 4) * 5 + Math.random() * 4),
  linux: Math.round(5 + Math.random() * 3),
  network: Math.round(7 + Math.random() * 4),
}));

const SEVERITY_DONUT = [
  { name: "Critique", value: 4, pct: 12, color: ACCENT.red },
  { name: "Attention", value: 7, pct: 22, color: ACCENT.orange },
  { name: "Info", value: 21, pct: 66, color: ACCENT.blue },
];

const TOP_CATEGORIES = [
  { label: "Malware", val: 6, color: ACCENT.red },
  { label: "Intrusion", val: 5, color: ACCENT.orange },
  { label: "Auth", val: 4, color: ACCENT.orange },
  { label: "Network", val: 4, color: ACCENT.green },
  { label: "Storage", val: 3, color: ACCENT.blue },
  { label: "Autres", val: 10, color: ACCENT.violet },
];

const SEV_META = {
  critical: { label: "Critique", color: ACCENT.red },
  warning: { label: "Attention", color: ACCENT.orange },
  info: { label: "Info", color: ACCENT.blue },
};

const LOGS = [
  { t: "08:12:04", src: "fortigate", sev: "critical", route: "41.226.13.90 → 192.168.1.42", msg: "Téléchargement bloqué depuis une IP malveillante connue", cat: "Malware" },
  { t: "08:09:51", src: "eset", sev: "critical", route: "PC-COMPTA-04 · 192.168.1.42", msg: "Trojan.GenericKD.68541812 mis en quarantaine", cat: "Malware" },
  { t: "07:58:22", src: "windows", sev: "warning", route: "WIN-DC01 · 192.168.1.10", msg: "5 échecs d'authentification consécutifs — j.dupont", cat: "Auth" },
  { t: "07:44:10", src: "network", sev: "info", route: "Switch-Core-01", msg: "Port Gi1/0/14 renégocié à 1 Gbps", cat: "Réseau" },
  { t: "07:30:03", src: "fortigate", sev: "warning", route: "192.168.1.77 → 185.220.101.5", msg: "Trafic sortant vers un nœud de sortie Tor connu", cat: "Réseau" },
  { t: "07:12:41", src: "synology", sev: "info", route: "Synology-NAS-01", msg: "Sauvegarde Hyper Backup terminée avec succès", cat: "Stockage" },
  { t: "06:55:19", src: "eset", sev: "info", route: "LAPTOP-DIR-01", msg: "Analyse planifiée terminée — aucune menace", cat: "Malware" },
  { t: "06:40:02", src: "fortigate", sev: "critical", route: "203.0.113.4 → 192.168.1.1", msg: "Tentative d'intrusion — signature IPS SSH.Brute.Force", cat: "Intrusion" },
  { t: "06:21:58", src: "windows", sev: "info", route: "WIN-DC01", msg: "Stratégie de groupe appliquée à 34 postes", cat: "Auth" },
  { t: "06:05:37", src: "network", sev: "warning", route: "Routeur-WAN", msg: "Latence anormale détectée sur le lien FAI secondaire", cat: "Réseau" },
];

const EQUIPMENTS = [
  { name: "FortiGate 600E", vendor: "Fortinet", model: "FortiGate 600E", version: "7.4.3", ip: "10.0.0.1", status: "online", logsToday: 1284, lastSeen: "il y a 12 s" },
  { name: "Switch-Core-3850", vendor: "Cisco", model: "Catalyst 3850", version: "16.12.5", ip: "10.0.0.2", status: "online", logsToday: 214, lastSeen: "il y a 8 s" },
  { name: "Routeur-WAN-Edge", vendor: "Cisco", model: "ISR 4331", version: "17.6.4", ip: "10.0.0.254", status: "online", logsToday: 96, lastSeen: "il y a 20 s" },
  { name: "Synology-DS1821+", vendor: "Synology", model: "DS1821+", version: "DSM 7.2", ip: "10.0.10.5", status: "online", logsToday: 58, lastSeen: "il y a 1 min" },
  { name: "ESET PROTECT Server", vendor: "ESET", model: "PROTECT On-Prem", version: "11.1", ip: "10.0.0.20", status: "online", logsToday: 73, lastSeen: "il y a 5 s" },
  { name: "WIN-DC01", vendor: "Microsoft", model: "Windows Server", version: "2022", ip: "10.0.0.10", status: "degraded", logsToday: 407, lastSeen: "il y a 4 min" },
];

const ALERTS = [
  { type: "Malware détecté", sev: "critical", device: "PC-COMPTA-04", ip: "192.168.1.42", t: "08:09:51", status: "nouvelle" },
  { type: "Tentative de brute force", sev: "critical", device: "FortiGate 600E", ip: "203.0.113.4", t: "06:40:02", status: "acquittée" },
  { type: "Scan réseau détecté", sev: "warning", device: "Switch-Core-3850", ip: "192.168.1.0/24", t: "05:22:10", status: "nouvelle" },
  { type: "Connexion suspecte (Tor)", sev: "warning", device: "FortiGate 600E", ip: "185.220.101.5", t: "07:30:03", status: "nouvelle" },
  { type: "Perte de connexion", sev: "warning", device: "Routeur-WAN-Edge", ip: "10.0.0.254", t: "hier 23:41", status: "résolue" },
  { type: "Échecs d'authentification répétés", sev: "warning", device: "WIN-DC01", ip: "192.168.1.10", t: "07:58:22", status: "acquittée" },
];

const REPORTS = [
  { name: "Rapport quotidien — 05 août 2026", period: "Quotidien", format: "PDF", size: "312 Ko", when: "05:00" },
  { name: "Rapport hebdomadaire — 28 juil. → 03 août", period: "Hebdomadaire", format: "PDF", size: "1,1 Mo", when: "lun. 06:00" },
  { name: "Export logs FortiGate — juillet", period: "Mensuel", format: "CSV", size: "4,8 Mo", when: "01/08 05:00" },
  { name: "Rapport quotidien — 04 août 2026", period: "Quotidien", format: "Excel", size: "298 Ko", when: "hier 05:00" },
];

const AGENT_PROMPTS = [
  "Résumé des événements critiques d'aujourd'hui",
  "Pourquoi cette IP est bloquée ?",
  "Quels équipements génèrent le plus d'alertes ?",
  "Donne-moi les attaques les plus fréquentes",
];

const EXAMPLE_QUERIES = [
  "source=FortiGate severity=Critical today",
  "IP=192.168.1.20",
  "source=ESET category=Malware",
  "severity=Critical last:7d",
];

const NAV_ITEMS = [
  { id: "dashboard", label: "Tableau de bord", icon: LayoutDashboard },
  { id: "logs", label: "Logs en temps réel", icon: Terminal },
  { id: "equip", label: "Équipements", icon: Server },
  { id: "alerts", label: "Alertes", icon: BellRing },
  { id: "query", label: "Requêtes", icon: Search },
  { id: "reports", label: "Rapports", icon: FileText },
  { id: "agent", label: "IA Analyste", icon: Bot },
  { id: "settings", label: "Paramètres", icon: Settings },
];

const SEVERITY_COLOR = { critical: ACCENT.red, warning: ACCENT.orange, info: ACCENT.blue };
const SEVERITY_LABEL = { critical: "Critique", warning: "Attention", info: "Info" };
const CATEGORY_COLOR = { Malware: ACCENT.red, Intrusion: ACCENT.orange, Auth: ACCENT.orange, Network: ACCENT.green, Storage: ACCENT.blue, Autres: ACCENT.violet };

function buildSeverityDonut(severityCounts) {
  const total = severityCounts.reduce((s, x) => s + x.count, 0) || 1;
  return severityCounts.map((s) => ({
    name: SEVERITY_LABEL[s.severity] || s.severity,
    value: s.count,
    pct: Math.round((s.count / total) * 100),
    color: SEVERITY_COLOR[s.severity] || ACCENT.violet,
  }));
}

function buildTopCategories(topCategories) {
  return topCategories.slice(0, 6).map((c) => ({
    label: c.category, val: c.count, color: CATEGORY_COLOR[c.category] || ACCENT.violet,
  }));
}

function buildHourlyChart(hourlyVolume) {
  const hours = Array.from({ length: 24 }, (_, h) => {
    const key = String(h).padStart(2, "0");
    const row = { h: `${key}h` };
    SOURCES.forEach((s) => { row[s.id] = 0; });
    return { key, row };
  });
  const byHour = Object.fromEntries(hours.map((h) => [h.key, h.row]));
  hourlyVolume.forEach((pt) => {
    if (byHour[pt.hour] && pt.source_type in byHour[pt.hour]) {
      byHour[pt.hour][pt.source_type] += pt.count;
    }
  });
  return hours.map((h) => h.row);
}

/* ---------------------------------------------------------------
   Primitives
--------------------------------------------------------------- */
function SectionLabel({ children, style }) {
  const C = useTheme();
  return <div className="text-[12px] font-bold uppercase tracking-[0.1em] mb-3" style={{ color: C.text, ...titleFont, ...style }}>{children}</div>;
}
function SevBadge({ sev }) {
  const C = useTheme();
  const m = SEV_META[sev];
  return (
    <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase" style={{ color: m.color, background: `${m.color}1F`, ...bodyFont }}>{m.label}</span>
  );
}
function SourceTag({ id }) {
  const s = SOURCES.find((x) => x.id === id);
  if (!s) return null;
  return (
    <span className="inline-flex items-center gap-1.5 text-[12px] font-semibold" style={{ color: s.color, ...bodyFont }}>
      <span className="w-1.5 h-1.5 rounded-full" style={{ background: s.color }} /> {s.full}
    </span>
  );
}
function PageTitle({ children }) {
  const C = useTheme();
  return <div className="text-[15px] font-extrabold tracking-[0.08em] mb-4" style={{ color: C.turquoise, ...titleFont }}>{children}</div>;
}

/* ---------------------------------------------------------------
   Sidebar
--------------------------------------------------------------- */
function Sidebar({ page, setPage }) {
  const C = useTheme();
  const { connected } = useApiCtx();
  return (
    <div className="hidden md:flex flex-col justify-between shrink-0 h-full py-5 px-3" style={{ width: 220, background: C.panel2, borderRight: `1px solid ${C.borderSoft}` }}>
      <div>
        <div className="flex items-center gap-2 px-2 mb-6">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: `${C.green}1F`, color: C.green }}>
            <Eye size={16} />
          </div>
          <span className="text-[16px] font-extrabold" style={{ color: C.text, ...titleFont }}>ARGUS</span>
        </div>
        <nav className="flex flex-col gap-1">
          {NAV_ITEMS.map((it) => {
            const active = page === it.id;
            return (
              <button key={it.id} onClick={() => setPage(it.id)} className="flex items-center gap-2.5 px-3 py-2 rounded-lg text-[13px] font-medium text-left"
                style={{ color: active ? C.turquoise : C.textDim, background: active ? `${C.turquoise}14` : "transparent", ...bodyFont }}>
                <it.icon size={15} /> {it.label}
              </button>
            );
          })}
        </nav>
      </div>
      <button onClick={() => setPage("settings")} className="flex items-center gap-1.5 px-3 py-2 rounded-lg" style={{ background: connected ? `${C.green}14` : `${C.red}14` }}>
        <span className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: connected ? C.green : C.red }} />
        <span className="text-[11px] font-semibold" style={{ color: connected ? C.green : C.red, ...bodyFont }}>
          {connected ? "Système Opérationnel" : "Backend injoignable"}
        </span>
      </button>
    </div>
  );
}

/* =================================================================
   PAGE 1 — Tableau de bord (réplique de l'image de référence)
================================================================= */
function DashboardPage() {
  const C = useTheme();

  const stats = useApi("/api/stats/overview?hours=24");
  const liveLogs = useApi("/api/logs?limit=5");
  const devices = useApi("/api/devices");

  const donutData = stats.data ? buildSeverityDonut(stats.data.severity_counts) : SEVERITY_DONUT;
  const categoriesData = stats.data ? buildTopCategories(stats.data.top_categories) : TOP_CATEGORIES;
  const pulseData = stats.data ? buildHourlyChart(stats.data.hourly_volume) : PULSE_DATA;
  const donutTotal = stats.data ? stats.data.severity_counts.reduce((s, x) => s + x.count, 0) : 32;
  const logsRows = liveLogs.data
    ? liveLogs.data.map((l) => ({ t: new Date(l.timestamp).toLocaleTimeString("fr-FR"), src: l.source_type, sev: l.severity, route: [l.src_ip, l.dst_ip].filter(Boolean).join(" → ") || l.source_device || "—", msg: l.message || l.event_type }))
    : LOGS.slice(0, 5);
  const equipRows = devices.data
    ? devices.data.map((d) => ({ name: d.name || d.ip, status: d.status, logsToday: d.logs_count }))
    : EQUIPMENTS.slice(0, 5);

  return (
    <div className="px-6 py-5 overflow-y-auto h-full">
      <PageTitle>TABLEAU DE BORD — VUE D'ENSEMBLE</PageTitle>
      <ApiStateBanner loading={stats.loading} error={stats.error} />

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4 mb-4">
        <div className="lg:col-span-3 p-4" style={glass(C)}>
          <SectionLabel>Événements par source (24h)</SectionLabel>
          <div style={{ height: 170 }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={pulseData} margin={{ top: 4, right: 0, left: 0, bottom: 0 }}>
                <defs>
                  {SOURCES.map((s) => (
                    <linearGradient key={s.id} id={`g-${s.id}`} x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={s.color} stopOpacity={0.55} />
                      <stop offset="100%" stopColor={s.color} stopOpacity={0} />
                    </linearGradient>
                  ))}
                </defs>
                <XAxis dataKey="h" tick={{ fill: C.textFaint, fontSize: 10 }} axisLine={{ stroke: C.borderSoft }} tickLine={false} interval={3} />
                {SOURCES.map((s) => (
                  <Area key={s.id} type="monotone" dataKey={s.id} stackId="1" stroke={s.color} strokeWidth={1.25} fill={`url(#g-${s.id})`} />
                ))}
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="flex flex-wrap gap-x-3 gap-y-1 mt-2">
            {SOURCES.map((s) => (
              <div key={s.id} className="flex items-center gap-1 text-[10.5px]" style={{ color: C.textFaint, ...bodyFont }}>
                <span className="w-1.5 h-1.5 rounded-full" style={{ background: s.color }} /> {s.name}
              </div>
            ))}
          </div>
        </div>

        <div className="lg:col-span-1 p-4" style={glass(C)}>
          <SectionLabel>Répartition des sévérités</SectionLabel>
          <div className="relative flex items-center justify-center" style={{ height: 110 }}>
            <ResponsiveContainer width={110} height={110}>
              <PieChart>
                <Pie data={donutData} dataKey="value" innerRadius={32} outerRadius={50} startAngle={90} endAngle={-270} stroke="none">
                  {donutData.map((d, i) => <Cell key={i} fill={d.color} />)}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-[18px] font-extrabold" style={{ color: C.text, ...titleFont }}>{donutTotal}</span>
              <span className="text-[8.5px]" style={{ color: C.textFaint, ...bodyFont }}>Événements</span>
            </div>
          </div>
          <div className="flex flex-col gap-1.5 mt-2">
            {donutData.map((d, i) => (
              <div key={i} className="flex items-center gap-1.5 text-[11px]" style={{ color: C.textDim, ...bodyFont }}>
                <span className="w-2 h-2 rounded-full shrink-0" style={{ background: d.color }} /> {d.name} <span style={{ color: C.textFaint }}>{d.value} ({d.pct}%)</span>
              </div>
            ))}
          </div>
        </div>

        <div className="lg:col-span-1 p-4" style={glass(C)}>
          <SectionLabel>Top catégories</SectionLabel>
          <div className="flex flex-col gap-2.5">
            {categoriesData.map((c, i) => (
              <div key={i} className="flex items-center gap-2">
                <span className="text-[11px] w-14 shrink-0" style={{ color: C.textDim, ...bodyFont }}>{c.label}</span>
                <div className="flex-1 h-1.5 rounded-full" style={{ background: C.borderSoft }}>
                  <div className="h-full rounded-full" style={{ width: `${Math.min(100, (c.val / (categoriesData[0]?.val || 1)) * 100)}%`, background: c.color }} />
                </div>
                <span className="text-[11px] w-4 text-right" style={{ color: C.textFaint, ...monoFont }}>{c.val}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        <div className="lg:col-span-3 p-4" style={glass(C)}>
          <div className="flex items-center justify-between mb-1">
            <SectionLabel style={{ marginBottom: 0 }}>Logs en temps réel</SectionLabel>
            <div className="flex items-center gap-1 text-[10.5px]" style={{ color: C.green, ...monoFont }}><Radio size={11} className="animate-pulse" /> LIVE</div>
          </div>
          <table className="w-full text-[11.5px] mt-2" style={{ borderCollapse: "collapse" }}>
            <thead>
              <tr>{["Heure", "Source", "Sévérité", "Source / Destination", "Message"].map((h) => (
                <th key={h} className="text-left py-1.5 font-semibold" style={{ color: C.textFaint, fontSize: 9.5, letterSpacing: "0.05em", textTransform: "uppercase", ...bodyFont }}>{h}</th>
              ))}</tr>
            </thead>
            <tbody>
              {logsRows.map((l, i) => (
                <tr key={i} style={{ borderTop: `1px solid ${C.borderSoft}` }}>
                  <td className="py-2 pr-2 whitespace-nowrap" style={{ color: C.textFaint, ...monoFont, fontSize: 10.5 }}>{l.t}</td>
                  <td className="py-2 pr-2"><SourceTag id={l.src} /></td>
                  <td className="py-2 pr-2"><SevBadge sev={l.sev} /></td>
                  <td className="py-2 pr-2 whitespace-nowrap" style={{ color: C.textDim, ...monoFont, fontSize: 10.5 }}>{l.route}</td>
                  <td className="py-2" style={{ color: C.text, ...bodyFont }}>{l.msg}</td>
                </tr>
              ))}
              {logsRows.length === 0 && <tr><td colSpan={5} className="text-center py-4" style={{ color: C.textFaint, ...bodyFont }}>Aucun log reçu.</td></tr>}
            </tbody>
          </table>
          <div className="text-[11px] font-semibold mt-2" style={{ color: C.turquoise, ...bodyFont }}>Voir tous les logs →</div>
        </div>

        <div className="lg:col-span-1 p-4" style={glass(C)}>
          <SectionLabel>Équipements</SectionLabel>
          <div className="flex flex-col gap-2.5">
            {equipRows.map((e, i) => (
              <div key={i} className="flex items-center justify-between text-[11.5px]">
                <div className="flex items-center gap-2 min-w-0">
                  <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ background: e.status === "online" ? C.green : C.orange }} />
                  <span className="truncate" style={{ color: C.text, ...bodyFont }}>{e.name}</span>
                </div>
                <span className="shrink-0" style={{ color: C.textFaint, ...monoFont, fontSize: 10.5 }}>{e.logsToday}</span>
              </div>
            ))}
          </div>
          <div className="text-[11px] font-semibold mt-3" style={{ color: C.turquoise, ...bodyFont }}>Voir tous les équipements →</div>
        </div>

        <div className="lg:col-span-1 p-4" style={glass(C)}>
          <div className="flex items-center gap-2 mb-3">
            <div className="w-8 h-8 rounded-full flex items-center justify-center" style={{ background: `${C.green}1F`, color: C.green }}><Bot size={15} /></div>
            <div>
              <div className="text-[12.5px] font-bold" style={{ color: C.text, ...bodyFont }}>IA Analyste</div>
              <div className="text-[10.5px]" style={{ color: C.textFaint, ...bodyFont }}>Bonjour ! Posez-moi une question sur vos logs.</div>
            </div>
          </div>
          <div className="text-[10.5px] font-semibold mb-1.5" style={{ color: C.textFaint, ...bodyFont }}>EXEMPLES :</div>
          <div className="flex flex-col gap-1.5">
            {AGENT_PROMPTS.map((p, i) => <div key={i} className="text-[11px]" style={{ color: C.turquoise, ...bodyFont }}>• {p}</div>)}
          </div>
        </div>
      </div>
    </div>
  );
}

/* =================================================================
   PAGE 2 — Logs en temps réel
================================================================= */
function LogsPage() {
  const C = useTheme();
  const [filter, setFilter] = useState("all");
  const [q, setQ] = useState("");

  const params = new URLSearchParams({ limit: "100" });
  if (filter !== "all") params.set("source_type", filter);
  if (q.trim()) params.set("q", q.trim());
  const { data, loading, error } = useApi(`/api/logs?${params.toString()}`, [filter, q]);

  const filtered = data
    ? data.map((l) => ({
        t: new Date(l.timestamp).toLocaleTimeString("fr-FR"), src: l.source_type, sev: l.severity,
        route: [l.src_ip, l.dst_ip].filter(Boolean).join(" → ") || l.source_device || "—",
        msg: l.message || l.event_type, cat: l.event_type || "—",
      }))
    : LOGS.filter((l) => filter === "all" || l.src === filter).filter((l) => l.msg.toLowerCase().includes(q.toLowerCase()) || l.route.toLowerCase().includes(q.toLowerCase()));

  return (
    <div className="px-6 py-5 overflow-y-auto h-full flex flex-col gap-4">
      <PageTitle>LOGS EN TEMPS RÉEL — TOUTES SOURCES</PageTitle>
      <ApiStateBanner loading={loading} error={error} />

      <div className="p-4" style={glass(C)}>
        <div className="flex items-center justify-between mb-2">
          <SectionLabel style={{ marginBottom: 0 }}>Volume — 24 dernières heures</SectionLabel>
          <div className="flex items-center gap-1 text-[10.5px]" style={{ color: C.green, ...monoFont }}><Radio size={11} className="animate-pulse" /> LIVE</div>
        </div>
        <div style={{ height: 140 }}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={PULSE_DATA} margin={{ top: 4, right: 0, left: 0, bottom: 0 }}>
              <defs>{SOURCES.map((s) => (
                <linearGradient key={s.id} id={`gl-${s.id}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={s.color} stopOpacity={0.55} /><stop offset="100%" stopColor={s.color} stopOpacity={0} />
                </linearGradient>
              ))}</defs>
              <XAxis dataKey="h" tick={{ fill: C.textFaint, fontSize: 9.5 }} axisLine={{ stroke: C.borderSoft }} tickLine={false} interval={3} />
              {SOURCES.map((s) => <Area key={s.id} type="monotone" dataKey={s.id} stackId="1" stroke={s.color} strokeWidth={1.25} fill={`url(#gl-${s.id})`} />)}
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <div className="flex items-center gap-2 px-3 py-2 flex-1 min-w-[200px]" style={glass(C, 10)}>
          <Search size={14} style={{ color: C.textFaint }} />
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Rechercher par IP, hôte, mot-clé…" className="flex-1 bg-transparent outline-none text-[12.5px]" style={{ color: C.text, ...bodyFont }} />
        </div>
        <button onClick={() => setFilter("all")} className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-[12px] font-medium" style={{ background: filter === "all" ? `${C.turquoise}14` : C.panel, border: `1px solid ${filter === "all" ? C.turquoise : C.borderSoft}`, color: filter === "all" ? C.turquoise : C.textDim, ...bodyFont }}><Filter size={12} /> Toutes sources</button>
        {SOURCES.map((s) => (
          <button key={s.id} onClick={() => setFilter(s.id)} className="px-3 py-2 rounded-lg text-[12px] font-medium" style={{ background: filter === s.id ? `${s.color}14` : C.panel, border: `1px solid ${filter === s.id ? s.color : C.borderSoft}`, color: filter === s.id ? s.color : C.textDim, ...bodyFont }}>{s.full}</button>
        ))}
        <button className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-[12px] ml-auto" style={{ background: C.panel, border: `1px solid ${C.borderSoft}`, color: C.textDim, ...bodyFont }}><Download size={12} /> Exporter</button>
      </div>

      <div className="p-4" style={glass(C)}>
        <table className="w-full text-[12px]" style={{ borderCollapse: "collapse" }}>
          <thead><tr>{["Heure", "Source", "Sévérité", "Origine / Cible", "Message", "Catégorie"].map((h) => (
            <th key={h} className="text-left py-2 font-semibold" style={{ color: C.textFaint, fontSize: 9.5, letterSpacing: "0.05em", textTransform: "uppercase", ...bodyFont }}>{h}</th>
          ))}</tr></thead>
          <tbody>
            {filtered.map((l, i) => (
              <tr key={i} style={{ borderTop: `1px solid ${C.borderSoft}` }}>
                <td className="py-2.5 pr-2 whitespace-nowrap" style={{ color: C.textFaint, ...monoFont }}>{l.t}</td>
                <td className="py-2.5 pr-2"><SourceTag id={l.src} /></td>
                <td className="py-2.5 pr-2"><SevBadge sev={l.sev} /></td>
                <td className="py-2.5 pr-2 whitespace-nowrap" style={{ color: C.textDim, ...monoFont, fontSize: 11.5 }}>{l.route}</td>
                <td className="py-2.5 pr-2" style={{ color: C.text, ...bodyFont }}>{l.msg}</td>
                <td className="py-2.5" style={{ color: C.textFaint, ...bodyFont }}>{l.cat}</td>
              </tr>
            ))}
            {filtered.length === 0 && <tr><td colSpan={6} className="text-center py-8" style={{ color: C.textFaint, ...bodyFont }}>Aucun journal ne correspond à ces critères.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* =================================================================
   PAGE 3 — Équipements
================================================================= */
function EquipPage() {
  const C = useTheme();
  const { data, loading, error } = useApi("/api/devices");
  const rows = data
    ? data.map((d) => ({
        name: d.name || d.ip, vendor: d.vendor || "—", model: d.model || "—", version: d.version || "—",
        ip: d.ip, status: d.status, logsToday: d.logs_count,
        lastSeen: new Date(d.last_seen).toLocaleString("fr-FR"),
      }))
    : EQUIPMENTS.map((e) => ({ ...e }));

  return (
    <div className="px-6 py-5 overflow-y-auto h-full">
      <PageTitle>ÉQUIPEMENTS SURVEILLÉS</PageTitle>
      <ApiStateBanner loading={loading} error={error} />
      {!loading && !error && (
        <div className="text-[11px] mb-3" style={{ color: C.textFaint, ...bodyFont }}>
          Constructeur / modèle / version non déductibles du syslog seul — à renseigner via <span style={{ ...monoFont }}>PATCH /api/devices/{"{id}"}</span>.
        </div>
      )}
      <div className="p-4" style={glass(C)}>
        <table className="w-full text-[12px]" style={{ borderCollapse: "collapse" }}>
          <thead><tr>{["Équipement", "Constructeur", "Modèle", "Version", "Adresse IP", "Statut", "Logs (24h)", "Dernière connexion"].map((h) => (
            <th key={h} className="text-left py-2 pr-3 font-semibold" style={{ color: C.textFaint, fontSize: 9.5, letterSpacing: "0.05em", textTransform: "uppercase", ...bodyFont }}>{h}</th>
          ))}</tr></thead>
          <tbody>
            {rows.map((e, i) => (
              <tr key={i} style={{ borderTop: `1px solid ${C.borderSoft}` }}>
                <td className="py-3 pr-3 font-semibold" style={{ color: C.text, ...bodyFont }}>{e.name}</td>
                <td className="py-3 pr-3" style={{ color: C.textDim, ...bodyFont }}>{e.vendor}</td>
                <td className="py-3 pr-3" style={{ color: C.textDim, ...bodyFont }}>{e.model}</td>
                <td className="py-3 pr-3" style={{ color: C.textFaint, ...monoFont, fontSize: 11 }}>{e.version}</td>
                <td className="py-3 pr-3" style={{ color: C.textFaint, ...monoFont, fontSize: 11 }}>{e.ip}</td>
                <td className="py-3 pr-3">
                  <span className="inline-flex items-center gap-1.5 text-[11px] font-semibold" style={{ color: e.status === "online" ? C.green : C.orange, ...bodyFont }}>
                    <span className="w-1.5 h-1.5 rounded-full" style={{ background: e.status === "online" ? C.green : C.orange }} />
                    {e.status === "online" ? "En ligne" : "Dégradé"}
                  </span>
                </td>
                <td className="py-3 pr-3" style={{ color: C.text, ...monoFont, fontSize: 11.5 }}>{e.logsToday}</td>
                <td className="py-3" style={{ color: C.textFaint, ...bodyFont, fontSize: 11.5 }}>{e.lastSeen}</td>
              </tr>
            ))}
            {rows.length === 0 && <tr><td colSpan={8} className="text-center py-8" style={{ color: C.textFaint, ...bodyFont }}>Aucun équipement détecté pour l'instant.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* =================================================================
   PAGE 4 — Alertes
================================================================= */
function AlertsPage() {
  const C = useTheme();
  const STATUS_META = {
    nouvelle: { color: C.red, label: "Nouvelle" },
    acquittée: { color: C.orange, label: "Acquittée" },
    résolue: { color: C.green, label: "Résolue" },
  };
  return (
    <div className="px-6 py-5 overflow-y-auto h-full">
      <PageTitle>ALERTES</PageTitle>
      <div className="flex flex-col gap-2.5">
        {ALERTS.map((a, i) => (
          <div key={i} className="flex items-center justify-between p-4" style={glass(C, 14)}>
            <div className="flex items-center gap-3 min-w-0">
              <div className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0" style={{ background: `${SEV_META[a.sev].color}1F`, color: SEV_META[a.sev].color }}>
                <ShieldAlert size={16} />
              </div>
              <div className="min-w-0">
                <div className="text-[13px] font-bold truncate" style={{ color: C.text, ...bodyFont }}>{a.type}</div>
                <div className="text-[11px]" style={{ color: C.textFaint, ...monoFont }}>{a.device} · {a.ip}</div>
              </div>
            </div>
            <div className="flex items-center gap-4 shrink-0">
              <SevBadge sev={a.sev} />
              <span className="text-[11px]" style={{ color: C.textFaint, ...monoFont }}>{a.t}</span>
              <span className="px-2.5 py-1 rounded-full text-[10.5px] font-semibold" style={{ color: STATUS_META[a.status].color, background: `${STATUS_META[a.status].color}1A`, ...bodyFont }}>{STATUS_META[a.status].label}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* =================================================================
   PAGE 5 — Requêtes
================================================================= */
const QUERY_SOURCE_ALIAS = { fortigate: "fortigate", eset: "eset", synology: "synology", windows: "windows", linux: "linux", network: "network", réseau: "network" };

function parseQuerySyntax(raw) {
  const lower = raw.toLowerCase();
  const params = new URLSearchParams({ limit: "100" });
  const srcMatch = lower.match(/source=([\w]+)/);
  const sevMatch = lower.match(/severity=([\w]+)/);
  const ipMatch = lower.match(/ip=([\d.]+)/);
  if (srcMatch && QUERY_SOURCE_ALIAS[srcMatch[1]]) params.set("source_type", QUERY_SOURCE_ALIAS[srcMatch[1]]);
  if (sevMatch) {
    const sev = sevMatch[1].startsWith("crit") ? "critical" : sevMatch[1].startsWith("warn") || sevMatch[1].startsWith("atten") ? "warning" : "info";
    params.set("severity", sev);
  }
  if (ipMatch) params.set("q", ipMatch[1]);
  if (!srcMatch && !sevMatch && !ipMatch && raw.trim()) params.set("q", raw.trim());
  return params;
}

function QueryPage() {
  const C = useTheme();
  const { apiBase } = useApiCtx();
  const [query, setQuery] = useState("");
  const [ran, setRan] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const run = async (text) => {
    const q = (text ?? query).trim();
    setQuery(q);
    if (!q) { setRan(null); return; }
    setLoading(true);
    setError(null);
    const params = parseQuerySyntax(q);
    try {
      const res = await fetch(`${apiBase}/api/logs?${params.toString()}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setRan(data.map((l) => ({
        t: new Date(l.timestamp).toLocaleTimeString("fr-FR"), src: l.source_type, sev: l.severity,
        route: [l.src_ip, l.dst_ip].filter(Boolean).join(" → ") || l.source_device || "—",
        msg: l.message || l.event_type,
      })));
    } catch (e) {
      setError(e.message || "Requête échouée");
      // repli sur les données de démonstration si le backend est injoignable
      const lower = q.toLowerCase();
      setRan(LOGS.filter((l) => {
        const srcMatch = lower.match(/source=([\w]+)/);
        const sevMatch = lower.match(/severity=([\w]+)/);
        const ipMatch = lower.match(/ip=([\d.]+)/);
        let ok = true;
        if (srcMatch) ok = ok && l.src.includes(srcMatch[1]);
        if (sevMatch) ok = ok && l.sev.includes(sevMatch[1]);
        if (ipMatch) ok = ok && l.route.includes(ipMatch[1]);
        if (!srcMatch && !sevMatch && !ipMatch) ok = l.msg.toLowerCase().includes(lower) || l.route.toLowerCase().includes(lower);
        return ok;
      }));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="px-6 py-5 overflow-y-auto h-full flex flex-col gap-4">
      <PageTitle>REQUÊTES — RECHERCHE DANS LES LOGS</PageTitle>
      <ApiStateBanner loading={false} error={error} />

      <div className="p-4" style={glass(C)}>
        <div className="flex items-center gap-2 px-3 py-2.5 rounded-lg mb-3" style={{ background: C.panel2, border: `1px solid ${C.borderSoft}` }}>
          <Terminal size={15} style={{ color: C.turquoise }} />
          <input
            value={query} onChange={(e) => setQuery(e.target.value)} onKeyDown={(e) => e.key === "Enter" && run()}
            placeholder="source=FortiGate severity=Critical today   ou   IP=192.168.1.20"
            className="flex-1 bg-transparent outline-none text-[13px]" style={{ color: C.text, ...monoFont }}
          />
          <button onClick={() => run()} className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[12px] font-semibold" style={{ border: `1px solid ${C.turquoise}`, color: C.turquoise, boxShadow: `0 0 10px ${C.turquoise}44`, ...bodyFont }}>
            {loading && <Loader2 size={12} className="animate-spin" />} Exécuter
          </button>
        </div>
        <div className="flex flex-wrap gap-2">
          {EXAMPLE_QUERIES.map((eq, i) => (
            <button key={i} onClick={() => run(eq)} className="text-[11.5px] px-3 py-1.5 rounded-full" style={{ background: C.panel2, border: `1px solid ${C.borderSoft}`, color: C.textDim, ...monoFont }}>{eq}</button>
          ))}
        </div>
      </div>

      {ran !== null && (
        <div className="p-4" style={glass(C)}>
          <SectionLabel>{ran.length} résultat{ran.length > 1 ? "s" : ""}</SectionLabel>
          <table className="w-full text-[12px]" style={{ borderCollapse: "collapse" }}>
            <thead><tr>{["Heure", "Source", "Sévérité", "Origine / Cible", "Message"].map((h) => (
              <th key={h} className="text-left py-2 pr-2 font-semibold" style={{ color: C.textFaint, fontSize: 9.5, letterSpacing: "0.05em", textTransform: "uppercase", ...bodyFont }}>{h}</th>
            ))}</tr></thead>
            <tbody>
              {ran.map((l, i) => (
                <tr key={i} style={{ borderTop: `1px solid ${C.borderSoft}` }}>
                  <td className="py-2.5 pr-2 whitespace-nowrap" style={{ color: C.textFaint, ...monoFont }}>{l.t}</td>
                  <td className="py-2.5 pr-2"><SourceTag id={l.src} /></td>
                  <td className="py-2.5 pr-2"><SevBadge sev={l.sev} /></td>
                  <td className="py-2.5 pr-2 whitespace-nowrap" style={{ color: C.textDim, ...monoFont, fontSize: 11.5 }}>{l.route}</td>
                  <td className="py-2.5" style={{ color: C.text, ...bodyFont }}>{l.msg}</td>
                </tr>
              ))}
              {ran.length === 0 && <tr><td colSpan={5} className="text-center py-8" style={{ color: C.textFaint, ...bodyFont }}>Aucun résultat pour cette requête.</td></tr>}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

/* =================================================================
   PAGE 6 — Rapports
================================================================= */
function ReportsPage() {
  const C = useTheme();
  const { apiBase } = useApiCtx();
  const [refreshKey, setRefreshKey] = useState(0);
  const [generating, setGenerating] = useState(false);
  const { data, loading, error } = useApi("/api/reports", [refreshKey]);

  const generate = async (period) => {
    setGenerating(true);
    try {
      const res = await fetch(`${apiBase}/api/reports/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ period }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setRefreshKey((k) => k + 1);
    } catch (e) {
      // silencieux — le bandeau d'état affichera déjà l'erreur au prochain fetch
    } finally {
      setGenerating(false);
    }
  };

  const formatSize = (bytes) => bytes > 1024 * 1024 ? `${(bytes / (1024 * 1024)).toFixed(1)} Mo` : `${Math.round(bytes / 1024)} Ko`;
  const rows = data
    ? data.map((r) => ({
        id: r.id, name: r.name, period: r.period === "daily" ? "Quotidien" : "Hebdomadaire",
        format: "PDF", size: formatSize(r.size_bytes),
        when: new Date(r.generated_at).toLocaleString("fr-FR"),
      }))
    : REPORTS.map((r) => ({ ...r, id: null }));

  return (
    <div className="px-6 py-5 overflow-y-auto h-full flex flex-col gap-4">
      <PageTitle>RAPPORTS</PageTitle>
      <ApiStateBanner loading={loading} error={error} />

      <div className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4" style={glass(C)}>
        <div>
          <div className="text-[13px] font-bold" style={{ color: C.text, ...bodyFont }}>Rapports planifiés</div>
          <div className="text-[12px] mt-1" style={{ color: C.textFaint, ...bodyFont }}>Quotidien à 05:00 UTC · Hebdomadaire le lundi à 06:00 UTC — export PDF, généré automatiquement.</div>
        </div>
        <div className="flex gap-2 shrink-0">
          <button onClick={() => generate("daily")} disabled={generating} className="flex items-center gap-2 px-4 py-2 rounded-lg text-[12.5px] font-semibold" style={{ border: `1px solid ${C.turquoise}`, color: C.turquoise, boxShadow: `0 0 10px ${C.turquoise}44`, opacity: generating ? 0.6 : 1, ...bodyFont }}>
            {generating ? <Loader2 size={13} className="animate-spin" /> : <RefreshCw size={13} />} Quotidien
          </button>
          <button onClick={() => generate("weekly")} disabled={generating} className="flex items-center gap-2 px-4 py-2 rounded-lg text-[12.5px] font-semibold" style={{ background: C.panel2, border: `1px solid ${C.borderSoft}`, color: C.textDim, opacity: generating ? 0.6 : 1, ...bodyFont }}>
            Hebdomadaire
          </button>
        </div>
      </div>

      <div className="flex flex-col gap-2.5">
        {rows.map((r, i) => (
          <div key={i} className="flex items-center justify-between p-4" style={glass(C, 14)}>
            <div className="flex items-center gap-3 min-w-0">
              <div className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0" style={{ background: `${C.turquoise}14`, color: C.turquoise }}><FileText size={15} /></div>
              <div className="min-w-0">
                <div className="text-[13px] font-semibold truncate" style={{ color: C.text, ...bodyFont }}>{r.name}</div>
                <div className="flex items-center gap-2 text-[11px] mt-0.5" style={{ color: C.textFaint, ...monoFont }}>
                  <span>{r.period}</span><span>·</span><span>{r.format}</span><span>·</span><span>{r.size}</span><span>·</span><span>{r.when}</span>
                </div>
              </div>
            </div>
            {r.id ? (
              <a href={`${apiBase}/api/reports/${r.id}/download`} target="_blank" rel="noreferrer" className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0" style={{ background: C.panel2, border: `1px solid ${C.borderSoft}` }}><Download size={14} style={{ color: C.textDim }} /></a>
            ) : (
              <button disabled className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 opacity-40" style={{ background: C.panel2, border: `1px solid ${C.borderSoft}` }}><Download size={14} style={{ color: C.textDim }} /></button>
            )}
          </div>
        ))}
        {rows.length === 0 && (
          <div className="text-center py-8 text-[12.5px]" style={{ color: C.textFaint, ...bodyFont }}>Aucun rapport généré pour l'instant.</div>
        )}
      </div>
    </div>
  );
}

/* =================================================================
   PAGE 7 — IA Analyste
================================================================= */
const TOOL_LABEL = {
  search_logs: "Recherche de logs",
  get_stats_overview: "Statistiques agrégées",
  list_devices: "Inventaire des équipements",
};

function ToolCallTag({ call }) {
  const C = useTheme();
  const src = call.args?.source_type;
  return (
    <span className="inline-flex items-center gap-1.5 text-[11px] font-semibold px-2 py-0.5 rounded" style={{ color: C.turquoise, background: `${C.turquoise}14`, ...bodyFont }}>
      <Bot size={11} /> {TOOL_LABEL[call.name] || call.name}
      {src && <span style={{ color: SOURCES.find((s) => s.id === src)?.color }}>· {src}</span>}
    </span>
  );
}

function AgentPage() {
  const C = useTheme();
  const { apiBase } = useApiCtx();
  const [messages, setMessages] = useState([
    { role: "agent", text: "Bonjour ! Posez-moi une question sur vos logs — je peux interroger les journaux et les statistiques en direct." },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const send = async (text) => {
    const t = (text ?? input).trim();
    if (!t || loading) return;
    const history = messages.map((m) => ({ role: m.role, text: m.text }));
    setMessages((m) => [...m, { role: "user", text: t }]);
    setInput("");
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/api/agent/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: t, history }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setMessages((m) => [...m, { role: "agent", text: data.reply, toolCalls: data.tool_calls || [] }]);
    } catch (e) {
      setMessages((m) => [...m, {
        role: "agent",
        text: `Backend injoignable (${e.message}). Vérifie l'URL API et la clé Gemini dans Paramètres.`,
        error: true,
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-full min-h-0">
      <div className="flex flex-col flex-1 min-w-0">
        <div className="px-6 pt-5"><PageTitle>IA ANALYSTE</PageTitle></div>
        <div className="flex-1 overflow-y-auto px-6 flex flex-col gap-5">
          {messages.map((m, i) => m.role === "user" ? (
            <div key={i} className="flex justify-end">
              <div className="max-w-[75%] px-4 py-2.5 rounded-xl rounded-tr-sm text-[13.5px]" style={{ background: `${C.turquoise}14`, border: `1px solid ${C.turquoise}44`, color: C.text, ...bodyFont }}>{m.text}</div>
            </div>
          ) : (
            <div key={i} className="flex gap-3 max-w-[85%]">
              <div className="w-7 h-7 rounded-md flex items-center justify-center shrink-0 mt-0.5" style={{ background: m.error ? `${C.red}1F` : `${C.green}1F`, color: m.error ? C.red : C.green }}><Bot size={13} /></div>
              <div className="p-4" style={glass(C, 14)}>
                <div className="text-[13.5px] leading-relaxed whitespace-pre-wrap" style={{ color: C.text, ...bodyFont }}>{m.text}</div>
                {m.toolCalls && m.toolCalls.length > 0 && (
                  <div className="flex items-center gap-2 flex-wrap mt-3 pt-3" style={{ borderTop: `1px solid ${C.borderSoft}` }}>
                    <span className="text-[10.5px]" style={{ color: C.textFaint, ...monoFont }}>OUTILS UTILISÉS</span>
                    {m.toolCalls.map((call, j) => <ToolCallTag key={j} call={call} />)}
                  </div>
                )}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex gap-3 max-w-[85%]">
              <div className="w-7 h-7 rounded-md flex items-center justify-center shrink-0 mt-0.5" style={{ background: `${C.green}1F`, color: C.green }}><Bot size={13} /></div>
              <div className="p-4 flex items-center gap-2" style={glass(C, 14)}>
                <Loader2 size={14} className="animate-spin" style={{ color: C.textFaint }} />
                <span className="text-[12.5px]" style={{ color: C.textFaint, ...bodyFont }}>Analyse des journaux en cours…</span>
              </div>
            </div>
          )}
        </div>
        <div className="px-6 pb-5 pt-3">
          <div className="flex gap-2 flex-wrap mb-3">
            {AGENT_PROMPTS.map((p, i) => (
              <button key={i} onClick={() => send(p)} disabled={loading} className="text-[12px] px-3 py-1.5 rounded-full" style={{ background: C.panel2, border: `1px solid ${C.borderSoft}`, color: C.textDim, opacity: loading ? 0.5 : 1, ...bodyFont }}>{p}</button>
            ))}
          </div>
          <div className="flex items-center gap-2 px-3 py-2.5 rounded-xl" style={glass(C, 14)}>
            <Sparkles size={15} style={{ color: C.turquoise }} />
            <input value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === "Enter" && send()} disabled={loading} placeholder="Interroger l'IA Analyste — logs, incidents, recommandations…" className="flex-1 bg-transparent outline-none text-[13.5px]" style={{ color: C.text, ...bodyFont }} />
            <button onClick={() => send()} disabled={loading} className="w-7 h-7 rounded-md flex items-center justify-center" style={{ border: `1px solid ${C.turquoise}`, boxShadow: `0 0 10px ${C.turquoise}44`, opacity: loading ? 0.5 : 1 }}>
              {loading ? <Loader2 size={13} className="animate-spin" style={{ color: C.turquoise }} /> : <Send size={13} style={{ color: C.turquoise }} />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

/* =================================================================
   PAGE 8 — Paramètres
================================================================= */
function Toggle({ on, setOn }) {
  const C = useTheme();
  return (
    <button onClick={() => setOn(!on)} className="w-9 h-5 rounded-full relative shrink-0" style={{ background: on ? C.green : C.borderSoft }}>
      <span className="absolute top-0.5 w-4 h-4 rounded-full transition-all" style={{ left: on ? 18 : 2, background: "#fff" }} />
    </button>
  );
}

function SettingsPage() {
  const C = useTheme();
  const { apiBase, setApiBase, connected, mode, setMode } = useApiCtx();
  const [draftApiBase, setDraftApiBase] = useState(apiBase);
  const [emailAlerts, setEmailAlerts] = useState(true);
  const [slackAlerts, setSlackAlerts] = useState(false);
  const [autoBackup, setAutoBackup] = useState(true);

  const users = [
    { name: "A. Doukkali", role: "Administrateur", email: "a.doukkali@entreprise.ma" },
    { name: "s.benali", role: "Analyste SOC", email: "s.benali@entreprise.ma" },
    { name: "k.tazi", role: "Lecture seule", email: "k.tazi@entreprise.ma" },
  ];

  return (
    <div className="px-6 py-5 overflow-y-auto h-full flex flex-col gap-4">
      <PageTitle>PARAMÈTRES</PageTitle>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="p-4" style={glass(C)}>
          <div className="flex items-center gap-2 mb-3"><Palette size={15} style={{ color: C.turquoise }} /><SectionLabel style={{ marginBottom: 0 }}>Apparence</SectionLabel></div>
          <div className="text-[11.5px] mb-3" style={{ color: C.textFaint, ...bodyFont }}>Choisir le thème de l'interface</div>
          <div className="flex gap-2">
            <button onClick={() => setMode("dark")} className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-[12.5px] font-semibold"
              style={{ background: mode === "dark" ? `${C.turquoise}14` : C.panel2, border: `1px solid ${mode === "dark" ? C.turquoise : C.borderSoft}`, color: mode === "dark" ? C.turquoise : C.textDim, ...bodyFont }}>
              <Moon size={14} /> Sombre
            </button>
            <button onClick={() => setMode("light")} className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-[12.5px] font-semibold"
              style={{ background: mode === "light" ? `${C.turquoise}14` : C.panel2, border: `1px solid ${mode === "light" ? C.turquoise : C.borderSoft}`, color: mode === "light" ? C.turquoise : C.textDim, ...bodyFont }}>
              <Sun size={14} /> Clair
            </button>
          </div>
        </div>

        <div className="p-4" style={glass(C)}>
          <div className="flex items-center gap-2 mb-3"><Globe size={15} style={{ color: C.turquoise }} /><SectionLabel style={{ marginBottom: 0 }}>Connexion à l'API ARGUS</SectionLabel></div>
          <div className="text-[11.5px] mb-2" style={{ color: C.textFaint, ...bodyFont }}>URL du backend (vide = même domaine, via reverse proxy)</div>
          <div className="flex items-center gap-2">
            <input
              value={draftApiBase} onChange={(e) => setDraftApiBase(e.target.value)}
              placeholder="ex: https://argus.moncorp.local ou vide"
              className="flex-1 px-3 py-2 rounded-lg text-[12px] outline-none"
              style={{ background: C.panel2, border: `1px solid ${C.borderSoft}`, color: C.text, ...monoFont }}
            />
            <button onClick={() => setApiBase(draftApiBase)} className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0" style={{ border: `1px solid ${C.turquoise}`, color: C.turquoise, boxShadow: `0 0 10px ${C.turquoise}44` }}><Save size={14} /></button>
          </div>
          <div className="flex items-center gap-1.5 mt-3 text-[11.5px] font-semibold" style={{ color: connected ? C.green : C.red, ...bodyFont }}>
            <span className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: connected ? C.green : C.red }} />
            {connected ? "Connecté — /health répond correctement" : "Backend injoignable sur cette URL"}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="p-4" style={glass(C)}>
          <div className="flex items-center gap-2 mb-3"><Users size={15} style={{ color: C.turquoise }} /><SectionLabel style={{ marginBottom: 0 }}>Utilisateurs & permissions</SectionLabel></div>
          <div className="flex flex-col gap-2">
            {users.map((u, i) => (
              <div key={i} className="flex items-center justify-between text-[12px] py-1.5" style={{ borderTop: i > 0 ? `1px solid ${C.borderSoft}` : "none" }}>
                <div>
                  <div className="font-semibold" style={{ color: C.text, ...bodyFont }}>{u.name}</div>
                  <div style={{ color: C.textFaint, ...bodyFont }}>{u.email}</div>
                </div>
                <span className="px-2 py-0.5 rounded text-[10.5px] font-semibold" style={{ color: C.turquoise, background: `${C.turquoise}14`, ...bodyFont }}>{u.role}</span>
              </div>
            ))}
          </div>
          <button className="flex items-center gap-1.5 text-[12px] font-semibold mt-3" style={{ color: C.turquoise, ...bodyFont }}><Plus size={13} /> Ajouter un utilisateur</button>
        </div>

        <div className="p-4" style={glass(C)}>
          <div className="flex items-center gap-2 mb-3"><KeyRound size={15} style={{ color: C.turquoise }} /><SectionLabel style={{ marginBottom: 0 }}>Intégration API</SectionLabel></div>
          <div className="text-[11.5px] mb-2" style={{ color: C.textFaint, ...bodyFont }}>Clé API pour l'agent IA et les intégrations externes</div>
          <div className="flex items-center gap-2 px-3 py-2 rounded-lg" style={{ background: C.panel2, border: `1px solid ${C.borderSoft}` }}>
            <span className="flex-1 text-[12px]" style={{ color: C.textDim, ...monoFont }}>••••••••••••••••••••gk8P</span>
            <button className="text-[11px] font-semibold" style={{ color: C.turquoise, ...bodyFont }}>Régénérer</button>
          </div>
        </div>

        <div className="p-4" style={glass(C)}>
          <div className="flex items-center gap-2 mb-3"><Bell size={15} style={{ color: C.turquoise }} /><SectionLabel style={{ marginBottom: 0 }}>Notifications</SectionLabel></div>
          <div className="flex items-center justify-between py-1.5"><span className="text-[12.5px]" style={{ color: C.text, ...bodyFont }}>Alertes par e-mail</span><Toggle on={emailAlerts} setOn={setEmailAlerts} /></div>
          <div className="flex items-center justify-between py-1.5"><span className="text-[12.5px]" style={{ color: C.text, ...bodyFont }}>Alertes Slack</span><Toggle on={slackAlerts} setOn={setSlackAlerts} /></div>
        </div>

        <div className="p-4" style={glass(C)}>
          <div className="flex items-center gap-2 mb-3"><Mail size={15} style={{ color: C.turquoise }} /><SectionLabel style={{ marginBottom: 0 }}>Serveur SMTP</SectionLabel></div>
          <div className="flex flex-col gap-2 text-[12px]">
            <div className="flex justify-between"><span style={{ color: C.textFaint, ...bodyFont }}>Hôte</span><span style={{ color: C.textDim, ...monoFont }}>smtp.entreprise.ma</span></div>
            <div className="flex justify-between"><span style={{ color: C.textFaint, ...bodyFont }}>Port</span><span style={{ color: C.textDim, ...monoFont }}>587 (TLS)</span></div>
            <div className="flex justify-between"><span style={{ color: C.textFaint, ...bodyFont }}>Expéditeur</span><span style={{ color: C.textDim, ...monoFont }}>argus@entreprise.ma</span></div>
          </div>
        </div>

        <div className="p-4" style={glass(C)}>
          <div className="flex items-center gap-2 mb-3"><Database size={15} style={{ color: C.turquoise }} /><SectionLabel style={{ marginBottom: 0 }}>Sauvegarde</SectionLabel></div>
          <div className="flex items-center justify-between py-1.5"><span className="text-[12.5px]" style={{ color: C.text, ...bodyFont }}>Sauvegarde automatique quotidienne</span><Toggle on={autoBackup} setOn={setAutoBackup} /></div>
          <div className="text-[11.5px] mt-1" style={{ color: C.textFaint, ...bodyFont }}>Dernière sauvegarde : aujourd'hui à 03:00</div>
        </div>

        <div className="p-4" style={glass(C)}>
          <div className="flex items-center gap-2 mb-3"><ShieldCheck size={15} style={{ color: C.turquoise }} /><SectionLabel style={{ marginBottom: 0 }}>Licence</SectionLabel></div>
          <div className="flex flex-col gap-2 text-[12px]">
            <div className="flex justify-between"><span style={{ color: C.textFaint, ...bodyFont }}>Plan</span><span style={{ color: C.turquoise, fontWeight: 700, ...bodyFont }}>ARGUS Enterprise</span></div>
            <div className="flex justify-between"><span style={{ color: C.textFaint, ...bodyFont }}>Équipements couverts</span><span style={{ color: C.textDim, ...monoFont }}>6 / 25</span></div>
            <div className="flex justify-between"><span style={{ color: C.textFaint, ...bodyFont }}>Expiration</span><span style={{ color: C.textDim, ...monoFont }}>14/03/2027</span></div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ---------------------------------------------------------------
   Root
--------------------------------------------------------------- */
const PAGES = {
  dashboard: DashboardPage, logs: LogsPage, equip: EquipPage, alerts: AlertsPage,
  query: QueryPage, reports: ReportsPage, agent: AgentPage, settings: SettingsPage,
};

export default function ArgusApp() {
  const [page, setPage] = useState("dashboard");
  const [mode, setMode] = useState(() => localStorage.getItem("argus_theme") || "dark");
  // Vide par défaut = chemins relatifs (/api/...), fonctionne nativement derrière le
  // reverse proxy (Caddy) qui sert le frontend ET l'API sur le même domaine.
  // En dev local (npm run dev), Vite proxie déjà /api vers le backend (voir vite.config.js).
  const [apiBase, setApiBase] = useState(() => localStorage.getItem("argus_api_base") ?? "");
  const [connected, setConnected] = useState(false);
  const C = PALETTES[mode];
  const Page = PAGES[page];

  useEffect(() => { localStorage.setItem("argus_theme", mode); }, [mode]);
  useEffect(() => { localStorage.setItem("argus_api_base", apiBase); }, [apiBase]);

  // Vérifie périodiquement /health pour refléter l'état réel du backend
  // (utilisé par le badge "Système Opérationnel" de la sidebar et Paramètres).
  useEffect(() => {
    let cancelled = false;
    const check = () => {
      fetch(`${apiBase}/health`)
        .then((r) => { if (!cancelled) setConnected(r.ok); })
        .catch(() => { if (!cancelled) setConnected(false); });
    };
    check();
    const id = setInterval(check, 15000);
    return () => { cancelled = true; clearInterval(id); };
  }, [apiBase]);

  return (
    <ThemeCtx.Provider value={C}>
      <ApiCtx.Provider value={{ apiBase, setApiBase, connected, mode, setMode }}>
        <div className="w-full h-screen flex transition-colors duration-200" style={{ background: `linear-gradient(180deg, ${C.bg} 0%, ${C.bgAlt} 60%, ${C.bgAlt2} 100%)`, ...bodyFont }}>
          <style>{`@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Poppins:wght@600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');`}</style>
          <Sidebar page={page} setPage={setPage} />
          <div className="flex-1 min-w-0 h-full">
            <Page />
          </div>
        </div>
      </ApiCtx.Provider>
    </ThemeCtx.Provider>
  );
}
