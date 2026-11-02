/**
 * Bike Management Controller
 * Handles bike search, filtering, pagination, creation with image uploads, updates, and deletion.
 */

const db = require('../config/db');

/**
 * Format bike object for consistent API response with both new and legacy field names
 */
function formatBike(b) {
  if (!b) return null;
  let images = [];
  if (Array.isArray(b.images)) {
    images = b.images;
  } else if (typeof b.images === 'string') {
    try {
      images = JSON.parse(b.images);
    } catch (e) {
      images = b.images ? [b.images] : [];
    }
  }

  const primaryImage = images.length > 0 ? images[0] : (b.image || 'https://images.unsplash.com/photo-1558981403-c5f9899a28bc?auto=format&fit=crop&w=600&q=80');

  return {
    id: b.id,
    title: b.title || b.listingTitle,
    brand: b.brand || b.makedFrom || 'Standard',
    model: b.model || b.bikeModel || '',
    year: b.year || b.bikeBuyingYear || '',
    price: parseFloat(b.price || b.bikePrice || 0),
    selling_price: parseFloat(b.selling_price || b.sellingPrice || b.price || b.bikePrice || 0),
    kilometers_driven: b.kilometers_driven || b.bikeKms || '0',
    fuel_type: b.fuel_type || 'Petrol',
    transmission: b.transmission || 'Manual',
    description: b.description || '',
    images: images.length > 0 ? images : [primaryImage],
    image: primaryImage, // Legacy compatibility
    seller_id: b.seller_id || null,
    seller_name: b.seller_name || b.sellerName || '',
    seller_phone: b.seller_phone || b.mobileNum || '',
    vehicle_number: b.vehicle_number || b.vehicleNumber || '',
    bike_condition: b.bike_condition || b.bikeCondition || 'Good',
    bike_color: b.bike_color || b.bikeColor || '',
    engine_cc: b.engine_cc || b.bikeEngineCC || '',
    insurance: b.insurance || 'No',
    horsepower: b.horsepower || 'No',
    location: b.location || b.bikeLocation || '',
    category_id: b.category_id || 1,
    status: b.status || (b.isSoldout ? 'soldout' : (b.isAccepted ? 'approved' : 'pending')),
    rejection_reason: b.rejection_reason || null,
    created_at: b.created_at || new Date(),
    updated_at: b.updated_at || new Date(),

    // Legacy fields mapping for backwards compatibility
    listingTitle: b.title || b.listingTitle,
    vehicleNumber: b.vehicle_number || b.vehicleNumber,
    sellerName: b.seller_name || b.sellerName,
    mobileNum: b.seller_phone || b.mobileNum,
    bikeCondition: b.bike_condition || b.bikeCondition,
    bikeType: b.brand || b.bikeType,
    makedFrom: b.brand || b.makedFrom,
    bikeModel: b.model || b.bikeModel,
    bikeKms: b.kilometers_driven || b.bikeKms,
    bikePrice: b.price || b.bikePrice,
    sellingPrice: b.selling_price || b.sellingPrice,
    bikeOwner: b.bikeOwner || 'First Owner',
    bikeBuyingYear: b.year || b.bikeBuyingYear,
    bikeColor: b.bike_color || b.bikeColor,
    bikeEngineCC: b.engine_cc || b.bikeEngineCC,
    driveType: b.driveType || 'Chain',
    bikeLocation: b.location || b.bikeLocation,
    isAccepted: b.status === 'approved' || b.isAccepted === 1,
    isSoldout: b.status === 'soldout' || b.isSoldout === 1
  };
}

/**
 * GET /api/bikes
 * Query params: minPrice, maxPrice, brand, model, search, category, status, page, limit
 */
