import { Link } from "@tanstack/react-router";
import { Menu, X, Download, ShieldAlert } from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";
import { Button } from "@/components/ui/button";

// mirrorcentral's own deployed URL, not this landing deployment's own origin - the landing page
// and backend are separate Vercel projects joined by a domain split (see vercel.json in the
// mirrorcentral repo root), so this has to be absolute.
const BACKEND_URL = "https://mirrorcentral.vercel.app";

type AppVersion = {
  version_name: string;
  download_url: string;
  release_notes: string;
};

export function MirrorMark({ compact = false }: { compact?: boolean }) {
  return (
    <div className="flex items-center gap-3" aria-label="mirror home">
      <svg className={compact ? "h-7 w-8" : "h-9 w-11"} viewBox="0 0 48 40" fill="none" aria-hidden="true">
        <path d="M5 35V5l19 21L43 5v30" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M24 26 43 5v30" stroke="currentColor" strokeOpacity=".35" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      <span className="font-display text-2xl lowercase">mirror</span>
    </div>
  );
}

const navItems = [
  { label: "Experience", to: "/" as const },
  { label: "How it works", to: "/guide" as const },
  { label: "About", to: "/about" as const },
  { label: "Pricing", to: "/pricing" as const },
  { label: "Contact", to: "/contact" as const },
];

const jcnAssets = import.meta.glob("/src/assets/jcn/*.{png,svg,webp,jpg,jpeg}", { eager: true, query: "?url", import: "default" }) as Record<string, string>;
const jcnAsset = (name: string) => Object.entries(jcnAssets).find(([path]) => path.split("/").pop()?.startsWith(name))?.[1];

/** Shown, deliberately small and quiet, at the very bottom of every page. */
export function PoweredBy() {
  const mark = jcnAsset("jcn-mark");
  const logo = jcnAsset("jcn-logo");
  return (
    <p className="flex items-center justify-center gap-1.5 text-[.6rem] uppercase tracking-[.16em] text-muted-foreground/60">
      <span>Powered by</span>
      {mark && <img src={mark} alt="" aria-hidden="true" className="h-3 w-auto opacity-60" />}
      {logo ? <img src={logo} alt="JCN" className="h-2.5 w-auto opacity-60" /> : <span className="font-semibold">JCN</span>}
    </p>
  );
}

export function SiteHeader() {
  const [open, setOpen] = useState(false);
  return (
    <header className="fixed inset-x-0 top-0 z-50 px-3 pt-3 sm:px-6 sm:pt-5">
      <div className="mx-auto grid max-w-7xl grid-cols-[minmax(0,1fr)_auto] items-center rounded-full border border-border/70 bg-background/85 px-5 py-3 shadow-soft backdrop-blur-xl sm:flex sm:justify-between">
        <Link to="/" className="min-w-0 text-foreground" aria-label="mirror home"><MirrorMark compact /></Link>
        <nav className="hidden items-center gap-6 lg:gap-8 md:flex" aria-label="Main navigation">
          {navItems.map((item) => (
            <Link key={item.to} to={item.to} activeOptions={{ exact: item.to === "/" }} className="nav-link" activeProps={{ className: "nav-link text-primary" }}>{item.label}</Link>
          ))}
        </nav>
        <div className="hidden items-center gap-2 md:flex">
          <Button asChild variant="ghost" className="rounded-full px-5"><Link to="/pricing">Subscribe</Link></Button>
          <Button asChild className="rounded-full px-6"><a href="#download">Download</a></Button>
        </div>
        <Button variant="ghost" size="icon" className="shrink-0 rounded-full md:hidden" onClick={() => setOpen((value) => !value)} aria-label={open ? "Close menu" : "Open menu"}>
          {open ? <X /> : <Menu />}
        </Button>
      </div>
      {open && (
        <nav className="mx-auto mt-2 flex max-w-7xl flex-col rounded-3xl border border-border bg-background p-3 shadow-soft md:hidden" aria-label="Mobile navigation">
          {navItems.map((item) => <Link key={item.to} to={item.to} onClick={() => setOpen(false)} className="rounded-full px-5 py-3 text-sm">{item.label}</Link>)}
          <Button asChild className="mt-2 rounded-full"><Link to="/pricing">Choose a plan</Link></Button>
        </nav>
      )}
    </header>
  );
}

