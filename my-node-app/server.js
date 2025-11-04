const express = require('express');
const mysql = require('mysql');
const bodyParser = require('body-parser');
const cors = require('cors');
const path = require('path');

const app = express();
app.use(cors());
app.use(bodyParser.json());
app.use('/uploads', express.static(path.join(__dirname, 'uploads')));
app.use(express.static(path.join(__dirname, 'public')));

const db = mysql.createPool({
  connectionLimit: process.env.DB_CONNECTION_LIMIT,
  host: process.env.DB_HOST,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME
});

function startServer() {
  const PORT = process.env.PORT || 5000;
  app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
}

db.getConnection((err, connection) => {
  if (err) {
    console.error("MySQL Connection Failed:", err.message);
    process.exit(1);
  }
  console.log("MySQL Connected Successfully");
  connection.release();
  initializeDatabase();
  startServer();
});

function initializeDatabase() {
  const queries = [
    `CREATE TABLE IF NOT EXISTS bikesforsale (
      id INT AUTO_INCREMENT PRIMARY KEY,
      listingTitle VARCHAR(255),
      vehicleNumber VARCHAR(255),
      sellerName VARCHAR(255),
      mobileNum VARCHAR(20),
      bikeCondition VARCHAR(50),
      bikeType VARCHAR(50),
      makedFrom VARCHAR(50),
      bikeModel VARCHAR(100),
      bikeKms VARCHAR(50),
      bikePrice VARCHAR(50),
      sellingPrice VARCHAR(50),
      bikeOwner VARCHAR(50),
      bikeBuyingYear VARCHAR(10),
      bikeColor VARCHAR(50),
      bikeEngineCC VARCHAR(50),
      driveType VARCHAR(50),
      insurance VARCHAR(50),
      horsepower VARCHAR(50),
      bikeLocation VARCHAR(255),
      description TEXT,
      isAccepted BOOLEAN DEFAULT FALSE,
      isSoldout BOOLEAN DEFAULT FALSE
    )`,
    `CREATE TABLE IF NOT EXISTS enquiries (
      id INT AUTO_INCREMENT PRIMARY KEY,
      listingId INT,
      listingTitle VARCHAR(255),
      customerName VARCHAR(255),
      mobile VARCHAR(20),
      email VARCHAR(255),
      location VARCHAR(255),
      timestamp VARCHAR(50),
      status VARCHAR(50) DEFAULT 'Not updated',
      message TEXT
    )`,
    `CREATE TABLE IF NOT EXISTS soldOutBike (
      id INT AUTO_INCREMENT PRIMARY KEY,
      originalBikeId INT,
      listingTitle VARCHAR(255),
      vehicleNumber VARCHAR(255),
      sellerName VARCHAR(255),
      mobileNum VARCHAR(20),
      bikeCondition VARCHAR(50),
      bikeType VARCHAR(50),
      makedFrom VARCHAR(50),
      bikeModel VARCHAR(100),
      bikeKms VARCHAR(50),
      bikePrice VARCHAR(50),
      sellingPrice VARCHAR(50),
      bikeOwner VARCHAR(50),
      bikeBuyingYear VARCHAR(10),
      bikeColor VARCHAR(50),
      bikeEngineCC VARCHAR(50),
      driveType VARCHAR(50),
      insurance VARCHAR(50),
      horsepower VARCHAR(50),
      bikeLocation VARCHAR(255),
      description TEXT,
      soldOutDate DATETIME DEFAULT NOW(),
      image VARCHAR(255)
    )`,
    `CREATE TABLE IF NOT EXISTS signUpList (
      id INT AUTO_INCREMENT PRIMARY KEY,
      firstName VARCHAR(50),
      lastName VARCHAR(50),
      mobileNumber VARCHAR(10) NOT NULL UNIQUE,
      email VARCHAR(100),
      signUpPassword VARCHAR(255)
    )`
  ];
  queries.forEach(sql => db.query(sql, err => { if (err) console.error(err); }));
}

app.post('/addBike', (req, res) => {
  const data = req.body;
  const bikeData = { ...data, isAccepted: data.isAccepted ? 1 : 0, isSoldout: data.isSoldout ? 1 : 0 };
  db.query('INSERT INTO bikesforsale SET ?', bikeData, (err, result) => {
    if (err) return res.status(500).json({ error: 'Database insert failed' });
    res.json({ message: 'Bike added successfully', id: result.insertId });
  });
});

app.get('/bikes', (req, res) => {
  db.query('SELECT * FROM bikesforsale', (err, result) => {
    if (err) return res.status(500).send(err);
    res.json(result);
  });
});

app.get('/bikes/:id', (req, res) => {
  db.query('SELECT * FROM bikesforsale WHERE id = ?', [req.params.id], (err, results) => {
    if (err) return res.status(500).json({ error: 'Database error' });
    res.json(results[0] || null);
  });
});

