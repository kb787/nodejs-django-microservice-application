const { Pool } = require("pg");
const dotenv = require("dotenv");
dotenv.config();

const pool = new Pool({
  user: process.env.DB_USER,
  host: process.env.DB_HOST,
  database: process.env.DB_NAME,
  password: process.env.DB_PASSWORD,
  port: process.env.DB_PORT,
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

const connectDB = async () => {
  let client;
  try {
    client = await pool.connect();
    console.log(`Successfully connected to database`.bgBlue);
  } catch (err) {
    console.log(`Unable to connect to database due to error ${err}`);
  } finally {
    if (client) client.release();
  }
};

module.exports = { connectDB };
