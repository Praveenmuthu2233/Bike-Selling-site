/**
 * Category Management Controller
 */

const db = require('../config/db');

async function getCategories(req, res) {
  try {
    let categories = [];
    if (db.getIsConnected()) {
      categories = await db.query('SELECT * FROM categories ORDER BY id ASC');
    } else {
      categories = db.fallbackStore.categories;
    }
    return res.json({ success: true, categories });
  } catch (err) {
    return res.status(500).json({ success: false, message: err.message });
  }
}

async function createCategory(req, res) {
  try {
    const { category_name, description, image_url } = req.body;
    if (!category_name) {
      return res.status(400).json({ success: false, message: 'Category name is required.' });
    }

    let insertId;
    if (db.getIsConnected()) {
      const result = await db.query(
        'INSERT INTO categories (category_name, description, image_url, status) VALUES (?, ?, ?, ?)',
        [category_name, description || '', image_url || '', 'active']
      );
      insertId = result.insertId;
    } else {
      insertId = db.fallbackStore.nextId.categories++;
      db.fallbackStore.categories.push({
        id: insertId,
        category_name,
        description: description || '',
        image_url: image_url || '',
        status: 'active',
        created_at: new Date()
      });
    }

    return res.status(201).json({ success: true, message: 'Category created.', id: insertId });
  } catch (err) {
    return res.status(500).json({ success: false, message: err.message });
  }
}

async function updateCategory(req, res) {
  try {
    const id = parseInt(req.params.id, 10);
    const { category_name, description, image_url, status } = req.body;

    if (db.getIsConnected()) {
      await db.query(
        'UPDATE categories SET category_name = COALESCE(?, category_name), description = COALESCE(?, description), image_url = COALESCE(?, image_url), status = COALESCE(?, status) WHERE id = ?',
        [category_name, description, image_url, status, id]
      );
    } else {
      const c = db.fallbackStore.categories.find(item => item.id === id);
      if (c) {
        if (category_name) c.category_name = category_name;
        if (description) c.description = description;
        if (image_url) c.image_url = image_url;
        if (status) c.status = status;
      }
    }

    return res.json({ success: true, message: 'Category updated.' });
  } catch (err) {
    return res.status(500).json({ success: false, message: err.message });
  }
}

async function deleteCategory(req, res) {
  try {
    const id = parseInt(req.params.id, 10);
    if (db.getIsConnected()) {
      await db.query('DELETE FROM categories WHERE id = ?', [id]);
    } else {
      db.fallbackStore.categories = db.fallbackStore.categories.filter(c => c.id !== id);
    }
    return res.json({ success: true, message: 'Category deleted.' });
  } catch (err) {
    return res.status(500).json({ success: false, message: err.message });
  }
}

module.exports = {
  getCategories,
  createCategory,
  updateCategory,
  deleteCategory
};