app.put('/bikes/:id/accept', (req, res) => {
  db.query('UPDATE bikesforsale SET isAccepted = 1 WHERE id = ?', [req.params.id], err => {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ success: true });
  });
});

app.put('/bikes/:id/reject', (req, res) => {
  db.query('UPDATE bikesforsale SET isAccepted = 0 WHERE id = ?', [req.params.id], err => {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ success: true });
  });
});

app.put('/bikes/:id/price', (req, res) => {
  const { newPrice } = req.body;
  if (!newPrice || newPrice <= 0) return res.status(400).json({ error: 'Invalid price' });
  db.query('UPDATE bikesforsale SET sellingPrice = ? WHERE id = ?', [newPrice, req.params.id], err => {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ success: true });
  });
});

app.post('/submitEnquiry', (req, res) => {
  db.query('INSERT INTO enquiries SET ?', req.body, (err, result) => {
    if (err) return res.status(500).json({ error: 'Database insert failed' });
    res.json({ message: 'Enquiry submitted successfully', id: result.insertId });
  });
});

app.get('/enquiries', (req, res) => {
  db.query('SELECT * FROM enquiries', (err, results) => {
    if (err) return res.status(500).json({ error: 'Failed to fetch enquiries' });
    res.json(results);
  });
});

app.put('/enquiries/:id/status', (req, res) => {
  db.query('UPDATE enquiries SET status = ? WHERE id = ?', [req.body.status, req.params.id], err => {
    if (err) return res.status(500).json({ error: 'Failed to update status' });
    res.json({ message: 'Status updated successfully' });
  });
});

app.put('/enquiries/:id/message', (req, res) => {
  db.query('UPDATE enquiries SET message = ? WHERE id = ?', [req.body.message, req.params.id], err => {
    if (err) return res.status(500).json({ error: 'Failed to update message' });
    res.json({ message: 'Message updated successfully' });
  });
});

app.put('/bikes/:id/soldout', (req, res) => {
  const bikeId = req.params.id;
  const query = `
    INSERT INTO soldOutBike (
      originalBikeId, listingTitle, vehicleNumber, sellerName, mobileNum, bikeCondition,
      bikeType, makedFrom, bikeModel, bikeKms, bikePrice, sellingPrice, bikeOwner,
      bikeBuyingYear, bikeColor, bikeEngineCC, driveType, insurance, horsepower,
      bikeLocation, description
    )
    SELECT 
      id, listingTitle, vehicleNumber, sellerName, mobileNum, bikeCondition,
      bikeType, makedFrom, bikeModel, bikeKms, bikePrice, sellingPrice, bikeOwner,
      bikeBuyingYear, bikeColor, bikeEngineCC, driveType, insurance, horsepower,
      bikeLocation, description
    FROM bikesforsale WHERE id = ?
  `;
  db.query(query, [bikeId], err => {
    if (err) return res.status(500).json({ message: 'Failed to copy bike' });
    db.query('DELETE FROM bikesforsale WHERE id = ?', [bikeId], err2 => {
      if (err2) return res.status(500).json({ message: 'Delete failed' });
      res.json({ message: 'Bike moved to Sold Out list successfully' });
    });
  });
});

app.get('/soldout', (req, res) => {
  db.query('SELECT * FROM soldOutBike', (err, results) => {
    if (err) return res.status(500).json(err);
    res.json(results);
  });
});

app.post('/addUser', (req, res) => {
  const { firstName, lastName, mobileNumber, email, signUpPassword } = req.body;
  const sql = 'INSERT INTO signUpList (firstName, lastName, mobileNumber, email, signUpPassword) VALUES (?, ?, ?, ?, ?)';
  db.query(sql, [firstName, lastName, mobileNumber, email, signUpPassword], err => {
    if (err) return res.status(500).send(err);
    res.send({ message: 'User registered successfully' });
  });
});

app.post('/login', (req, res) => {
  const { mobileNumber, signUpPassword } = req.body;
  const sql = 'SELECT * FROM signUpList WHERE mobileNumber = ? AND signUpPassword = ?';
  db.query(sql, [mobileNumber, signUpPassword], (err, results) => {
    if (err) return res.status(500).json({ success: false, message: 'Login failed', error: err });
    if (results.length > 0) {
      const user = results[0];
      res.json({ success: true, message: 'Login successful', firstName: user.firstName, lastName: user.lastName, email: user.email });
    } else {
      res.json({ success: false, message: 'Invalid credentials' });
    }
  });
});

app.get('/checkMobile/:mobile', (req, res) => {
  db.query('SELECT * FROM signUpList WHERE mobileNumber = ?', [req.params.mobile], (err, result) => {
    if (err) return res.json({ exists: false });
    res.json({ exists: result.length > 0 });
  });
});

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});
