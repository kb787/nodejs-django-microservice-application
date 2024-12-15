const http = require("http");
const express = require("express");
const app = express();
const server = http.createServer(app);
app.use(express.json());
const dotenv = require("dotenv");
dotenv.config();
const server_port = process.env.server_port;
const { connectDB } = require("./config/dbConnection");

app.get("/", (req, res) => {
  return res.json({ message: "App running successfully" });
});
connectDB();
server.listen(server_port, () => {
  console.log(`Server running successfully on port no ${server_port}`);
});