async function getBikes(req, res) {
  try {
    const {
      minPrice,
      maxPrice,
      brand,
      model,
      search,
      category,
      status,
      page = 1,
      limit = 100
    } = req.query;

    const pageNum = Math.max(1, parseInt(page, 10));
    const limitNum = Math.min(100, Math.max(1, parseInt(limit, 10)));
    const offset = (pageNum - 1) * limitNum;

    let bikes = [];
    if (db.getIsConnected()) {
      let conditions = [];
      let params = [];

      // Default to approved bikes for public view unless specific status is requested
      if (status && status !== 'all') {
        conditions.push('status = ?');
        params.push(status);
      } else if (!status) {
        conditions.push('(status = "approved" OR status IS NULL)');
      }

      if (brand && brand !== 'all') {
        conditions.push('(brand = ? OR title LIKE ?)');
        params.push(brand, `%${brand}%`);
      }

      if (minPrice) {
        conditions.push('(COALESCE(selling_price, price) >= ?)');
        params.push(parseFloat(minPrice));
      }

      if (maxPrice) {
        conditions.push('(COALESCE(selling_price, price) <= ?)');
        params.push(parseFloat(maxPrice));
      }

      if (search) {
        conditions.push('(title LIKE ? OR brand LIKE ? OR model LIKE ? OR description LIKE ?)');
        const searchPattern = `%${search}%`;
        params.push(searchPattern, searchPattern, searchPattern, searchPattern);
      }

      const whereClause = conditions.length > 0 ? `WHERE ${conditions.join(' AND ')}` : '';
      const querySql = `SELECT * FROM bikes ${whereClause} ORDER BY created_at DESC LIMIT ? OFFSET ?`;
      params.push(limitNum, offset);

      bikes = await db.query(querySql, params);
    } else {
      let list = db.fallbackStore.bikes;
      if (status && status !== 'all') {
        list = list.filter(b => b.status === status);
      } else if (!status) {
        list = list.filter(b => b.status === 'approved');
      }

      if (brand && brand !== 'all') {
        list = list.filter(b => (b.brand || '').toLowerCase() === brand.toLowerCase() || (b.title || '').toLowerCase().includes(brand.toLowerCase()));
      }

      if (minPrice) {
        const minP = parseFloat(minPrice);
        list = list.filter(b => (b.selling_price || b.price) >= minP);
      }

      if (maxPrice) {
        const maxP = parseFloat(maxPrice);
        list = list.filter(b => (b.selling_price || b.price) <= maxP);
      }

      if (search) {
        const q = search.toLowerCase();
        list = list.filter(b => (b.title || '').toLowerCase().includes(q) || (b.brand || '').toLowerCase().includes(q) || (b.model || '').toLowerCase().includes(q));
      }

      bikes = list.slice(offset, offset + limitNum);
    }

    const formatted = bikes.map(formatBike);

    // If request asks for json array (legacy style for /bikes)
    if (req.originalUrl === '/bikes' || req.query.format === 'legacy') {
      return res.json(formatted);
    }

    return res.json({
      success: true,
      count: formatted.length,
      page: pageNum,
      limit: limitNum,
      bikes: formatted
    });
  } catch (err) {
    console.error('[GetBikes Error]:', err.message);
    return res.status(500).json({ success: false, message: 'Failed to retrieve bikes.' });
  }
}

/**
 * GET /api/bikes/:id
 */
async function getBikeById(req, res) {
  try {
    const bikeId = parseInt(req.params.id, 10);
    if (isNaN(bikeId)) {
      return res.status(400).json({ success: false, message: 'Invalid bike ID.' });
    }

    let bike = null;
    if (db.getIsConnected()) {
      const rows = await db.query('SELECT * FROM bikes WHERE id = ?', [bikeId]);
      if (rows && rows.length > 0) bike = rows[0];
    } else {
      bike = db.fallbackStore.bikes.find(b => b.id === bikeId);
    }

    if (!bike) {
      return res.status(404).json({ success: false, message: 'Bike not found.' });
    }

    const formatted = formatBike(bike);
    if (req.originalUrl.startsWith('/bikes/')) {
      return res.json(formatted);
    }

    return res.json({
      success: true,
      bike: formatted
    });
  } catch (err) {
    console.error('[GetBikeById Error]:', err.message);
    return res.status(500).json({ success: false, message: 'Failed to retrieve bike.' });
  }
}

/**
 * POST /api/bikes
 * Handles both new & legacy field names and multer uploaded images
 */
