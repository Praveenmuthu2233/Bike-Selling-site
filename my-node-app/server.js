require('dotenv').config();
const express = require('express');
const mysql = require('mysql');
const bodyParser = require('body-parser');
const path = require('path');
const fs = require('fs');
const bcrypt = require("bcryptjs");
const cors = require('cors');
const jwt = require("jsonwebtoken");
const multer = require("multer");

const app = express();
const JWT_SECRET = process.env.JWT_SECRET;

app.use(cors({
  origin: "*",
  methods: "GET,POST,PUT,DELETE",
  allowedHeaders: "Content-Type,Authorization"
}));

app.use(express.json());
app.use(bodyParser.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'public')));

const uploadDir = path.join('/tmp', 'uploads');
if (!fs.existsSync(uploadDir)) fs.mkdirSync(uploadDir, { recursive: true });
app.use('/uploads', express.static(uploadDir));

const storage = multer.diskStorage({
  destination: function (req, file, cb) {
    cb(null, uploadDir);
  },
  filename: function (req, file, cb) {
    cb(null, Date.now() + "-" + file.originalname);
  }
});
const upload = multer({ storage });

const db = mysql.createPool({
  connectionLimit: process.env.DB_CONNECTION_LIMIT || 10,
  host: process.env.DB_HOST,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME
});

db.getConnection((err) => {
  if (err) console.error("DB Error:", err);
  else console.log("DB Connected");
});

initializeDatabase();
startServer();

