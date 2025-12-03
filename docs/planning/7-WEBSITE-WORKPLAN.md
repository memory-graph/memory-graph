# MemoryGraph Marketing Website Plan

## Vision

A retro-inspired marketing site that stands out from the sea of identical SaaS landing pages. The aesthetic evokes the "golden age" of computing—when software felt personal and developers were explorers—while delivering modern UX and conversion optimization.

**Target vibe**: 90s terminal/BBS aesthetic meets modern developer tool. Think: the nostalgia of early computing, the excitement of discovery, the warmth of a tool that "gets" you.

**Why retro works for MemoryGraph**:
- Memory itself is nostalgic—we're literally helping AI "remember"
- Developer tools with personality stand out (see: Stripe's early days, Vercel's boldness)
- Counter-cultural to the sterile, corporate AI tool landscape
- Creates emotional connection—memorable (pun intended)

---

## Design Direction

### Era: Late 80s / Early 90s Terminal + Early Web

**Primary aesthetic elements**:
- Monospace fonts (IBM Plex Mono, JetBrains Mono, or custom pixel font)
- Terminal green (#00FF00) or amber (#FFB000) on dark backgrounds
- Scanline effects (subtle CSS overlay)
- Pixel art icons and illustrations
- ASCII art headers and dividers
- CRT screen glow effects (box-shadow, blur)
- Blinking cursors
- "Window" chrome (title bars, close buttons, drag handles)

**Secondary elements**:
- Starfield or grid backgrounds
- Glitch effects on hover (subtle)
- Typing animations for headlines
- Retro button styles (beveled, 3D)
- "Loading" animations that feel nostalgic

### Color Palette

**Option A: Terminal Green**
```
Background: #0a0a0a (near black)
Primary: #00FF00 (terminal green)
Secondary: #00CC00 (darker green)
Accent: #FFFF00 (warning yellow)
Text: #CCCCCC (light gray)
Highlight: #00FF00 with glow
```

**Option B: Amber Terminal**
```
Background: #1a1a0a (warm black)
Primary: #FFB000 (amber)
Secondary: #CC8800 (darker amber)
Accent: #FF6600 (orange)
Text: #CCBB99 (warm gray)
Highlight: #FFB000 with glow
```

**Option C: Vaporwave (bolder)**
```
Background: #0f0f23 (deep purple-black)
Primary: #00FFFF (cyan)
Secondary: #FF00FF (magenta)
Accent: #FFFF00 (yellow)
Text: #E0E0FF (light lavender)
Gradients: cyan → magenta
```

**Recommendation**: Option A (Terminal Green) for credibility with developers, with subtle Option C accents for visual interest.

### Typography

**Headlines**: 
- Primary: Pixelated/bitmap font (e.g., "Press Start 2P", "VT323", custom)
- Fallback: IBM Plex Mono Bold

**Body**:
- IBM Plex Mono or JetBrains Mono
- 16-18px base size for readability

**Code blocks**:
- Fira Code (with ligatures)
- Terminal-style background with slight glow

---

## Site Structure

```
memorygraph.dev/
├── / (Landing Page)
├── /docs (Documentation - can link to GitHub or separate)
├── /pricing (If applicable for future paid tiers)
├── /blog (Optional - for launch post, updates)
└── /about (Optional - story, team)
```

### Landing Page Sections

```
┌─────────────────────────────────────────────────────────────────┐
│ [HEADER: Logo + Nav]                                            │
│  memorygraph_                    Docs | GitHub | Discord        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ [HERO SECTION]                                                  │
│                                                                 │
│  > MEMORY FOR YOUR AI CODING AGENT_                             │
│                                                                 │
│  Never re-explain your project again.                           │
│  Claude Code remembers what worked.                             │
│                                                                 │
│  ┌──────────────────────────────────────┐                       │
│  │ $ pip install memorygraphMCP        │                       │
│  │ $ claude mcp add memorygraph        │                       │
│  │ ✓ Ready. Your AI now has a memory.  │                       │
│  └──────────────────────────────────────┘                       │
│                                                                 │
│  [GET STARTED] [VIEW ON GITHUB]                                 │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ [DEMO GIF/VIDEO]                                                │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                                                         │    │
│  │   Animated terminal showing:                            │    │
│  │   1. Install command                                    │    │
│  │   2. "Remember: retry with backoff fixed timeouts"      │    │
│  │   3. New session: "What fixed the timeout issue?"       │    │
│  │   4. Claude recalls the solution                        │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ [PROBLEM/SOLUTION - "The Struggle"]                             │
│                                                                 │
│  WITHOUT MEMORY:                    WITH MEMORYGRAPH:           │
│  ┌────────────────────┐            ┌────────────────────┐       │
│  │ Session 1:         │            │ Session 1:         │       │
│  │ "Here's my arch.." │            │ "Remember this..." │       │
│  │                    │            │                    │       │
│  │ Session 2:         │            │ Session 2:         │       │
│  │ "Here's my arch.." │            │ "Continue where    │       │
│  │ (again)            │            │  we left off"      │       │
│  │                    │            │                    │       │
│  │ Session 3:         │            │ Session 3:         │       │
│  │ "Here's my arch.." │            │ Claude already     │       │
│  │ (seriously?)       │            │  knows ✓           │       │
│  └────────────────────┘            └────────────────────┘       │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ [FEATURES - Terminal Window Style]                              │
│                                                                 │
│  ┌─ FEATURES ─────────────────────────────────────── □ ─ × ─┐   │
│  │                                                          │   │
│  │  > PERSISTENT MEMORY                                     │   │
│  │    Store solutions, patterns, and decisions              │   │
│  │    that survive across sessions.                         │   │
│  │                                                          │   │
│  │  > RELATIONSHIP TRACKING                                 │   │
│  │    Know what SOLVED what. What CAUSED what.              │   │
│  │    Not just notes—connected knowledge.                   │   │
│  │                                                          │   │
│  │  > ZERO CONFIG                                           │   │
│  │    SQLite by default. Works offline.                     │   │
│  │    Your data never leaves your machine.                  │   │
│  │                                                          │   │
│  │  > PROJECT AWARE                                         │   │
│  │    Organize memories by project.                         │   │
│  │    Switch contexts cleanly.                              │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ [HOW IT WORKS - Animated/Interactive]                           │
│                                                                 │
│  STEP 1: STORE                                                  │
│  ════════════════                                               │
│  "Remember: exponential backoff fixed the API timeouts"         │
│                        ↓                                        │
│  ┌─────────────────────────────────────┐                        │
│  │ Entity: ExponentialBackoff          │                        │
│  │ Type: Solution                      │                        │
│  │ Relationship: SOLVES → APITimeout   │                        │
│  └─────────────────────────────────────┘                        │
│                                                                 │
│  STEP 2: RECALL                                                 │
│  ═══════════════                                                │
│  "What fixed the timeout issues?"                               │
│                        ↓                                        │
│  Claude searches → Finds ExponentialBackoff → Returns answer    │
│                                                                 │
│  STEP 3: BUILD ON IT                                            │
│  ═══════════════════                                            │
│  Next time you hit a timeout, Claude already knows the fix.     │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ [SOCIAL PROOF / TESTIMONIALS]                                   │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ "Finally, Claude Code doesn't forget everything        │     │
│  │  between sessions. Game changer for long projects."    │     │
│  │                                    — @developer        │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                 │
│  (Initially can use: GitHub stars, download count,              │
│   or placeholder for future testimonials)                       │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ [COMPARISON TABLE - vs Alternatives]                            │
│                                                                 │
│  <details> style accordion:                                     │
│                                                                 │
│  > How does this compare to CLAUDE.md?                          │
│    CLAUDE.md is static. MemoryGraph is dynamic and searchable.  │
│                                                                 │
│  > How does this compare to basic-memory?                       │
│    basic-memory is general-purpose PKM. MemoryGraph is          │
│    purpose-built for coding workflows with typed relationships. │
│                                                                 │
│  > What about Anthropic's built-in memory?                      │
│    MemoryGraph gives you control, visibility, and portability.  │
│    Your data stays local. You own it.                           │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ [CTA - Final Push]                                              │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                                                          │   │
│  │   READY TO GIVE YOUR AI A MEMORY?                        │   │
│  │                                                          │   │
│  │   $ pip install memorygraphMCP && claude mcp add memorygraph │
│  │                                                          │   │
│  │   [COPY COMMAND]  [READ THE DOCS]  [JOIN DISCORD]        │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│ [FOOTER]                                                        │
│  memorygraph © 2025 | MIT License | GitHub | Discord            │
│  Made with ♥ for Claude Code users                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Interactive Elements

### 1. Typing Animation for Headlines
```css
/* Typewriter effect for hero headline */
.typewriter {
  overflow: hidden;
  border-right: .15em solid #00FF00;
  white-space: nowrap;
  animation: typing 2s steps(40, end), blink-caret .75s step-end infinite;
}
```

### 2. Terminal Demo (Interactive)
- Allow visitors to "type" commands in a fake terminal
- Show realistic output as if they're using MemoryGraph
- Copy-to-clipboard for real install command

### 3. Scanline Overlay
```css
.scanlines::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: repeating-linear-gradient(
    0deg,
    rgba(0, 0, 0, 0.15),
    rgba(0, 0, 0, 0.15) 1px,
    transparent 1px,
    transparent 2px
  );
  pointer-events: none;
}
```

### 4. CRT Glow Effect
```css
.terminal-window {
  box-shadow: 
    0 0 10px rgba(0, 255, 0, 0.3),
    0 0 20px rgba(0, 255, 0, 0.2),
    0 0 30px rgba(0, 255, 0, 0.1);
}
```

### 5. ASCII Art Logo
```
                                                           _     
 _ __ ___   ___ _ __ ___   ___  _ __ _   _  __ _ _ __ __ _ _ __ | |__  