async function createBike(req, res) {
  try {
    const data = req.body;

    // Process uploaded files if any
    let uploadedImageUrls = [];
    if (req.files && req.files.length > 0) {
      uploadedImageUrls = req.files.map(f => `/uploads/${f.filename}`);
    } else if (data.images) {
      if (Array.isArray(data.images)) {
        uploadedImageUrls = data.images;
      } else if (typeof data.images === 'string') {
        try {
          uploadedImageUrls = JSON.parse(data.images);
        } catch (e) {
          uploadedImageUrls = [data.images];
        }
      }
    } else if (data.image) {
      uploadedImageUrls = [data.image];
    }

    // Default image if none provided
    if (uploadedImageUrls.length === 0) {
      uploadedImageUrls = ['https://images.unsplash.com/photo-1558981403-c5f9899a28bc?auto=format&fit=crop&w=600&q=80'];
    }

    const title = data.title || data.listingTitle || 'Untitled Bike';
    const brand = data.brand || data.makedFrom || data.bikeType || 'Standard';
    const model = data.model || data.bikeModel || title;
    const year = data.year || data.bikeBuyingYear || '2022';
    const price = parseFloat(data.price || data.bikePrice || 0);
    const sellingPrice = parseFloat(data.selling_price || data.sellingPrice || price);
    const kms = data.kilometers_driven || data.bikeKms || '0';
    const fuelType = data.fuel_type || 'Petrol';
    const transmission = data.transmission || 'Manual';
    const description = data.description || '';
    const vehicleNumber = data.vehicle_number || data.vehicleNumber || '';
    const bikeCondition = data.bike_condition || data.bikeCondition || 'Good';
    const bikeColor = data.bike_color || data.bikeColor || 'Black';
    const engineCC = data.engine_cc || data.bikeEngineCC || '150cc';
    const insurance = data.insurance || 'No';
    const horsepower = data.horsepower || 'No';
    const location = data.location || data.bikeLocation || 'Chennai';
    const categoryId = parseInt(data.category_id || 1, 10);

    // Determine seller
    const sellerId = req.user ? req.user.id : (data.seller_id || null);
    const sellerName = req.user ? req.user.name : (data.sellerName || data.seller_name || 'Individual');
    const sellerPhone = req.user ? (req.user.phone || data.mobileNum || '') : (data.mobileNum || data.seller_phone || '');

    // Status: Admin creates approved bikes directly, Users create pending bikes
    const isAdmin = req.admin || (req.user && req.user.role === 'admin');
    const status = isAdmin ? 'approved' : 'pending';

    let newId;
    if (db.getIsConnected()) {
      const sql = `
        INSERT INTO bikes (
          title, brand, model, year, price, selling_price, kilometers_driven,
          fuel_type, transmission, description, images, seller_id, seller_name,
          seller_phone, vehicle_number, bike_condition, bike_color, engine_cc,
          insurance, horsepower, location, category_id, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `;

      const result = await db.query(sql, [
        title, brand, model, year, price, sellingPrice, kms,
        fuelType, transmission, description, JSON.stringify(uploadedImageUrls),
        sellerId, sellerName, sellerPhone, vehicleNumber, bikeCondition,
        bikeColor, engineCC, insurance, horsepower, location, categoryId, status
      ]);
      newId = result.insertId;
    } else {
      newId = db.fallbackStore.nextId.bikes++;
      const newBike = {
        id: newId,
        title, brand, model, year, price, selling_price: sellingPrice,
        kilometers_driven: kms, fuel_type: fuelType, transmission, description,
        images: uploadedImageUrls, seller_id: sellerId, seller_name: sellerName,
        seller_phone: sellerPhone, vehicle_number: vehicleNumber, bike_condition: bikeCondition,
        bike_color: bikeColor, engine_cc: engineCC, insurance, horsepower,
        location, category_id: categoryId, status,
        created_at: new Date(), updated_at: new Date()
      };
      db.fallbackStore.bikes.unshift(newBike);
    }

    return res.status(201).json({
      success: true,
      message: isAdmin ? 'Bike listing created and approved.' : 'Bike listing submitted for administrator review.',
      id: newId,
      status
    });
  } catch (err) {
    console.error('[CreateBike Error]:', err.message);
    return res.status(500).json({ success: false, message: 'Failed to create bike listing.' });
  }
}

