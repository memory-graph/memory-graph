# Workplan 17: memorygraph.dev Website (v1.0.0)

> ## ❌ DEPRECATED (2025-12-06)
>
> **This workplan has been superseded by the memorygraph.dev repository.**
>
> ### What Happened
> - Marketing website was built in `/Users/gregorydickson/memorygraph.dev/`
> - Website is live at https://memorygraph.dev
> - Spanish translations complete
>
> ### Where to Find the Active Work
> - **Replacement**: `memorygraph.dev/docs/planning/3-WORKPLAN-marketing-site.md`
> - **Live Site**: https://memorygraph.dev
> - **Status**: ✅ COMPLETE
>
> ### Do NOT use this workplan for implementation.
>
> ---

**Version Target**: v1.0.0
**Priority**: ~~HIGH~~ DEPRECATED
**Prerequisites**:
- ~~Domain registered (memorygraph.dev)~~
- ~~Workplan 14 Section 2 (Cloudflare Pages setup)~~
- See memorygraph.dev workplans instead
**Estimated Effort**: ~~12-16 hours~~ N/A (already implemented)
**Status**: ❌ DEPRECATED

---

## Overview

~~Build the marketing website for memorygraph.dev with retro-terminal aesthetic. Merge content from deprecated 7-WEBSITE-WORKPLAN and add cloud-specific sections.~~

**This work was completed in the memorygraph.dev repository. Site is live at https://memorygraph.dev**

**Design Philosophy**: 90s terminal/BBS aesthetic meets modern developer tool. Memorable, personality-driven, stands out from sterile SaaS landing pages.

**Target vibe**: The nostalgia of early computing + the excitement of discovery + modern UX.

---

## Goal

Create a marketing website that:
- Converts visitors to users (signup/install)
- Showcases features and benefits
- Differentiates from competitors (Cipher, Graphiti)
- Provides documentation and pricing
- Loads fast (<2s)
- Works on all devices

---

## Success Criteria

- [ ] Website live at memorygraph.dev
- [ ] Load time <2 seconds
- [ ] Works on mobile, tablet, desktop
- [ ] All sections complete (hero, features, pricing, docs)
- [ ] Comparison page published
- [ ] Lighthouse score >90
- [ ] Analytics tracking active

---

## Section 1: Design System

### 1.1 Color Palette (Terminal Green Theme)

**Colors**:
```css
/* Terminal Green (chosen option) */
--background: #0a0a0a;          /* Near black */
--primary: #00FF00;             /* Terminal green */
--secondary: #00CC00;           /* Darker green */
--accent: #FFFF00;              /* Warning yellow */
--text: #CCCCCC;                /* Light gray */
--text-dim: #666666;            /* Dimmed text */
--glow: rgba(0, 255, 0, 0.5);   /* Green glow */
```

**Usage**:
- Background: Dark terminal background
- Primary: Headlines, links, buttons
- Accent: CTAs, important highlights
- Text: Body copy

**Tasks**:
- [ ] Create CSS variables for colors
- [ ] Test contrast ratios (WCAG AA compliance)
- [ ] Create color utility classes

### 1.2 Typography

**Fonts**:
- Headlines: **IBM Plex Mono Bold** (or VT323 for more retro)
- Body: **IBM Plex Mono** (16-18px)
- Code: **Fira Code** (with ligatures)

**CDN Links**:
```html
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;700&family=Fira+Code&display=swap" rel="stylesheet">
```

**Tasks**:
- [ ] Add font imports to layout
- [ ] Create typography utility classes
- [ ] Set up responsive font sizes
- [ ] Test readability on various devices

### 1.3 Visual Effects

**Scanline Effect**:
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
  z-index: 1000;
}
```

**CRT Glow**:
```css
.terminal-window {
  box-shadow:
    0 0 10px rgba(0, 255, 0, 0.3),
    0 0 20px rgba(0, 255, 0, 0.2),
    0 0 30px rgba(0, 255, 0, 0.1);
}
```

**Blinking Cursor**:
```css
.cursor {
  animation: blink 1s step-end infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  50.1%, 100% { opacity: 0; }
}
```

**Tasks**:
- [ ] Implement scanline effect (subtle, not distracting)
- [ ] Implement CRT glow on terminal windows
- [ ] Implement blinking cursor animation
- [ ] Test performance (effects should be GPU-accelerated)

---

## Section 2: Landing Page Structure

### 2.1 Header/Nav

**Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│ memorygraph_          Docs | GitHub | Discord | Login       │
└─────────────────────────────────────────────────────────────┘
```

