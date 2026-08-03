export const metadata = {
  title: 'Imprint — Logistics Startup Market',
};

export default function ImprintPage() {
  return (
    <main className="page-shell">
      <section className="page-header">
        <div>
          <p className="eyebrow">Imprint</p>
          <h1>Legal information</h1>
        </div>
      </section>

      <article className="card">
        <h2>LOG-PMO e.U.</h2>
        <p>
          Obdorfweg 40
          <br />
          6700 Bludenz
          <br />
          Email: <a href="mailto:office@log-pmo.com">office@log-pmo.com</a>
        </p>

        <h3>Register entry</h3>
        <p>
          Entry in the Handelsregister.
          <br />
          Registering court: Landesgericht Feldkirch
          <br />
          Registration number: FN 334848z
        </p>
      </article>
    </main>
  );
}
