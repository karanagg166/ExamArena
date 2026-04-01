# Exam Arena — UI & Design System Reference

> This is the **source of truth** for all UI decisions. Every new page and component must follow these rules.

## Design Philosophy

- **Style**: Dark Glassmorphism (Selective)
- **Glass on**: Sidebar, navbar, modals, floating cards, hero sections
- **Glass off**: Exam attempt pages, data tables, forms, content-heavy areas
- **Dark-only** for now (CSS vars support light mode later)
- **Desktop-first**, responsive down to tablet
- **Audience**: Schools — principals, teachers, students (13-18+)

---

## Color Tokens (CSS Variables)

```
Background:     --background: #09090b
Surfaces:       --surface-1: #111114  |  --surface-2: #18181b  |  --surface-3: #27272a
Text:           --text-primary: #fafafa  |  --text-secondary: #a1a1aa  |  --text-muted: #71717a  |  --text-dimmed: #52525b
Accent:         --accent: #6366f1  |  --accent-hover: #818cf8  |  --accent-muted: rgba(99,102,241,0.15)
Success:        --success: #10b981  |  --success-muted: rgba(16,185,129,0.15)
Warning:        --warning: #f59e0b  |  --warning-muted: rgba(245,158,11,0.15)
Error:          --error: #f43f5e  |  --error-muted: rgba(244,63,94,0.15)
Info:           --info: #3b82f6  |  --info-muted: rgba(59,130,246,0.15)
Borders:        --border-subtle: rgba(255,255,255,0.06)  |  --border-default: rgba(255,255,255,0.1)
Glass:          --glass-bg: rgba(255,255,255,0.03)  |  --glass-border: rgba(255,255,255,0.08)
```

### Usage Rules
- ❌ Never use raw Tailwind colors (`bg-zinc-800`, `text-indigo-500`)
- ✅ Use CSS vars: `bg-[var(--surface-1)]`, `text-[var(--text-primary)]`, `border-[var(--border-subtle)]`
- ✅ Or use design system classes: `.glass-card`, `.panel`, `.page-title`

---

## Border Radius

| Element | Radius | CSS Var |
|---------|--------|---------|
| Cards, panels | 16px | `rounded-2xl` or `var(--radius-lg)` |
| Buttons | 12px | `rounded-xl` or `var(--radius-md)` |
| Inputs | 12px | `rounded-xl` |
| Badges | 9999px | `rounded-full` |
| Small elements | 8px | `rounded-lg` or `var(--radius-sm)` |

---

## Typography

| Class | Usage | Size |
|-------|-------|------|
| `.page-title` | Main page heading (h1) | 1.75rem → 2.25rem on md |
| `.section-title` | Section headings (h2/h3) | 1.25rem |
| `.page-subtitle` | Description below title | 0.875rem → 1rem on md |
| `.overline` | Small label above title | 0.6875rem, uppercase, tracking-wide |
| `.text-gradient` | Gradient text for hero sections | Accent gradient |

### Font
- **Primary**: Geist Sans (loaded via Next.js `--font-geist-sans`)
- **Mono**: Geist Mono (for code/IDs)

---

## Component Library (`src/components/ui/`)

### Core Components (from shadcn/Radix)
| Component | File | Usage |
|-----------|------|-------|
| `Button` | `button.tsx` | Variants: primary, secondary, ghost, danger, success, outline. Sizes: sm, md, lg. Has `active:scale-[0.98]` press effect. |
| `Card` | `card.tsx` | Surface card with `--surface-1` bg. Sub-components: CardHeader, CardTitle, CardDescription, CardContent, CardFooter. |
| `Input` | `input.tsx` | Text input with glass background, accent focus ring. Height: h-10. |
| `Textarea` | `textarea.tsx` | Multi-line input, same styling as Input. Min-height: 6rem. |
| `Badge` | `badge.tsx` | Pill badges. Variants: default (accent), success, warning, danger, neutral. |
| `Label` | `label.tsx` | Form label. |
| `Spinner` | `loading.tsx` | Spinning circle loader using accent color. |

### Custom Components
| Component | File | Usage |
|-----------|------|-------|
| `GlassCard` | `glass-card.tsx` | Frosted glass card. Props: `interactive` (hover lift), `padding` (none/sm/md/lg). Use for dashboard cards, floating panels. |
| `StatCard` | `stat-card.tsx` | Dashboard stat. Props: `label`, `value`, `icon`, `description`, `trend` (up/down/neutral). Icon changes color on hover. |
| `PageHeader` | `page-header.tsx` | Page title bar. Props: `title`, `subtitle`, `overline`, `actions` (ReactNode slot). |
| `EmptyState` | `empty-state.tsx` | Empty list state. Props: `icon`, `title`, `description`, `action`. Centered with fade-in. |
| `Skeleton` | `skeleton.tsx` | Shimmer loading. Base: `<Skeleton />`. Pre-built: `StatCardSkeleton`, `CardSkeleton`, `TableRowSkeleton`, `PageHeaderSkeleton`. |
| `Breadcrumb` | `breadcrumb.tsx` | Nav breadcrumbs. Props: `items` (array of {label, href?}), `showHome`. |

---

## Glass Effect Classes (from globals.css)