**File**: `website/src/components/Header.astro`

```astro
---
const navLinks = [
  { href: "/docs", label: "Docs" },
  { href: "https://github.com/gregorydickson/memory-graph", label: "GitHub" },
  { href: "/discord", label: "Discord" },
  { href: "/login", label: "Login" }
];
---

<header class="bg-background border-b border-primary">
  <nav class="container mx-auto px-4 py-4 flex justify-between items-center">
    <a href="/" class="text-2xl font-bold text-primary">memorygraph_</a>
    <ul class="flex gap-6">
      {navLinks.map(link => (
        <li><a href={link.href} class="text-primary hover:text-accent">{link.label}</a></li>
      ))}
    </ul>
  </nav>
</header>
```

**Tasks**:
- [ ] Create header component
- [ ] Add responsive nav (hamburger menu on mobile)
- [ ] Add active link highlighting
- [ ] Test on all breakpoints

### 2.2 Hero Section

**Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  > MEMORY FOR YOUR AI CODING AGENT_                         │
│                                                             │
│  Never re-explain your project again.                       │
│  Claude Code remembers what worked.                         │
│                                                             │
│  ┌──────────────────────────────────────┐                   │
│  │ $ pip install memorygraphMCP        │                   │
│  │ $ claude mcp add memorygraph        │                   │
│  │ ✓ Ready. Your AI now has a memory.  │                   │
│  └──────────────────────────────────────┘                   │
│                                                             │
│  [GET STARTED] [VIEW ON GITHUB]                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**File**: `website/src/components/Hero.astro`

**Tasks**:
- [ ] Create hero component with typing animation
- [ ] Add terminal window with install commands
- [ ] Add CTA buttons
- [ ] Add copy-to-clipboard for commands
- [ ] Implement typing effect for headline

### 2.3 Demo Section

**File**: `website/src/components/Demo.astro`

**Content**:
- Animated terminal showing:
  1. Installing MemoryGraph
  2. Storing a solution: "Remember: retry with backoff fixed timeouts"
  3. New session: "What fixed the timeout issue?"
  4. Claude recalls the solution

**Tasks**:
- [ ] Record asciinema demo
- [ ] Convert to animated GIF or video
- [ ] Embed in demo section
- [ ] Add fallback image if video fails to load

### 2.4 Problem/Solution Section

**Layout**: Side-by-side comparison

**File**: `website/src/components/ProblemSolution.astro`

**Tasks**:
- [ ] Create visual comparison
- [ ] Show "without memory" pain points
- [ ] Show "with memory" benefits
- [ ] Use terminal window styling

### 2.5 Features Section

**Features**:
1. **Persistent Memory** - Survives across sessions
2. **Relationship Tracking** - SOLVES, CAUSES, DEPENDS_ON
3. **Zero Config** - SQLite by default, works offline
4. **Project Aware** - Organize by project context
5. **Temporal Tracking** - Know what changed and when
6. **Semantic Navigation** - No embeddings needed

**File**: `website/src/components/Features.astro`

**Tasks**:
- [ ] Create feature cards with icons
- [ ] Use terminal window chrome for each feature
- [ ] Add hover effects (glow on hover)
- [ ] Link to documentation for details

### 2.6 Comparison Section

**File**: `website/src/components/Comparison.astro`

**Accordion-style**:
```
> How does this compare to CLAUDE.md?
  CLAUDE.md is static. MemoryGraph is dynamic and searchable.

> How does this compare to basic-memory?
  basic-memory is general PKM. MemoryGraph is purpose-built for coding.

> What about Cipher?
  Cipher uses Elastic License (restrictive). We're Apache 2.0 (true open source).
```

**Tasks**:
- [ ] Create accordion component
- [ ] Add comparisons (CLAUDE.md, basic-memory, Cipher, Anthropic)
- [ ] Link to full comparison page
- [ ] Keep tone respectful but clear on differences

### 2.7 Social Proof

**Placeholder content**:
- GitHub stars count (live)
- PyPI downloads (live)
- Testimonial placeholders (fill in post-launch)

**File**: `website/src/components/SocialProof.astro`

**Tasks**:
- [ ] Fetch GitHub stars dynamically
- [ ] Fetch PyPI downloads
- [ ] Create testimonial card template
- [ ] Add space for user testimonials

### 2.8 Final CTA

