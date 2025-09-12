import express from 'express';
import { json, urlencoded } from 'body-parser';
import { connectToDb } from './database';
import routes from './routes';

const app = express();

app.use(json());
app.use(urlencoded({ extended: true }));

app.use('/', routes);

connectToDb().then(() => {
  app.listen(8000, () => {
    console.log('Server is running on port 8000');
  });
});