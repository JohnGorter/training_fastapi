# Serverside Rendering


---
### Server side rendering

Single Page Applications (SPAs) ship a minimal HTML container and rely on client-side JavaScript to fetch data and construct the UI 

Server-Side Rendering (SSR) compiles fully populated HTML on the server, streaming ready-to-display content directly to the browser

---
### Perceived Performance & Core Web Vitals

Client-side rendering forces users through a multi-step waterfall
- downloading HTML
- fetching JS bundle
- parsing JS
- making secondary API requests


---
### Perceived Performance & Core Web Vitals (2)

SSR bypasses this chain to optimize load perception:
- First Contentful Paint (FCP) & Largest Contentful Paint (LCP)
    - SSR delivers pre-rendered markup in the initial HTTP payload
    - eliminates the blank white screen typical of cold-starting SPAs
- Time to Interactive (TTI) & Hydration
    - users see content quickly, but complex interactions must wait until hydration finishes

---
### SEO & Social Media Crawling

Search engines and social media platforms rely on automated scrapers to parse page content and metadata
- Crawler Reliability 
    - search engine bots process raw HTML first
    - SSR guarantees 100% content availability on the initial request.

- Link Previews (Open Graph)
    - Web scrapers for platforms like WhatsApp, LinkedIn, X, and Slack do not execute JavaScript
    - fails to render rich link preview cards

---
### Rendering Strategy Comparison

|Metric / Capability	| Single-Page Application (SPA)	|Server-Side Rendering (SSR)|
|---|---|
|Initial Load Speed|Slow (large JS bundle download)|Fast (pre-compiled HTML stream)|
|Subsequent Page Navigation|Instant (client-side route swaps)|Requires partial/full server roundtrips|
|Search Engine Indexing|Delayed or inconsistent|Immediate and 100% reliable|
|Social Media Card Support|Fails without pre-rendering hacks|Native out of the box|
|Server CPU Load|Minimal (serves static files)|Higher (compiles HTML per request)|