**Layout**:
```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│   READY TO GIVE YOUR AI A MEMORY?                        │
│                                                          │
│   $ pip install memorygraphMCP                           │
│                                                          │
│   [COPY COMMAND]  [READ THE DOCS]  [JOIN DISCORD]        │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**File**: `website/src/components/FinalCTA.astro`

**Tasks**:
- [ ] Create prominent CTA section
- [ ] Add copy-to-clipboard button
- [ ] Link to docs and Discord
- [ ] Add terminal styling

### 2.9 Footer

**Content**:
- Links: GitHub, Discord, Twitter, Docs
- Copyright and license info
- "Made with ♥ for Claude Code users"

**File**: `website/src/components/Footer.astro`

**Tasks**:
- [ ] Create footer with links
- [ ] Add copyright notice
- [ ] Add Apache 2.0 license badge
- [ ] Keep it minimal and clean

---

## Section 3: Additional Pages

### 3.1 Pricing Page

**File**: `website/src/pages/pricing.astro`

**Tiers**:

| Free | Pro ($8/month) | Team ($12/user) |
|------|----------------|-----------------|
| 1,000 API calls/day | 100,000 API calls/day | 1M API calls/day |
| 100 memories | 10,000 memories | Unlimited |
| SQLite local or Turso | Cloud PostgreSQL | Cloud + team features |
| Community support | Email support | Priority support |

**Tasks**:
- [ ] Create pricing comparison table
- [ ] Add "Sign Up" CTAs for each tier
- [ ] Add FAQ section (billing, upgrades, etc.)
- [ ] Link to Stripe checkout

### 3.2 Comparison Page (Detailed)

**File**: `website/src/pages/compare.astro`

**Sections**:
1. **vs Cipher (Byterover)**
   - License: Apache 2.0 vs Elastic 2.0
   - Relationships: 35+ typed vs generic edges
   - Language: Python vs Node.js
   - Ecosystem: MCP + SDK vs MCP only

2. **vs Graphiti (Zep)**
   - Focus: Coding-specific vs general-purpose
   - Dependencies: SQLite default vs Neo4j required
   - Complexity: Lightweight vs enterprise-grade

3. **vs CLAUDE.md**
   - Dynamic vs static
   - Searchable vs grep
   - Relationships vs flat text

**Tasks**:
- [ ] Create detailed comparison page
- [ ] Add feature matrix table
- [ ] Be honest about strengths/weaknesses
- [ ] Link from landing page

### 3.3 Documentation Hub

**File**: `website/src/pages/docs/index.astro`

**Content**:
- Link to GitHub docs
- Quick start guide (embedded)
- API reference link
- SDK documentation link
- Guides index

**Tasks**:
- [ ] Create docs landing page
- [ ] Embed or link to existing docs
- [ ] Add search functionality (Algolia DocSearch)
- [ ] Organize by getting started, guides, reference

### 3.4 Login Page

**File**: `website/src/pages/login.astro`

**Content**:
- Email/password login
- "Sign in with GitHub" button
- "Sign in with Google" button
- "Forgot password?" link
- "Don't have an account? Sign up"

**Tasks**:
- [ ] Create login form
- [ ] Integrate with Supabase Auth (from Workplan 15)
- [ ] Add OAuth buttons
- [ ] Style with terminal theme
- [ ] Add form validation

### 3.5 Signup Page

**File**: `website/src/pages/signup.astro`

**Content**:
- Email/password signup
- OAuth options
- Terms of Service and Privacy Policy checkboxes
- Redirect to dashboard after signup

**Tasks**:
- [ ] Create signup form
- [ ] Integrate with Supabase Auth
- [ ] Add password strength indicator
- [ ] Add terms acceptance checkbox
- [ ] Redirect to dashboard

---

## Section 4: Assets

### 4.1 Logo and Branding

**ASCII Logo** (for header):
```
                                                           _
 _ __ ___   ___ _ __ ___   ___  _ __ _   _  __ _ _ __ __ _ _ __ | |__
| '_ ` _ \ / _ \ '_ ` _ \ / _ \| '__| | | |/ _` | '__/ _` | '_ \| '_ \
| | | | | |  __/ | | | | | (_) | |  | |_| | (_| | | | (_| | |_) | | | |
|_| |_| |_|\___|_| |_| |_|\___/|_|   \__, |\__, |_|  \__,_| .__/|_| |_|
                                     |___/ |___/          |_|