function startServer() {
  const PORT = process.env.PORT || 5000;
  app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
}

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
    )`,
    `CREATE TABLE IF NOT EXISTS gallery_uploads (
      id INT AUTO_INCREMENT PRIMARY KEY,
      fileName VARCHAR(255),
      filePath VARCHAR(255),
      uploadedAt DATETIME DEFAULT NOW()
    )`,
    `CREATE TABLE IF NOT EXISTS attachments_uploads (
      id INT AUTO_INCREMENT PRIMARY KEY,
      fileName VARCHAR(255),
      filePath VARCHAR(255),
      uploadedAt DATETIME DEFAULT NOW()
    )`
  ];

  queries.forEach(sql => db.query(sql, err => { }));
}

app.post('/addBike', (req, res) => {
  const data = req.body;
  const bikeData = { ...data, isAccepted: data.isAccepted ? 1 : 0, isSoldout: data.isSoldout ? 1 : 0 };

  db.query('INSERT INTO bikesforsale SET ?', bikeData, (err, result) => {
    if (err) return res.status(500).json({ error: err.sqlMessage });
    res.json({ message: 'Bike added successfully', id: result.insertId });
  });
});

app.post("/userAddBike", (req, res) => {
  const data = req.body;
  const bikeData = {
    listingTitle: data.listingTitle,
    vehicleNumber: data.vehicleNumber,
    sellerName: data.sellerName,
    mobileNum: data.mobileNum,
    bikeCondition: data.bikeCondition,
    bikeType: data.bikeType,
    makedFrom: data.makedFrom,
    bikeModel: data.bikeModel,
    bikeKms: data.bikeKms,
    bikePrice: data.bikePrice,
    sellingPrice: data.sellingPrice,
    bikeOwner: data.bikeOwner,
    bikeBuyingYear: data.bikeBuyingYear,
    bikeColor: data.bikeColor,
    bikeEngineCC: data.bikeEngineCC,
    driveType: data.driveType,
    insurance: data.insurance,
    horsepower: data.horsepower,
    bikeLocation: data.bikeLocation,
    description: data.description,
    isAccepted: data.isAccepted ? 1 : 0,
    isSoldout: data.isSoldout ? 1 : 0
  };

  db.query("INSERT INTO bikesforsale SET ?", bikeData, (err, result) => {
    if (err) return res.status(500).json({ success: false, message: err.sqlMessage });
    res.json({ success: true, message: "Bike Added Successfully", id: result.insertId });
  });
});

app.post('/upload/gallery', upload.array('attachments', 10), (req, res) => {
  if (!req.files || req.files.length === 0) return res.status(400).json({ message: 'No files uploaded' });
  const files = req.files.map(f => [f.filename, f.path]);

  db.query('INSERT INTO gallery_uploads (fileName, filePath) VALUES ?', [files], err => {
    if (err) return res.status(500).json({ message: 'Upload failed' });
    res.json({ message: 'Gallery uploaded successfully', files });
  });
});

app.post('/upload/attachments', upload.array('attachments', 10), (req, res) => {
  if (!req.files || req.files.length === 0) return res.status(400).json({ message: 'No files uploaded' });
  const files = req.files.map(f => [f.filename, f.path]);

  db.query('INSERT INTO attachments_uploads (fileName, filePath) VALUES ?', [files], err => {
    if (err) return res.status(500).json({ message: 'Upload failed' });
    res.json({ message: 'Attachments uploaded successfully', files });
  });
});

app.get('/gallery', (req, res) => {
  db.query('SELECT * FROM gallery_uploads ORDER BY uploadedAt DESC', (err, results) => {
    res.json(results);
  });
});

app.get('/attachments', (req, res) => {
  db.query('SELECT * FROM attachments_uploads ORDER BY uploadedAt DESC', (err, results) => {
    res.json(results);
  });
});

app.get('/bikes', (req, res) => {
  db.query('SELECT * FROM bikesforsale', (err, result) => {
    res.json(result);
  });
});

app.get('/bikes/:id', (req, res) => {
  db.query('SELECT * FROM bikesforsale WHERE id = ?', [req.params.id], (err, results) => {
    res.json(results[0] || null);
  });
});

app.delete('/deleteEnquiry/:id', (req, res) => {
  db.query('DELETE FROM enquiries WHERE id = ?', [req.params.id], (err, result) => {
    res.json({ message: "Enquiry deleted successfully" });
  });
});

app.put('/bikes/:id/accept', (req, res) => {
  db.query('UPDATE bikesforsale SET isAccepted = 1 WHERE id = ?', [req.params.id], err => {
    res.json({ success: true });
  });
});

app.put('/bikes/:id/reject', (req, res) => {
  db.query('UPDATE bikesforsale SET isAccepted = 0 WHERE id = ?', [req.params.id], err => {
    res.json({ success: true });
  });
});

app.put('/bikes/:id/price', (req, res) => {
  const { newPrice } = req.body;
  db.query('UPDATE bikesforsale SET sellingPrice = ? WHERE id = ?', [newPrice, req.params.id], err => {
    res.json({ success: true });
  });
});

app.post('/enquiries', (req, res) => {
  db.query('INSERT INTO enquiries SET ?', req.body, (err, result) => {
    res.json({ message: 'Enquiry submitted successfully', id: result.insertId });
  });
});

app.get('/enquiries', (req, res) => {
  db.query('SELECT * FROM enquiries', (err, results) => {
    res.json(results);
  });
});

app.put('/enquiries/:id/status', (req, res) => {
  db.query('UPDATE enquiries SET status = ? WHERE id = ?', [req.body.status, req.params.id], err => {
    res.json({ message: 'Status updated successfully' });
  });
});

app.put('/enquiries/:id/message', (req, res) => {
  db.query('UPDATE enquiries SET message = ? WHERE id = ?', [req.body.message, req.params.id], err => {
    res.json({ message: 'Message updated successfully' });
  });
});
app.get('/enquiries/:mobile', (req, res) => {
  const mobile = req.params.mobile;

  db.query(
    'SELECT * FROM enquiries WHERE mobile = ?', 
    [mobile], 
    (err, results) => {
      if (err) return res.status(500).json({ error: err });
      res.json(results);
    }
  );
});

app.put('/bikes/:id/soldout', (req, res) => {
  const bikeId = req.params.id;

  const query = `
    INSERT INTO soldOutBike (
      originalBikeId,
      listingTitle, vehicleNumber, sellerName, mobileNum, bikeCondition,
      bikeType, makedFrom, bikeModel, bikeKms, bikePrice, sellingPrice, bikeOwner,
      bikeBuyingYear, bikeColor, bikeEngineCC, driveType, insurance, horsepower,
      bikeLocation, description, soldOutDate, image
    )
    SELECT 
      id,
      listingTitle, vehicleNumber, sellerName, mobileNum, bikeCondition,
      bikeType, makedFrom, bikeModel, bikeKms, bikePrice, sellingPrice, bikeOwner,
      bikeBuyingYear, bikeColor, bikeEngineCC, driveType, insurance, horsepower,
      bikeLocation, description, NOW(), null
    FROM bikesforsale WHERE id = ?
  `;

  db.query(query, [bikeId], (err) => {
    db.query('DELETE FROM bikesforsale WHERE id = ?', [bikeId], (err2) => {
      res.json({ message: 'Bike moved to Sold Out list successfully' });
    });
  });
});

app.get('/soldout', (req, res) => {
  const adminName = req.query.adminName;
  db.query('SELECT * FROM soldOutBike', (err, results) => {
    let resultData = results;

    if (adminName.toLowerCase() === "mani") {
      resultData = resultData.map(bike => ({
        ...bike,
        bikePrice: undefined,
      }));
      return res.json(resultData);
    } else if (adminName === "murugan" || adminName === "raja") {
      return res.json(resultData);
    }

    res.status(403).json({ message: "Access denied" });
  });
});

app.post('/addUser', async (req, res) => {
  const { firstName, lastName, mobileNumber, email, signUpPassword } = req.body;
  const hashedPassword = await bcrypt.hash(signUpPassword, 10);

  db.query(
    'INSERT INTO signUpList (firstName, lastName, mobileNumber, email, signUpPassword) VALUES (?, ?, ?, ?, ?)',
    [firstName, lastName, mobileNumber, email, hashedPassword],
    err => {
      if (err) return res.status(500).send(err);
      res.send({ message: 'User registered successfully' });
    }
  );
});

app.post('/login', (req, res) => {
  const { mobileNumber, signUpPassword } = req.body;

  db.query('SELECT * FROM signUpList WHERE mobileNumber = ?', [mobileNumber], async (err, results) => {
    if (results.length === 0) return res.json({ success: false, message: "Mobile number not found" });

    const user = results[0];
    const isMatch = await bcrypt.compare(signUpPassword, user.signUpPassword);

    if (!isMatch) return res.json({ success: false, message: "Wrong password" });

    const token = jwt.sign({ id: user.id, mobile: user.mobileNumber }, JWT_SECRET, { expiresIn: "7d" });

    res.json({
      success: true,
      message: "Login successful",
      token,
      user: {
        firstName: user.firstName,
        lastName: user.lastName,
        email: user.email
      }
    });
  });
});

function auth(req, res, next) {
  const header = req.headers.authorization;
  if (!header) return res.status(401).json({ message: "Missing token" });

  const token = header.split(" ")[1];
  jwt.verify(token, JWT_SECRET, (err, decoded) => {
    if (err) return res.status(401).json({ message: "Invalid token" });
    req.user = decoded;
    next();
  });
}

app.get("/profile", auth, (req, res) => {
  db.query("SELECT firstName, lastName, mobileNumber, email FROM signUpList WHERE id = ?", 
  [req.user.id], (err, results) => {
    res.json(results[0]);
  });
});

app.get('/checkMobile/:mobile', (req, res) => {
  db.query('SELECT * FROM signUpList WHERE mobileNumber = ?', [req.params.mobile], (err, result) => {
    res.json({ exists: result.length > 0 });
  });
});

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});
