import express, { Express } from 'express';
import credentialsRoute from './routes/credentialsRoute';
import authStartRoute from './routes/authStartRoute';
import verifyRoute from './routes/verifyRoute';
import sendRoute from './routes/sendRoute';
import getRoute from './routes/getRoute';

const app: Express = express();
const PORT = process.env.PORT || 8005;

app.use(express.json());

app.use('/auth/credentials', credentialsRoute);
app.use('/auth/start', authStartRoute);
app.use('/auth/verify', verifyRoute);
app.use('/send', sendRoute);
app.use('/get', getRoute);

app.listen(PORT, () => {
  console.log(`Telegram service running on port ${PORT}`);
});