```

**Tasks**:
- [ ] Create ASCII logo (or use text)
- [ ] Create favicon (16x16, 32x32 pixel art)
- [ ] Create Open Graph image (1200x630 for social sharing)
- [ ] Create logo variants (white, green, transparent)

### 4.2 Demo Assets

**Tasks**:
- [ ] Record asciinema terminal demo
- [ ] Convert to GIF or MP4
- [ ] Optimize for web (<5MB)
- [ ] Create fallback still image

### 4.3 Icons

**Needed**:
- Feature icons (6 icons for features section)
- Social icons (GitHub, Discord, Twitter)
- UI icons (copy, download, external link)

**Tasks**:
- [ ] Create or source pixel art icons
- [ ] Use heroicons or phosphor icons (modern fallback)
- [ ] Add icons to all sections
- [ ] Optimize SVGs

---

## Section 5: Performance Optimization

### 5.1 Build Optimization

**Tasks**:
- [ ] Enable Astro's static site generation
- [ ] Minify CSS and JS
- [ ] Optimize images (WebP format)
- [ ] Enable compression (gzip/brotli)
- [ ] Lazy load below-the-fold images
- [ ] Preload critical fonts

### 5.2 Lighthouse Targets

**Targets**:
- Performance: >90
- Accessibility: >90
- Best Practices: 100
- SEO: 100

**Tasks**:
- [ ] Run Lighthouse audit
- [ ] Fix any issues
- [ ] Optimize largest contentful paint (LCP)
- [ ] Reduce cumulative layout shift (CLS)
- [ ] Minimize first input delay (FID)

---

## Section 6: SEO and Analytics

### 6.1 SEO Optimization

**Meta Tags**:
```html
<title>MemoryGraph - Memory for AI Coding Agents</title>
<meta name="description" content="Never re-explain your project to Claude Code again. MemoryGraph gives your AI assistant persistent memory that remembers what worked.">
<meta property="og:title" content="MemoryGraph - Memory for AI Coding Agents">
<meta property="og:description" content="Persistent memory for AI coding assistants">
<meta property="og:image" content="/og-image.png">
<meta property="og:url" content="https://memorygraph.dev">
<meta name="twitter:card" content="summary_large_image">
```

**Tasks**:
- [ ] Add meta tags to all pages
- [ ] Create Open Graph image
- [ ] Add structured data (JSON-LD) for search engines
- [ ] Submit sitemap to Google Search Console
- [ ] Add robots.txt

### 6.2 Analytics

**Choice**: Plausible Analytics (privacy-friendly, GDPR-compliant)
**Alternative**: PostHog (free tier, more features)

**Tasks**:
- [ ] Set up Plausible account
- [ ] Add tracking script
- [ ] Set up goals (signups, installs, documentation views)
- [ ] Test event tracking
- [ ] Add privacy policy mentioning analytics

**Cost**: $0-9/month (Plausible free for low traffic, $9 for 10k visitors)

---

## Section 7: Deployment

### 7.1 Cloudflare Pages Configuration

**Tasks**:
- [ ] Connect GitHub repo to Cloudflare Pages
- [ ] Configure build settings:
  - Build command: `npm run build`
  - Publish directory: `dist/`
- [ ] Set environment variables (if needed)
- [ ] Configure custom domain: memorygraph.dev
- [ ] Enable automatic deployments on push to main

### 7.2 DNS Configuration

**Tasks**:
- [ ] Add CNAME record: memorygraph.dev → pages.dev
- [ ] Enable Cloudflare proxy (orange cloud)
- [ ] Verify SSL certificate active
- [ ] Test HTTPS redirect

### 7.3 Preview Deployments

**Tasks**:
- [ ] Enable preview deployments for PRs
- [ ] Test preview functionality
- [ ] Set up branch deployments (staging)

---

## Section 8: Testing

### 8.1 Cross-Browser Testing

**Browsers**:
- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Android)

**Tasks**:
- [ ] Test on all major browsers
- [ ] Test on mobile devices
- [ ] Check for layout issues
- [ ] Verify animations work
- [ ] Test form submissions

### 8.2 Accessibility Testing

**Tasks**:
- [ ] Run axe DevTools audit
- [ ] Check keyboard navigation
- [ ] Verify color contrast ratios
- [ ] Add ARIA labels where needed
- [ ] Test with screen reader

### 8.3 Performance Testing

**Tasks**:
- [ ] Run Lighthouse (desktop and mobile)
- [ ] Test with slow 3G connection
- [ ] Measure time to interactive
- [ ] Check bundle sizes
- [ ] Optimize critical path

---

## Section 9: Content Writing

### 9.1 Copy for Landing Page

**Sections to write**:
- [ ] Hero headline and subhead
- [ ] Feature descriptions (6 features)
- [ ] Comparison answers (4 competitors)
- [ ] CTA copy
- [ ] Footer tagline

**Tone**: Technical but approachable, confident but not arrogant

### 9.2 Legal Pages

**Pages needed**:
- Terms of Service
- Privacy Policy
- Cookie Policy (if using cookies)

**Tasks**:
- [ ] Write or adapt Terms of Service
- [ ] Write Privacy Policy (mention analytics, data storage)
- [ ] Add links to footer
- [ ] Consult legal if needed (or use templates)

---

## Section 10: Launch Preparation

### 10.1 Pre-Launch Checklist

**Content**:
- [ ] All pages complete
- [ ] All links working
- [ ] All images optimized
- [ ] All copy proofread
- [ ] Legal pages published

**Technical**:
- [ ] SSL certificate active
- [ ] DNS configured correctly
- [ ] Analytics tracking
- [ ] Forms tested
- [ ] APIs integrated

**Performance**:
- [ ] Lighthouse score >90
- [ ] Mobile responsive
- [ ] Fast load times (<2s)

### 10.2 Soft Launch

**Tasks**:
- [ ] Deploy to production
- [ ] Test live site end-to-end
- [ ] Share with small group (10-20 people)
- [ ] Collect feedback
- [ ] Fix critical issues

### 10.3 Public Launch

**Tasks**:
- [ ] Announce on Hacker News
- [ ] Post on Reddit (r/programming, r/ClaudeAI)
- [ ] Tweet launch announcement
- [ ] Post in Discord/Slack communities
- [ ] Update README with website link

---

## Acceptance Criteria Summary

### Design
- [ ] Retro terminal aesthetic implemented
- [ ] Scanlines and CRT effects working
- [ ] Terminal green color scheme applied
- [ ] Responsive on all devices

### Content
- [ ] All sections complete (hero, features, pricing, docs)
- [ ] Comparison page published
- [ ] Legal pages published
- [ ] Copy polished and proofread

### Performance
- [ ] Load time <2 seconds
- [ ] Lighthouse score >90
- [ ] Works on slow connections
- [ ] Optimized for mobile

### Technical
- [ ] Deployed on Cloudflare Pages
- [ ] SSL active
- [ ] Analytics tracking
- [ ] Forms working
- [ ] Auth integration working

---

## Notes for Coding Agent

**Design Guidelines**:

1. **Scanlines should be subtle**: Don't distract from content
2. **Accessibility first**: Effects should be optional, not required
3. **Performance over effects**: If effect slows page, remove it
4. **Test on real devices**: Emulators don't show real performance

**Framework Choice**:
- **Astro** (recommended): Fast, static, great DX
- Tailwind CSS for styling
- Minimal JavaScript (progressive enhancement)

**Content Strategy**:
- **Show, don't tell**: Use demos and examples
- **Be honest**: Acknowledge what competitors do well
- **Focus on benefits**: Not features, but what users gain

---

## Dependencies

**External**:
- Cloudflare Pages (hosting)
- Plausible or PostHog (analytics)
- Supabase Auth (login/signup)
- Google Fonts (typography)

**Internal**:
- Workplan 14 (cloud infrastructure)
- Workplan 15 (authentication)
- Existing documentation

---

## Estimated Timeline

| Section | Effort | Dependencies |
|---------|--------|--------------|
| Section 1: Design System | 2-3 hours | None |
| Section 2: Landing Page | 4-6 hours | Design done |
| Section 3: Additional Pages | 3-4 hours | Landing done |
| Section 4: Assets | 2-3 hours | Parallel with pages |
| Section 5: Performance | 2 hours | All pages done |
| Section 6: SEO/Analytics | 1-2 hours | All pages done |
| Section 7: Deployment | 1-2 hours | All done |
| Section 8: Testing | 2-3 hours | Deployed |
| Section 9: Content | 2-3 hours | Parallel with dev |
| Section 10: Launch | 1-2 hours | All tested |
| **Total** | **20-31 hours** | Sequential + parallel |

---

## References

- **7-WEBSITE-WORKPLAN.md**: Original design spec (DEPRECATED, content merged here)
- **Workplan 14**: Cloud infrastructure
- **Workplan 15**: Authentication
- **PRODUCT_ROADMAP.md**: Phase 3 (Cloud Launch)

---

**Last Updated**: 2025-12-05
**Status**: NOT STARTED
**Next Step**: Set up Astro project
**Deprecates**: 7-WEBSITE-WORKPLAN.md (content merged into this workplan)
