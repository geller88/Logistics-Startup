Pipeline discovery sources:
- https://www.freightwaves.com/feed/
- https://www.supplychaindive.com/rss/all/
- https://theloadstar.com/feed/
- https://techcrunch.com/tag/logistics/feed/
- https://tech.eu/feed/
- https://www.eu-startups.com/tag/logistics/feed/
- https://www.sifted.eu/tag/supply-chain/feed/
- https://seedtable.com/best-logistics-startups

New pipeline behavior:
- seedtable startup URLs are scraped from the public Seedtable page and treated as discovery candidates
- raw discovery items are persisted into Supabase `sources` and `raw_items`
- startup website content is scraped to infer `has_product`, `product_status`, and `product_timeline`
