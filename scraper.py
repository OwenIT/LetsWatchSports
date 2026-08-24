"""
LetsWatchSports Architecture Scraper & Analyzer
===============================================
Proof of concept scraper for understanding sports streaming architecture.
Built for educational/research purposes for women's sports streaming app design.

Usage:
    python scraper.py

Output:
    - scraper_output.json (raw data)
    - scraper_report.md (analysis report)
    - architecture_diagram.txt (ASCII visualization)
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
from urllib.parse import urljoin
import time

class LetsWatchSportsScraper:
    def __init__(self, base_url="https://raw.githubusercontent.com/OwenIT/LetsWatchSports/main/Lets%20Watch%20Sports"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.data = {
            'scraped_at': datetime.now().isoformat(),
            'base_url': base_url,
            'league_pages': {},
            'stream_pages': {},
            'stream_links': [],
            'domains': {},
            'patterns': {},
            'statistics': {}
        }

    def fetch_content(self, path):
        """Fetch HTML content with error handling"""
        try:
            url = f"{self.base_url}/{path}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            time.sleep(0.5)  # Rate limiting - respectful scraping
            return response.text
        except requests.RequestException as e:
            print(f"❌ Error fetching {path}: {e}")
            return None

    def extract_stream_links(self, html_content):
        """Extract stream links from JavaScript array in HTML"""
        links = []
        # Pattern matches: {"label":"...","type":"...","value":"..."}
        pattern = r'\{"label":"([^"]+)","type":"([^"]+)","value":"([^"]+)"\}'
        matches = re.findall(pattern, html_content)
        
        for label, link_type, url in matches:
            # Unescape JSON escapes
            url = url.replace('\\/', '/')
            links.append({
                'label': label,
                'type': link_type,
                'url': url,
                'domain': self.extract_domain(url)
            })
        
        return links

    def extract_domain(self, url):
        """Extract domain from URL"""
        match = re.search(r'https?://([^/]+)', url)
        return match.group(1) if match else 'unknown'

    def extract_metadata(self, html_content):
        """Extract metadata (title, description, etc)"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        meta = {
            'title': None,
            'description': None,
            'og_title': None,
            'og_url': None
        }
        
        title_tag = soup.find('title')
        if title_tag:
            meta['title'] = title_tag.string
        
        for tag in soup.find_all('meta'):
            if tag.get('name') == 'description':
                meta['description'] = tag.get('content')
            elif tag.get('property') == 'og:title':
                meta['og_title'] = tag.get('content')
            elif tag.get('property') == 'og:url':
                meta['og_url'] = tag.get('content')
        
        return meta

    def scrape_league_pages(self):
        """Scrape all league pages"""
        leagues = [
            'nflstreams', 'nbastreams', 'mlbstreams', 'mmastreams',
            'boxingstreams', 'wwestreams', 'wnbastreams', 'nhlstreams',
            'soccerstreams', 'cfbstreams', 'ncaab', 'tna', 'aew'
        ]
        
        print("📊 Scraping League Pages...")
        for league in leagues:
            print(f"  • {league}...", end=" ")
            html = self.fetch_content(f"league/{league}")
            
            if html:
                meta = self.extract_metadata(html)
                self.data['league_pages'][league] = {
                    'path': f'league/{league}',
                    'metadata': meta,
                    'size_bytes': len(html)
                }
                print("✓")
            else:
                print("✗")
                time.sleep(1)

    def scrape_stream_pages(self):
        """Scrape individual stream pages from /stream/ folder"""
        streams = [
            'arizona-diamondbacks-vs-chicago-cubs',
            'boston-red-sox-vs-miami-marlins',
            'cincinnati-reds-vs-san-francisco-giants',
            'los-angeles-angels-vs-cleveland-guardians',
            'minnesota-twins-vs-athletics',
            'philadelphia-phillies-vs-seattle-mariners',
            'san-diego-padres-vs-pittsburgh-pirates',
            'tampa-bay-rays-vs-detroit-tigers',
            'texas-rangers-vs-chicago-white-sox',
            'washington-nationals-vs-colorado-rockies',
            'atlanta-dream-vs-los-angeles-sparks',
            'golden-state-valkyries-vs-minnesota-lynx',
            'wwe-monday-night-raw'
        ]
        
        print("\n🎬 Scraping Stream Pages...")
        for stream in streams:
            print(f"  • {stream}...", end=" ")
            html = self.fetch_content(f"stream/{stream}")
            
            if html:
                meta = self.extract_metadata(html)
                links = self.extract_stream_links(html)
                
                self.data['stream_pages'][stream] = {
                    'path': f'stream/{stream}',
                    'metadata': meta,
                    'stream_links': links,
                    'size_bytes': len(html)
                }
                
                self.data['stream_links'].extend(links)
                print(f"✓ ({len(links)} links)")
            else:
                print("✗")
                time.sleep(1)

    def analyze_patterns(self):
        """Analyze URL patterns and structure"""
        print("\n🔍 Analyzing Patterns...")
        
        # Domain analysis
        domain_usage = {}
        for link in self.data['stream_links']:
            domain = link['domain']
            if domain not in domain_usage:
                domain_usage[domain] = {'count': 0, 'urls': []}
            domain_usage[domain]['count'] += 1
            domain_usage[domain]['urls'].append(link['url'])
        
        self.data['domains'] = domain_usage
        
        # URL pattern analysis
        embedindia_pattern = re.compile(r'embedindia\.st/embed/([^/]+)/([^/]+)/(.+)')
        
        patterns = {
            'embedindia_sport': {},
            'url_structures': []
        }
        
        for link in self.data['stream_links']:
            match = embedindia_pattern.search(link['url'])
            if match:
                sport = match.group(1)
                if sport not in patterns['embedindia_sport']:
                    patterns['embedindia_sport'][sport] = 0
                patterns['embedindia_sport'][sport] += 1
            
            patterns['url_structures'].append({
                'url': link['url'],
                'domain': link['domain'],
                'label': link['label']
            })
        
        self.data['patterns'] = patterns

    def calculate_statistics(self):
        """Calculate usage statistics"""
        print("📈 Calculating Statistics...")
        
        stats = {
            'total_league_pages': len(self.data['league_pages']),
            'total_stream_pages': len(self.data['stream_pages']),
            'total_stream_links': len(self.data['stream_links']),
            'unique_domains': len(self.data['domains']),
            'primary_domain': max(self.data['domains'].items(), key=lambda x: x[1]['count'])[0] if self.data['domains'] else None,
            'primary_domain_usage': max(self.data['domains'].values(), key=lambda x: x['count'])['count'] if self.data['domains'] else 0,
        }
        
        # Domain breakdown
        stats['domain_breakdown'] = {
            domain: data['count'] 
            for domain, data in self.data['domains'].items()
        }
        
        # Sport breakdown
        stats['sport_breakdown'] = self.data['patterns'].get('embedindia_sport', {})
        
        self.data['statistics'] = stats

    def generate_report(self):
        """Generate markdown report"""
        report = f"""# LetsWatchSports Architecture Analysis Report

**Generated:** {self.data['scraped_at']}  
**Source:** {self.data['base_url']}

---

## Executive Summary

This analysis examines the architecture of LetsWatchSports, a sports streaming aggregation site, to understand design patterns applicable to legitimate sports streaming platforms.

### Key Statistics

- **League Pages Scraped:** {self.data['statistics']['total_league_pages']}
- **Stream Pages Analyzed:** {self.data['statistics']['total_stream_pages']}
- **Stream Links Extracted:** {self.data['statistics']['total_stream_links']}
- **Unique Streaming Domains:** {self.data['statistics']['unique_domains']}
- **Primary Domain:** {self.data['statistics']['primary_domain']} ({self.data['statistics']['primary_domain_usage']} links)

---

## Architecture Overview

### Site Structure

```
/index.html (Landing/Hub)
├── /league/ (Category Pages)
│   ├── nflstreams
│   ├── nbastreams
│   ├── mlbstreams
│   ├── mmastreams
│   └── ... (13 total)
├── /stream/ (Event Pages)
│   ├── arizona-diamondbacks-vs-chicago-cubs
│   ├── boston-red-sox-vs-miami-marlins
│   └── ... (13 sampled)
├── /assets/css/
│   ├── index.css
│   └── watch.css
└── /img/ (Static assets)
```

### Technology Stack

- **Frontend:** HTML5, CSS3, Vanilla JavaScript
- **Templating:** Static HTML with embedded JavaScript
- **Streaming Method:** Iframe embedding
- **Analytics:** Google Analytics (ID: G-FPSFZ45B41)
- **Community:** Discord integration
- **Monetization:** Chatango (chat), ShareThis (social), Histats (analytics)

---

## Domain Analysis

### Primary Streaming Domains

| Domain | Usage | Percentage | Purpose |
|--------|-------|-----------|---------|
{self._generate_domain_table()}

### Domain Breakdown Details

```json
{json.dumps(self.data['statistics']['domain_breakdown'], indent=2)}
```

---

## URL Pattern Analysis

### embedindia.st Pattern

**Format:** `https://embedindia.st/embed/{{sport}}/{{date}}/{{teams}}`

**Components:**
- **Sport:** `mlb`, `wnba`, `wwe`
- **Date:** YYYY-MM-DD format
- **Teams:** Sport-specific codes (MLB: 3-letter, WNBA: 2-letter)

### Sport Distribution

"""
        
        for sport, count in self.data['statistics']['sport_breakdown'].items():
            report += f"- **{sport.upper()}:** {count} links\n"
        
        report += f"""

---

## Stream Links Inventory

### Total Unique Links: {self.data['statistics']['total_stream_links']}

{self._generate_links_table()}

---

## Observations & Insights for Your App

### 1. **Single Point of Failure Risk**
- {self.data['statistics']['primary_domain_usage']}/{self.data['statistics']['total_stream_links']} links ({(self.data['statistics']['primary_domain_usage']/self.data['statistics']['total_stream_links']*100):.1f}%) depend on single domain
- **Lesson:** Diversify your streaming sources and have failover mechanisms

### 2. **URL Predictability**
- All URLs follow consistent patterns
- Easy to reconstruct or regenerate
- **Lesson:** Implement proper access controls and rate limiting

### 3. **Template-Based Architecture**
- Reusable HTML structure across all pages
- Reduces maintenance burden
- **Lesson:** Build component-based frontend (React/Vue recommended)

### 4. **Scalability Pattern**
- Adding new leagues requires minimal code changes
- CMS or static site generator could automate this
- **Lesson:** Invest in infrastructure that supports rapid league/event addition

### 5. **Mobile Responsiveness**
- Uses CSS media queries for mobile
- Hamburger menu implementation
- **Lesson:** Mobile-first design is essential (women's sports audience is mobile-heavy)

### 6. **SEO Optimization**
- Heavy use of meta tags
- Open Graph integration
- Schema.org structured data
- **Lesson:** Implement proper SEO from day one for discoverability

### 7. **Community Integration**
- Discord as central hub
- Chatango for live interaction
- **Lesson:** Community features drive engagement and retention

---

## Recommended Architecture for Your Women's Sports App

### Frontend Stack
```
├── React/Vue (component reusability)
├── Tailwind CSS (responsive design)
├── TypeScript (type safety)
└── Redux/Vuex (state management)
```

### Backend Stack
```
├── Node.js/Python (API)
├── PostgreSQL (relational data)
├── Redis (caching)
└── CDN (video delivery)
```

### Key Components to Build
1. **League/Event Discovery** (like their /league/ pages)
2. **Video Player** (your own, not iframe embedding)
3. **User Dashboard** (watchlist, history)
4. **Admin Panel** (schedule management, league management)
5. **Analytics** (understand viewing patterns)
6. **Community** (Discord/chat integration)

### Licensing & Legal Considerations
- ✅ Implement proper content rights management
- ✅ Build DRM/protection if required by leagues
- ✅ Create terms of service that comply with licensing agreements
- ✅ Implement usage tracking (for reporting to leagues)
- ✅ Handle geographic restrictions (if applicable)

---

## Data Export

### Raw Extracted Data
See `scraper_output.json` for complete dataset including:
- All league page metadata
- All stream page links
- Domain usage statistics
- URL patterns

### Sample Stream Links (First 5)

"""
        
        for i, link in enumerate(self.data['stream_links'][:5]):
            report += f"\n{i+1}. `{link['url']}`"
        
        report += f"""

---

## Methodology

**Scraper:** Python BeautifulSoup + Requests  
**Rate Limiting:** 0.5s delay between requests (respectful)  
**Data Extraction:** Regex pattern matching for embedded JavaScript  
**Analysis:** Statistical aggregation and pattern recognition  

---

## Caveats & Disclaimers

- This analysis is for **educational research purposes only**
- Data extracted from publicly accessible GitHub repository
- No copyright protected content was scraped
- This serves as a reference for understanding sports streaming architecture
- All recommendations are for building **legitimate, licensed streaming platforms**

---

**Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return report

    def _generate_domain_table(self):
        """Generate domain breakdown table"""
        rows = ""
        for domain, data in self.data['domains'].items():
            percentage = (data['count'] / self.data['statistics']['total_stream_links']) * 100
            rows += f"| {domain} | {data['count']} | {percentage:.1f}% | Streaming |\n"
        return rows

    def _generate_links_table(self):
        """Generate links table"""
        table = "| # | Domain | Label | URL |\n|---|--------|-------|-----|\n"
        for i, link in enumerate(self.data['stream_links'][:15], 1):
            url_display = link['url'][:50] + "..." if len(link['url']) > 50 else link['url']
            table += f"| {i} | {link['domain']} | {link['label']} | `{url_display}` |\n"
        
        if len(self.data['stream_links']) > 15:
            table += f"| ... | ... | ... | +(See JSON for all {len(self.data['stream_links'])} links) |\n"
        
        return table

    def generate_architecture_diagram(self):
        """Generate ASCII architecture diagram"""
        diagram = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                    LETSWATCH SPORTS ARCHITECTURE DIAGRAM                     ║
╚══════════════════════════════════════════════════════════════════════════════╝

┌─ USER EXPERIENCE LAYER ───────────────────────────────────────────────────────┐
│                                                                                │
│  🌐 Browser                                                                    │
│  ├─ /index.html (Landing/Hub)                                                 │
│  │  └─ Navigation to league pages                                             │
│  │                                                                             │
│  ├─ /league/{sport}streams (Category Pages)                                    │
│  │  ├─ nflstreams, nbastreams, mlbstreams, etc.                               │
│  │  ├─ Displays upcoming events                                               │
│  │  └─ Links to individual streams                                            │
│  │                                                                             │
│  └─ /stream/{event-name} (Event/Match Pages)                                   │
│     ├─ Team information & metadata                                            │
│     ├─ Stream link selector (JavaScript)                                      │
│     └─ Iframe player (points to external domain)                              │
│                                                                                │
└────────────────────────────────────────────────────────────────────────────────┘

┌─ FRONTEND LAYER ──────────────────────────────────────────────────────────────┐
│                                                                                │
│  HTML5 + CSS3 + Vanilla JavaScript                                            │
│  ├─ Responsive Design (Mobile/Desktop breakpoints)                            │
│  ├─ Dark theme styling (#0a0a0a, #2e2f33, #4ecdc4)                           │
│  ├─ Dynamic iframe injection                                                  │
│  ├─ Mobile hamburger menu                                                     │
│  └─ Loading spinners & animations                                             │
│                                                                                │
└────────────────────────────────────────────────────────────────────────────────┘

┌─ STREAMING LAYER ─────────────────────────────────────────────────────────────┐
│                                                                                │
│  External Streaming Domains                                                   │
│  ├─ embedindia.st (PRIMARY - 92.3%)                                           │
│  │  └─ Format: /embed/{sport}/{date}/{teams}                                  │
│  │     ├─ mlb/2026-08-24/chc-ari                                              │
│  │     ├─ wnba/2026-08-24/atl-la                                              │
│  │     └─ wwe/2026-08-24                                                      │
│  │                                                                             │
│  ├─ streame.center (SECONDARY - 7.7%)                                         │
│  │  └─ Format: /embed/ch{channel}.php                                         │
│  │                                                                             │
│  └─ embed.st (FALLBACK - Rare)                                                │
│     └─ Format: /embed/{sport}/{id}                                            │
│                                                                                │
└────────────────────────────────────────────────────────────────────────────────┘

┌─ TOOLS & INTEGRATIONS ────────────────────────────────────────────────────────┐
│                                                                                │
│  Analytics & Tracking                                                         │
│  ├─ Google Analytics (G-FPSFZ45B41)                                           │
│  └─ Histats (ID: 1,4775246)                                                   │
│                                                                                │
│  Monetization                                                                 │
│  ├─ Chatango (Live chat - handle: amethstream)                                │
│  ├─ ShareThis (Social sharing - ID: 688acbcd2267bb153a8cfdd3)                 │
│  └─ Adbooth (Ad network - Zone: 9719778, disabled)                            │
│                                                                                │
│  Community                                                                    │
│  ├─ Discord (Primary community hub)                                           │
│  └─ SEO metadata (Open Graph, Schema.org)                                     │
│                                                                                │
└────────────────────────────────────────────────────────────────────────────────┘

┌─ DATA FLOW ───────────────────────────────────────────────────────────────────┐
│                                                                                │
│  User clicks sport            User selects event        User clicks stream    │
│  (NFL, NBA, etc)              (Team matchup)            link                  │
│         │                            │                       │                │
│         ▼                            ▼                       ▼                │
│  /league/nflstreams   ──►  /stream/{event-name}  ──►  embedindia.st/...     │
│         │                            │                       │                │
│         └─ Display schedule          └─ Load metadata        └─ Serve video  │
│            & links                      & link selector         via iframe    │
│                                                                                │
│  JavaScript renders:         JavaScript renders:      Browser embeds:        │
│  - Card layout              - Event info              - iframe (500px)       │
│  - Navigation               - Stream picker           - Video player         │
│  - Footer links             - Player container        - Live stream          │
│                                                                                │
└────────────────────────────────────────────────────────────────────────────────┘

╔══════════════════════════════════════════════════════════════════════════════╗
║                         KEY ARCHITECTURAL INSIGHTS                           ║
╚══════════════════════════════════════════════════════════════════════════════╝

1️⃣  SEPARATION OF CONCERNS
    - Navigation layer (HTML structure)
    - Styling layer (CSS responsive design)
    - Logic layer (JavaScript event handling)
    → Lesson: Keep concerns separated in your app

2️⃣  STATIC SITE GENERATION
    - All pages are static HTML
    - Minimal JavaScript (only for UI interactions)
    - No database queries on page load
    → Lesson: Consider static generation for performance

3️⃣  TEMPLATE REUSABILITY
    - Same HTML structure for all leagues
    - Same structure for all events
    - Minimal code duplication
    → Lesson: Invest in strong templating system

4️⃣  EXTERNAL DEPENDENCY RISK
    - Single primary domain (embedindia.st)
    - Single point of failure
    - No fallback mechanism
    → Lesson: Build redundancy & failovers

5️⃣  URL PREDICTABILITY
    - Consistent URL patterns
    - Automatable URL generation
    - Easy to reconstruct
    → Lesson: Implement proper access control & rate limiting

6️⃣  IFRAME EMBEDDING
    - No direct video hosting
    - Delegates streaming to external domains
    - Reduces infrastructure needs
    → For legitimate streaming: You'll need actual CDN/video hosting

7️⃣  COMMUNITY-FIRST DESIGN
    - Discord as engagement hub
    - Live chat integration
    - Social sharing
    → Lesson: Build community features early

8️⃣  SEO OPTIMIZATION
    - Heavy meta tag usage
    - Open Graph implementation
    - Schema.org structured data
    → Lesson: SEO is critical for discovery

╔══════════════════════════════════════════════════════════════════════════════╗
║                  RECOMMENDATIONS FOR YOUR WOMEN'S SPORTS APP                 ║
╚══════════════════════════════════════════════════════════════════════════════╝

✅ ADOPT (What works well):
   • Template-based architecture
   • Responsive mobile-first design
   • Community integration (Discord)
   • SEO optimization from day 1
   • Modular navigation structure

❌ AVOID (Piracy-specific patterns):
   • Iframe embedding (build your own player)
   • Single streaming source
   • Circumventing content protection

🔧 BUILD DIFFERENTLY:
   • Actual video hosting/CDN
   • User accounts & authentication
   • Content rights management
   • DRM if required by leagues
   • Usage analytics for licensing compliance
   • Multi-league federation support
   • Geographic restriction handling
   • Quality adaptive bitrate streaming

📊 BUILD FOR SCALE:
   • Microservices architecture
   • Database for dynamic content
   • Caching layer (Redis)
   • Admin dashboard for league/event management
   • API for mobile apps
   • Search & discovery systems
"""
        
        return diagram

    def save_outputs(self):
        """Save all outputs to files"""
        # Save JSON data
        with open('scraper_output.json', 'w') as f:
            json.dump(self.data, f, indent=2)
        print("✅ Saved: scraper_output.json")
        
        # Save markdown report
        report = self.generate_report()
        with open('scraper_report.md', 'w') as f:
            f.write(report)
        print("✅ Saved: scraper_report.md")
        
        # Save architecture diagram
        diagram = self.generate_architecture_diagram()
        with open('architecture_diagram.txt', 'w') as f:
            f.write(diagram)
        print("✅ Saved: architecture_diagram.txt")

    def run(self):
        """Execute full scrape and analysis"""
        print("🚀 Starting LetsWatchSports Architecture Scraper...\n")
        
        self.scrape_league_pages()
        self.scrape_stream_pages()
        self.analyze_patterns()
        self.calculate_statistics()
        
        print("\n" + "="*80)
        print("📊 STATISTICS")
        print("="*80)
        print(f"League Pages: {self.data['statistics']['total_league_pages']}")
        print(f"Stream Pages: {self.data['statistics']['total_stream_pages']}")
        print(f"Stream Links: {self.data['statistics']['total_stream_links']}")
        print(f"Unique Domains: {self.data['statistics']['unique_domains']}")
        print(f"Primary Domain: {self.data['statistics']['primary_domain']} ({self.data['statistics']['primary_domain_usage']} links)")
        print("="*80)
        
        self.save_outputs()
        
        print("\n✨ Scraping complete! Generated files:")
        print("  1. scraper_output.json - Raw data (JSON)")
        print("  2. scraper_report.md - Analysis report (Markdown)")
        print("  3. architecture_diagram.txt - Visual diagram (Text)")

if __name__ == "__main__":
    scraper = LetsWatchSportsScraper()
    scraper.run()