/**
 * mirror isn't distributed through the Play Store or App Store - it's a direct .apk download,
 * since there's no store review step to wait on for an MVP. Fetches the current release from
 * mirrorcentral's /app/version so this never links to a stale build, and includes the "Chrome
 * blocked this download" troubleshooting steps inline, since that's the single most common
 * reason a direct-APK download fails on Android.
 */
export function StoreBadges() {
  const [release, setRelease] = useState<AppVersion | null>(null);
  const [failed, setFailed] = useState(false);
  const [showHelp, setShowHelp] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetch(`${BACKEND_URL}/app/version?platform=android`)
      .then((res) => (res.ok ? res.json() : Promise.reject(res.status)))
      .then((data: AppVersion) => { if (!cancelled) setRelease(data); })
      .catch(() => { if (!cancelled) setFailed(true); });
    return () => { cancelled = true; };
  }, []);

  return (
    <div id="download" className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-3">
        {release ? (
          <a href={release.download_url} className="store-badge" aria-label={`Download mirror ${release.version_name} for Android`}>
            <Download className="size-5" />
            <span><small>Download for Android</small>v{release.version_name}</span>
          </a>
        ) : (
          <span className="store-badge pointer-events-none opacity-60" aria-live="polite">
            <Download className="size-5" />
            <span><small>Download for Android</small>{failed ? "Not available yet" : "Checking…"}</span>
          </span>
        )}
        <button
          type="button"
          onClick={() => setShowHelp((value) => !value)}
          className="inline-flex items-center gap-1.5 text-xs text-muted-foreground underline underline-offset-4 hover:text-foreground"
        >
          <ShieldAlert className="size-3.5" /> Download blocked or won't install?
        </button>
      </div>
      {showHelp && (
        <div className="max-w-md rounded-2xl border border-border bg-card p-5 text-sm leading-relaxed text-muted-foreground">
          <p className="font-medium text-foreground">If your browser blocks the download:</p>
          <p className="mt-1">Chrome and some other browsers flag direct .apk downloads by default. Try again, or switch to another browser (Firefox and Samsung Internet usually allow it).</p>
          <p className="mt-3 font-medium text-foreground">If Android won't install it:</p>
          <p className="mt-1">Go to <strong>Settings → Apps → [your browser] → Install unknown apps</strong> and turn it on for that app, then open the downloaded file again. Once mirror is installed, turn that setting back off — it's safest left disabled when you're not actively installing something.</p>
        </div>
      )}
    </div>
  );
}

export function SiteFooter() {
  return (
    <footer className="border-t border-border px-5 pb-8 pt-14 sm:px-8">
      <div className="mx-auto grid max-w-7xl gap-10 md:grid-cols-[1fr_auto] md:items-end">
        <div><MirrorMark /><p className="mt-5 max-w-sm text-sm text-muted-foreground">Private, precise makeup simulation shaped for Nigerian beauty and professional artistry.</p></div>
        <div className="flex flex-wrap gap-x-8 gap-y-3 text-sm">
          <Link to="/">Experience</Link><Link to="/guide">How it works</Link><Link to="/about">About</Link><Link to="/pricing">Pricing</Link><Link to="/contact">Support & inquiries</Link>
        </div>
      </div>
      <div className="mx-auto mt-12 flex max-w-7xl flex-col gap-2 border-t border-border pt-5 text-xs text-muted-foreground sm:flex-row sm:justify-between">
        <span>© 2026 mirror atelier.</span>
        <span>Created for Nigerian beauty.</span>
      </div>
      <div className="mx-auto mt-8 max-w-7xl"><PoweredBy /></div>
    </footer>
  );
}

export function PageShell({ children }: { children: ReactNode }) {
  return <div className="min-h-screen overflow-hidden bg-background text-foreground"><SiteHeader />{children}<SiteFooter /></div>;
}