/**
 * PUT /api/bikes/:id
 */
async function updateBike(req, res) {
  try {
    const bikeId = parseInt(req.params.id, 10);
    const data = req.body;

    // Check permissions: only owner or admin can update
    let bike;
    if (db.getIsConnected()) {
      const rows = await db.query('SELECT * FROM bikes WHERE id = ?', [bikeId]);
      bike = rows[0];
    } else {
      bike = db.fallbackStore.bikes.find(b => b.id === bikeId);
    }

    if (!bike) {
      return res.status(404).json({ success: false, message: 'Bike not found.' });
    }

    const isAdmin = req.admin || (req.user && req.user.role === 'admin');
    if (!isAdmin && req.user && bike.seller_id !== req.user.id) {
      return res.status(403).json({ success: false, message: 'Not authorized to modify this listing.' });
    }

    const title = data.title || data.listingTitle || bike.title;
    const price = data.price !== undefined ? parseFloat(data.price) : bike.price;
    const sellingPrice = data.selling_price !== undefined || data.sellingPrice !== undefined ? parseFloat(data.selling_price || data.sellingPrice) : bike.selling_price;
    const kms = data.kilometers_driven || data.bikeKms || bike.kilometers_driven;
    const description = data.description !== undefined ? data.description : bike.description;
    const status = isAdmin && data.status ? data.status : bike.status;

    if (db.getIsConnected()) {
      await db.query(
        'UPDATE bikes SET title = ?, price = ?, selling_price = ?, kilometers_driven = ?, description = ?, status = ?, updated_at = NOW() WHERE id = ?',
        [title, price, sellingPrice, kms, description, status, bikeId]
      );
    } else {
      bike.title = title;
      bike.price = price;
      bike.selling_price = sellingPrice;
      bike.kilometers_driven = kms;
      bike.description = description;
      bike.status = status;
      bike.updated_at = new Date();
    }

    return res.json({
      success: true,
      message: 'Bike listing updated successfully.'
    });
  } catch (err) {
    console.error('[UpdateBike Error]:', err.message);
    return res.status(500).json({ success: false, message: 'Failed to update bike.' });
  }
}

/**
 * DELETE /api/bikes/:id
 */
async function deleteBike(req, res) {
  try {
    const bikeId = parseInt(req.params.id, 10);

    let bike;
    if (db.getIsConnected()) {
      const rows = await db.query('SELECT * FROM bikes WHERE id = ?', [bikeId]);
      bike = rows[0];
    } else {
      bike = db.fallbackStore.bikes.find(b => b.id === bikeId);
    }

    if (!bike) {
      return res.status(404).json({ success: false, message: 'Bike not found.' });
    }

    const isAdmin = req.admin || (req.user && req.user.role === 'admin');
    if (!isAdmin && req.user && bike.seller_id !== req.user.id) {
      return res.status(403).json({ success: false, message: 'Not authorized to delete this listing.' });
    }

    if (db.getIsConnected()) {
      await db.query('DELETE FROM bikes WHERE id = ?', [bikeId]);
      await db.query('DELETE FROM favorites WHERE bike_id = ?', [bikeId]);
    } else {
      db.fallbackStore.bikes = db.fallbackStore.bikes.filter(b => b.id !== bikeId);
      db.fallbackStore.favorites = db.fallbackStore.favorites.filter(f => f.bike_id !== bikeId);
    }

    return res.json({
      success: true,
      message: 'Bike listing deleted successfully.'
    });
  } catch (err) {
    console.error('[DeleteBike Error]:', err.message);
    return res.status(500).json({ success: false, message: 'Failed to delete bike.' });
  }
}

module.exports = {
  getBikes,
  getBikeById,
  createBike,
  updateBike,
  deleteBike,
  formatBike
};
