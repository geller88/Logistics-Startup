import Link from 'next/link';

const categories = [
  {
    title: 'Transport & Freight',
    description: 'Trucking, shipping lines, airlines/cargo, rail, and last-mile delivery execution.',
    accent: 'category-tra',
  },
  {
    title: 'Warehousing & Fulfillment',
    description: 'Warehouse robotics, fulfillment centers, storage, and inventory management.',
    accent: 'category-whf',
  },
  {
    title: 'Tracking & Visibility',
    description: 'Real-time shipment tracking, IoT sensors, and supply chain visibility platforms.',
    accent: 'category-trv',
  },
  {
    title: 'Labeling & Packaging',
    description: 'Shipping labels, packaging design/materials, and print-and-apply systems.',
    accent: 'category-lab',
  },
  {
    title: 'Digital Freight & Marketplaces',
    description: 'Online freight forwarding platforms and load-matching marketplaces.',
    accent: 'category-dfm',
  },
  {
    title: 'Supply Chain Software & Analytics',
    description: 'TMS/WMS/ERP software, planning tools, and supply chain data analytics.',
    accent: 'category-sca',
  },
  {
    title: 'Customs, Compliance & Trade',
    description: 'Customs brokerage, trade compliance, and cross-border documentation.',
    accent: 'category-cct',
  },
  {
    title: 'Sustainability & Green Logistics',
    description: 'Decarbonization, electric/alternative-fuel fleets, and green cold chain.',
    accent: 'category-sgl',
  },
];

export default function Home() {
  return (
    <main className="page-shell">
      <section className="hero-section">
        <div>
          <p className="eyebrow">Logistics Startup Market</p>
          <h1>Monitor logistics startups by category, not by accident.</h1>
          <p className="hero-copy">
            Browse logistics startup categories, discover new companies from pipeline discovery, and register for
            free access to full profile research.
          </p>
          <div className="button-row">
            <Link href="/companies" className="button button-primary">
              Startup monitor
            </Link>
            <Link href="/search" className="button button-secondary">
              Discovery search
            </Link>
          </div>
        </div>
        <div className="hero-panel">
          <div className="feature-card">
            <h2>Automatic startup tracking</h2>
            <p>New logistics startups are surfaced automatically by the discovery pipeline and presented in category cards.</p>
          </div>
          <div className="feature-card">
            <h2>Free registration gating</h2>
            <p>Register for a free account to unlock deeper company insights and market context.</p>
          </div>
          <div className="feature-card">
            <h2>Premium LLM research</h2>
            <p>Reserve premium logistics analysis for growth teams and investors looking for deeper trend intelligence.</p>
          </div>
        </div>
      </section>

      <section className="section-grid">
        <div className="section-header">
          <h2 className="section-title">Category cards</h2>
          <p className="section-text">Explore logistics startup themes and jump into the startup monitor for detailed company tracking.</p>
        </div>
        <div className="grid-4">
          {categories.map((category) => (
            <article key={category.title} className={`category-card ${category.accent}`}>
              <strong>{category.title}</strong>
              <p>{category.description}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="section-grid">
        <div className="section-header">
          <h2 className="section-title">How it works</h2>
          <p className="section-text">
            The app now focuses on discovery from real startup signals, simple search over company data, and registration-gated profile access.
          </p>
        </div>
        <div className="grid-3">
          <article className="card">
            <h3>Pipeline discovery</h3>
            <p>Fetch startups from web sources, enrich them with profile details, then surface the most relevant logistics companies.</p>
          </article>
          <article className="card">
            <h3>Free user registration</h3>
            <p>Register to unlock full descriptions and company details while keeping the initial discovery and search free.</p>
          </article>
          <article className="card">
            <h3>Premium research</h3>
            <p>Offer premium deep-dive research for logistics technology and market trends as a next step for power users.</p>
          </article>
        </div>
      </section>
    </main>
  );
}
