const express = require('express');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 4000;

app.use(express.static(path.join(__dirname, 'public')));
app.get('/api/health', (req, res) => res.json({ status: 'ok', name: 'Logistics Startup Market' }));

app.listen(PORT, () => {
  console.log(`Logistics Startup Market is running at http://localhost:${PORT}`);
});