| '_ ` _ \ / _ \ '_ ` _ \ / _ \| '__| | | |/ _` | '__/ _` | '_ \| '_ \ 
| | | | | |  __/ | | | | | (_) | |  | |_| | (_| | | | (_| | |_) | | | |
|_| |_| |_|\___|_| |_| |_|\___/|_|   \__, |\__, |_|  \__,_| .__/|_| |_|
                                     |___/ |___/          |_|          
```

---

## Technical Implementation

### Recommended Stack

**Option A: Static Site (Recommended for launch)**
- **Framework**: Astro (fast, static, great DX)
- **Styling**: Tailwind CSS + custom retro components
- **Hosting**: Cloudflare Pages or Vercel (free tier)
- **Domain**: memorygraph.dev

**Option B: React-based (if more interactivity needed)**
- **Framework**: Next.js (static export)
- **Styling**: Tailwind + Framer Motion for animations
- **Hosting**: Vercel

### Key Pages

1. **Landing Page** (`/`)
   - All sections above
   - Primary conversion goal: Get visitors to install

2. **Documentation** (`/docs` or external)
   - Can link to GitHub README initially
   - Later: Dedicated docs site (Docusaurus, Mintlify, or Astro Starlight)

3. **Pricing** (`/pricing`) - Future
   - Free tier details
   - Pro tier ($8/month) when cloud sync launches
   - Team tier ($12/user/month) when ready

### Assets Needed

**Graphics**:
- [ ] Logo (text-based, terminal style, or pixel art)
- [ ] Favicon (16x16, 32x32 pixel art)
- [ ] Open Graph image (1200x630 for social sharing)
- [ ] Demo GIF or video (asciinema recording)
- [ ] Pixel art icons for features (4-6 icons)

**Copy**:
- [ ] Hero headline and subhead
- [ ] Feature descriptions (4-6)
- [ ] How it works steps
- [ ] FAQ/comparison answers
- [ ] Meta description for SEO

**Technical**:
- [ ] Install command snippets
- [ ] Code examples for demo
- [ ] Terminal animation script

---

## SEO & Marketing Integration

### Meta Tags
```html
<title>MemoryGraph - Memory for AI Coding Agents</title>
<meta name="description" content="Never re-explain your project to Claude Code again. MemoryGraph gives your AI assistant persistent memory that remembers what worked.">
<meta property="og:image" content="/og-image.png">
```

### Target Keywords
- "Claude Code memory"
- "MCP memory server"
- "AI coding assistant memory"
- "Claude context persistence"
- "Claude Code tools"

### Launch Integration
- Links to GitHub, PyPI, Discord
- Analytics (Plausible or PostHog - privacy-friendly)
- Email capture for updates (optional)

---

## Development Phases

### Phase 1: MVP Landing Page (1-2 days)
- [ ] Set up Astro project with Tailwind
- [ ] Create basic page structure
- [ ] Implement terminal aesthetic (colors, fonts, glow)
- [ ] Hero section with install command
- [ ] Features section
- [ ] Footer with links
- [ ] Deploy to Cloudflare Pages

### Phase 2: Polish & Assets (1-2 days)
- [ ] Record asciinema demo
- [ ] Create/source pixel art icons
- [ ] Add typing animations
- [ ] Implement scanline/CRT effects
- [ ] Create Open Graph image
- [ ] Add comparison section

### Phase 3: Launch Readiness (1 day)
- [ ] Connect custom domain
- [ ] Add analytics
- [ ] Test on mobile
- [ ] Cross-browser testing
- [ ] Performance optimization
- [ ] Final copy review

### Phase 4: Post-Launch Iteration
- [ ] Add testimonials as they come in
- [ ] Blog for updates
- [ ] Pricing page when ready
- [ ] Docs site integration

---

## Inspiration Links

**Retro/Terminal Developer Sites**:
- https://www.windows93.net/ (interactive retro OS)
- https://poolside.fm/ (retro aesthetic, modern site)
- https://bruno-simon.com/ (creative, memorable)

**Developer Tool Sites with Personality**:
- https://linear.app/ (bold, distinctive)
- https://ray.so/ (clean but memorable)
- https://warp.dev/ (terminal-focused)

**Retro Design Resources**:
- https://www.awwwards.com/websites/retro/
- https://www.lapa.ninja/category/retro-style/
- https://gifcities.org/ (retro GIFs from Geocities)

**Fonts**:
- https://fonts.google.com/specimen/VT323
- https://fonts.google.com/specimen/Press+Start+2P
- https://www.jetbrains.com/lp/mono/

---

## Success Metrics

| Metric | Target (Month 1) |
|--------|------------------|
| Unique visitors | 2,000+ |
| GitHub stars from site | 50+ |
| PyPI installs attributed to site | 500+ |
| Discord joins from site | 100+ |
| Average time on page | >60 seconds |
| Bounce rate | <60% |

---

## Budget Estimate

| Item | Cost |
|------|------|
| Domain (memorygraph.dev) | ~$12/year |
| Hosting (Cloudflare Pages) | Free |
| Fonts (Google Fonts) | Free |
| Icons (custom or free sources) | Free or ~$20 |
| Demo video (asciinema) | Free |
| Analytics (Plausible) | Free tier or $9/month |
| **Total Launch Cost** | **~$12-50** |

---

## Next Steps

1. **Register domain**: memorygraph.dev (if not already done)
2. **Choose color palette**: Terminal Green vs Amber vs Vaporwave
3. **Create logo**: Text-based ASCII or simple pixel art
4. **Set up Astro project**: Basic structure with Tailwind
5. **Build MVP**: Hero + Features + Install command + Footer
6. **Record demo**: asciinema terminal recording
7. **Deploy and iterate**

---

## Notes

The retro aesthetic should enhance, not hinder:
- **Readability first**: Retro fonts are fun but must be legible
- **Mobile works**: Retro doesn't mean broken on phones
- **Fast loading**: No heavy assets that slow the site
- **Accessible**: Contrast ratios, focus states, semantic HTML
- **Professional**: Nostalgic ≠ unprofessional

The goal is a site that makes developers smile, feel understood, and think "I need to try this."
