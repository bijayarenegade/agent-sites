# Rebuild

Edit `config.js` (agent data), then from the site folder:

```
cp ~/.claude/skills/ai-website-agent-v2/template/{index,about,services,contact}.html .
python _build/bake.py .     # bakes config data into the HTML
python _build/seo.py .      # schema graph, meta, links, 404, robots, sitemap, vercel.json, og-image
python _build/audit.py      # pre-launch checks — should print "no issues"
```
