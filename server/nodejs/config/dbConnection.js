const { Pool } = require("pg");
const dotenv = require("dotenv");
const colors = require("colors");
dotenv.config();

const pool = new Pool({
  user: process.env.database_user,
  host: process.env.database_host,
  database: process.env.database_name,
  password: process.env.database_password,
  port: process.env.database_port,
});

const connectDB = async () => {
  try {
    await pool.connect();
    console.log(`Successfully connected to database`.bgBlue);
  } catch (err) {
    console.log(`Unable to connect to database due to error ${err}`.bgRed);
  }
};

module.exports = { connectDB };