| Class | Use Case | Effect |
|-------|----------|--------|
| `.glass` | Base glass utility | blur(16px) + subtle bg + border |
| `.glass-card` | Cards with hover | blur + shadow + hover lift/glow |
| `.glass-nav` | Sidebar/topbar | blur(20px) + saturate, opaque-ish |
| `.glass-panel` | Side panels, filters | blur + surface-1 bg |
| `.glass-input` | Standalone inputs | Glass bg + focus ring |

### Performance Rules
- Max 3-4 glass elements per viewport
- Never use glass on scrolling content
- Only on fixed/sticky elements (sidebar, navbar, modals)
- Add `will-change: transform` (already in CSS classes)

---

## Animation Classes

| Class | Effect | Duration |
|-------|--------|----------|
| `.animate-fade-in` | Opacity 0→1 | 0.3s |
| `.animate-fade-in-up` | Fade + slide up 12px | 0.4s |
| `.animate-fade-in-down` | Fade + slide down 12px | 0.4s |
| `.animate-scale-in` | Fade + scale 0.95→1 | 0.3s |
| `.animate-slide-in-right` | Fade + slide right 20px | 0.4s |
| `.stagger-1` to `.stagger-6` | Animation delay increments | 0.05s each |
| `.skeleton` | Shimmer gradient loop | 1.5s infinite |
| `.animated-gradient` | Background gradient shift | 6s infinite |
| `.glow` | Pulsing accent glow | 2s infinite |

### For list animations
```tsx
{items.map((item, i) => (
  <Card key={item.id} className={`animate-fade-in-up stagger-${Math.min(i + 1, 6)}`}>
    ...
  </Card>
))}
```

---

## Navigation Architecture

### AppSidebar (`src/components/navbars/AppSidebar.tsx`)

**Desktop**: Collapsible glass sidebar (fixed left, 240px → 68px collapsed)
**Mobile**: Bottom tab bar (first 5 nav items)

#### Integration
```tsx
// Already done in (protected)/layout.tsx — wraps ALL authenticated pages
import { SidebarLayout } from "@/components/navbars/AppSidebar";
<SidebarLayout>{children}</SidebarLayout>
```

#### Role-Based Nav Items
| Role | Items |
|------|-------|
| Principal | Dashboard, My School, Classes, Profile |
| Teacher | Dashboard, My Classes, Create Exam, Exams, Profile |
| Student | Dashboard, My School, My Class, Take Exam, Results, Profile |
| Admin | Dashboard, Schools, Users, Profile |

#### Adding New Nav Items
Edit `navItemsByRole` in `AppSidebar.tsx`:
```tsx
{ label: "New Page", href: "/role/new-page", icon: SomeIcon, matchPrefix: "/role/new-page" }
```

#### Role Badge Colors
- **Principal**: Violet
- **Teacher**: Emerald
- **Student**: Sky
- **Admin**: Amber

---

## Layout Patterns

### Page Shell
```tsx
<div className="page-shell">  {/* max-w-6xl, px-4/6, py-6/10 */}
  <PageHeader title="Schools" subtitle="Manage all schools" actions={<Button>Add</Button>} />
  <div className="mt-6">
    {/* Page content */}
  </div>
</div>
```

### Card Grid
```tsx
<div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
  {items.map(item => <GlassCard key={item.id} interactive>...</GlassCard>)}
</div>
```

### Empty State
```tsx
<EmptyState
  icon={ClipboardList}
  title="No exams scheduled"
  description="Check back later or contact your teacher."
  action={<Button size="sm">Refresh</Button>}
/>
```

### Panel (opaque surface for content)
```tsx
<div className="panel panel-padding">
  {/* Forms, data tables, settings */}
</div>
```

---

## Page-Level Glass Budget

| Page Type | Glass Level | Which elements |
|-----------|-------------|----------------|
| Landing, Login, Signup | 🔥 High | Hero card, form card, feature cards |
| Dashboard | 🔥 High | Stat cards, nav sidebar |
| School/Class lists | ⚡ Medium | Cards only (no sidebar glass on scroll) |
| Profile, Settings | ✅ Low | Panel only |
| Exam Attempt | 🚫 None | Clean, opaque, distraction-free |

---

## Exam Attempt Page Rules (CRITICAL)

- 🚫 No sidebar, no navbar
- ⏱️ Timer fixed top-right, red when < 5min
- 📏 Progress bar fixed top
- 🔤 Max contrast: `text-zinc-50` on `bg-zinc-950`
- 📱 Option buttons min 48px height
- 🚫 No glass effects
- ⬅️➡️ Question nav pills at bottom

---

## Do / Don't Quick Reference

### ✅ DO
- Use `<PageHeader>` on every page
- Use `<EmptyState>` for all empty lists
- Use `<Skeleton>` presets for loading states
- Use CSS var tokens for all colors
- Add `animate-fade-in-up` with stagger to card lists
- Use `<GlassCard interactive>` for clickable items
- Use `<Button variant="primary">` for main CTAs

### ❌ DON'T
- Use raw `bg-zinc-*` or `text-indigo-*` colors
- Put glass effects on exam attempt page
- Use more than 4 glass elements per viewport
- Skip empty states (show a spinner forever)
- Create inline styles — use design system classes
- Use `<div>` when a semantic element exists (`<main>`, `<section>`, `<nav>`)
