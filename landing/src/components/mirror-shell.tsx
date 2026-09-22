import { Link } from "@tanstack/react-router";
import { Menu, X } from "lucide-react";
import { useState, type ReactNode } from "react";
import { Button } from "@/components/ui/button";

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
  { label: "Pricing", to: "/pricing" as const },
  { label: "Contact", to: "/contact" as const },
];

export function SiteHeader() {
  const [open, setOpen] = useState(false);
  return (
    <header className="fixed inset-x-0 top-0 z-50 px-3 pt-3 sm:px-6 sm:pt-5">
      <div className="mx-auto grid max-w-7xl grid-cols-[minmax(0,1fr)_auto] items-center rounded-full border border-border/70 bg-background/85 px-5 py-3 shadow-soft backdrop-blur-xl sm:flex sm:justify-between">
        <Link to="/" className="min-w-0 text-foreground" aria-label="mirror home"><MirrorMark compact /></Link>
        <nav className="hidden items-center gap-8 md:flex" aria-label="Main navigation">
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

export function StoreBadges() {
  return (
    <div id="download" className="flex flex-wrap gap-3">
      <a href="https://www.apple.com/app-store/" target="_blank" rel="noreferrer" className="store-badge" aria-label="Download on the App Store">
        <span className="text-lg">●</span><span><small>Download on the</small>App Store</span>
      </a>
      <a href="https://play.google.com/store" target="_blank" rel="noreferrer" className="store-badge" aria-label="Get it on Google Play">
        <span className="text-lg">▶</span><span><small>Get it on</small>Google Play</span>
      </a>
    </div>
  );
}

export function SiteFooter() {
  return (
    <footer className="border-t border-border px-5 py-14 sm:px-8">
      <div className="mx-auto grid max-w-7xl gap-10 md:grid-cols-[1fr_auto] md:items-end">
        <div><MirrorMark /><p className="mt-5 max-w-sm text-sm text-muted-foreground">Private, precise makeup simulation shaped for Nigerian beauty and professional artistry.</p></div>
        <div className="flex flex-wrap gap-x-8 gap-y-3 text-sm">
          <Link to="/">Experience</Link><Link to="/pricing">Pricing</Link><Link to="/contact">Support & inquiries</Link>
        </div>
      </div>
      <div className="mx-auto mt-12 flex max-w-7xl flex-col gap-2 border-t border-border pt-5 text-xs text-muted-foreground sm:flex-row sm:justify-between">
        <span>© 2026 mirror atelier.</span><span>Created for Nigerian beauty.</span>
      </div>
    </footer>
  );
}

export function PageShell({ children }: { children: ReactNode }) {
  return <div className="min-h-screen overflow-hidden bg-background text-foreground"><SiteHeader />{children}<SiteFooter /></div>;
}