const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const paperRoutes = require('./routes/paperRoutes');
const userRoutes = require('./routes/userRoutes');

const app = express();

app.use(helmet());
app.use(cors());
app.use(express.json());

app.use('/api/papers', paperRoutes);
app.use('/api/users', userRoutes);

app.get('/', (req, res) => res.send('Academic Peer Review API is running.'));
app.get('/health', (req, res) => res.json({ status: 'ok', timestamp: new Date().toISOString() }));

module.exports = app;
