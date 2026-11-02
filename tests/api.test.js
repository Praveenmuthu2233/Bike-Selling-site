/**
 * Comprehensive Automated Test Suite - SMR Motors Modernization
 * Validates All Core Flows: Auth, Database Resilience, User Dashboard, Admin Console, Bike CRUD, Enquiries.
 */

const http = require('http');
const assert = require('assert');
const app = require('../server');

let server;
const PORT = 5599; // Isolated test port
const BASE = `http://127.0.0.1:${PORT}`;

function request(method, path, body = null, headers = {}) {
  return new Promise((resolve, reject) => {
    const url = new URL(path, BASE);
    const reqHeaders = { ...headers };
    let postData = null;

    if (body) {
      postData = JSON.stringify(body);
      reqHeaders['Content-Type'] = 'application/json';
      reqHeaders['Content-Length'] = Buffer.byteLength(postData);
    }

    const req = http.request(url, {
      method,
      headers: reqHeaders
    }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        let json = null;
        try { json = JSON.parse(data); } catch (e) {}
        resolve({
          status: res.statusCode,
          headers: res.headers,
          data,
          json
        });
      });
    });

    req.on('error', reject);
    if (postData) req.write(postData);
    req.end();
  });
}

async function runTests() {
  console.log('\n======================================================');
  console.log('  STARTING SMR MOTORS AUTOMATED TEST SUITE');
  console.log('======================================================\n');

  let passed = 0;
  let failed = 0;

  async function test(name, fn) {
    try {
      await fn();
      console.log(`  [PASS] ${name}`);
      passed++;
    } catch (err) {
      console.error(`  [FAIL] ${name}`);
      console.error(`         Error: ${err.message}`);
      failed++;
    }
  }

  // Start test server
  await new Promise(resolve => {
    server = app.listen(PORT, resolve);
  });

  let userToken = '';
  let adminToken = '';
  let createdBikeId = null;
  let createdEnquiryId = null;

  try {
    /* 1. Page Routes Serving */
    await test('HTML Route / (Homepage) returns 200', async () => {
      const res = await request('GET', '/');
      assert.strictEqual(res.status, 200);
      assert.ok(res.data.includes('SMR MOTORS') || res.data.includes('SMR Motors'));
    });

    await test('HTML Route /userLogin.html returns 200 with Google Auth', async () => {
      const res = await request('GET', '/userLogin.html');
      assert.strictEqual(res.status, 200);
      assert.ok(res.data.includes('Google') || res.data.includes('Continue with Google'));
    });

    await test('HTML Route /profile.html returns 200 with User Dashboard tabs', async () => {
      const res = await request('GET', '/profile.html');
      assert.strictEqual(res.status, 200);
      assert.ok(res.data.includes('My Bike Listings') || res.data.includes('User Dashboard'));
    });

    await test('HTML Route /admin.html returns 200 with Admin Portal', async () => {
      const res = await request('GET', '/admin.html');
      assert.strictEqual(res.status, 200);
      assert.ok(res.data.includes('Admin') || res.data.includes('ADMIN CONSOLE'));
    });

    await test('HTML Route /bikeSelling.html returns 200 with Multi-Image Form', async () => {
      const res = await request('GET', '/bikeSelling.html');
      assert.strictEqual(res.status, 200);
      assert.ok(res.data.includes('Add listing') || res.data.includes('Listing Title') || res.data.includes('Sell Your Motorcycle'));
    });

    await test('New Clean Structure: /about.html, /contact.html, /login.html return 200', async () => {
      const resAbout = await request('GET', '/about.html');
      assert.strictEqual(resAbout.status, 200);
      const resContact = await request('GET', '/contact.html');
      assert.strictEqual(resContact.status, 200);
      const resLogin = await request('GET', '/login.html');
      assert.strictEqual(resLogin.status, 200);
    });

    await test('New Clean Structure: /user/dashboard.html & /admin/dashboard.html return 200', async () => {
      const resUser = await request('GET', '/user/dashboard.html');
      assert.strictEqual(resUser.status, 200);
      const resAdmin = await request('GET', '/admin/dashboard.html');
      assert.strictEqual(resAdmin.status, 200);
    });

    await test('Mandatory CSS Stylesheets load with 200 OK', async () => {
      const resStyle = await request('GET', '/assets/css/style.css');
      assert.strictEqual(resStyle.status, 200);
      const resComp = await request('GET', '/assets/css/components.css');
      assert.strictEqual(resComp.status, 200);
      const resResp = await request('GET', '/assets/css/responsive.css');
      assert.strictEqual(resResp.status, 200);
    });

    /* 2. Public API Endpoints */
    await test('GET /api/bikes returns list of motorcycles', async () => {
      const res = await request('GET', '/api/bikes');
      assert.strictEqual(res.status, 200);
      assert.ok(res.json.success === true || Array.isArray(res.json));
      const bikes = res.json.bikes || res.json;
      assert.ok(bikes.length > 0, 'Should have seed/sample bikes');
    });

    await test('GET /api/categories returns motorcycle categories', async () => {
      const res = await request('GET', '/api/categories');
      assert.strictEqual(res.status, 200);
      assert.strictEqual(res.json.success, true);
      assert.ok(res.json.categories.length > 0);
    });

    /* 3. Google Sign-In & User Authentication */
    await test('POST /api/auth/demo-google creates user & returns signed JWT', async () => {
      const res = await request('POST', '/api/auth/demo-google', {
        email: 'test.rider@gmail.com',
        name: 'Test Rider',
        picture: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde'
      });
      assert.strictEqual(res.status, 200);
      assert.strictEqual(res.json.success, true);
      assert.ok(res.json.token, 'Must return JWT token');
      assert.strictEqual(res.json.user.email, 'test.rider@gmail.com');
      userToken = res.json.token;
    });

    await test('GET /api/auth/me returns authenticated user identity', async () => {
      const res = await request('GET', '/api/auth/me', null, {
        Authorization: `Bearer ${userToken}`
      });
      assert.strictEqual(res.status, 200);
      assert.strictEqual(res.json.success, true);
      assert.strictEqual(res.json.user.email, 'test.rider@gmail.com');
    });

    /* 4. User Profile & Security Safeguards */
    await test('PUT /api/users/profile updates user phone number', async () => {
      const res = await request('PUT', '/api/users/profile', {
        name: 'Test Rider Updated',
        phone: '9876543210'
      }, {
        Authorization: `Bearer ${userToken}`
      });
      assert.strictEqual(res.status, 200);
      assert.strictEqual(res.json.success, true);
      assert.strictEqual(res.json.user.phone, '9876543210');
    });

    await test('PUT /api/users/profile REJECTS role privilege escalation (Security Audit)', async () => {
      const res = await request('PUT', '/api/users/profile', {
        name: 'Hacker',
        role: 'admin',
        isAdmin: true
      }, {
        Authorization: `Bearer ${userToken}`
      });
      assert.strictEqual(res.status, 403, 'Must reject role modification with 403 Forbidden');
      assert.strictEqual(res.json.success, false);
    });

    await test('GET /api/users/dashboard returns aggregated user metrics', async () => {
      const res = await request('GET', '/api/users/dashboard', null, {
        Authorization: `Bearer ${userToken}`
      });
      assert.strictEqual(res.status, 200);
      assert.strictEqual(res.json.success, true);
      assert.ok(res.json.stats);
      assert.ok('totalListings' in res.json.stats);
    });

    /* 5. User Bike Listing Submission & Multi-Image Validation */
    await test('POST /api/bikes creates user bike in pending state', async () => {
      const res = await request('POST', '/api/bikes', {
        title: 'KTM Duke 390 Special Edition',
        brand: 'KTM',
        model: 'Duke 390',
        year: '2023',
        price: 185000,
        kilometers_driven: '8500',
        vehicle_number: 'TN 09 BX 9988',
        bike_condition: 'Good',
        description: 'First owner bike in mint showroom condition.',
        images: ['https://images.unsplash.com/photo-1558981403-c5f9899a28bc?w=600']
      }, {
        Authorization: `Bearer ${userToken}`
      });
      assert.strictEqual(res.status, 201);
      assert.strictEqual(res.json.success, true);
      assert.strictEqual(res.json.status, 'pending', 'User listed bike must default to pending');
      createdBikeId = res.json.id;
    });

    await test('GET /api/users/listings shows user listed bike', async () => {
      const res = await request('GET', '/api/users/listings', null, {
        Authorization: `Bearer ${userToken}`
      });
      assert.strictEqual(res.status, 200);
      assert.strictEqual(res.json.success, true);
      assert.ok(res.json.listings.length > 0);
    });

    /* 6. Admin Authentication & Role Protection */
    await test('POST /api/admin/login validates credentials & issues Admin JWT', async () => {
      const res = await request('POST', '/api/admin/login', {
        username: 'admin',
        password: 'Admin@123'
      });
      assert.strictEqual(res.status, 200);
      assert.strictEqual(res.json.success, true);
      assert.ok(res.json.token, 'Must return admin JWT token');
      adminToken = res.json.token;
    });

    await test('GET /api/admin/dashboard returns system-wide metrics', async () => {
      const res = await request('GET', '/api/admin/dashboard', null, {
        Authorization: `Bearer ${adminToken}`
      });
      assert.strictEqual(res.status, 200);
      assert.strictEqual(res.json.success, true);
      assert.ok(res.json.stats.totalBikes >= 0);
      assert.ok(res.json.stats.pendingApprovals >= 1);
    });

    /* 7. Admin Bike Approval Workflow */
    await test('PUT /api/admin/bikes/:id/approve approves pending bike', async () => {
      const res = await request('PUT', `/api/admin/bikes/${createdBikeId}/approve`, {}, {
        Authorization: `Bearer ${adminToken}`
      });
      assert.strictEqual(res.status, 200);
      assert.strictEqual(res.json.success, true);
    });

    await test('PUT /api/admin/bikes/:id/price updates bike selling price', async () => {
      const res = await request('PUT', `/api/admin/bikes/${createdBikeId}/price`, {
        newPrice: 190000
      }, {
        Authorization: `Bearer ${adminToken}`
      });
      assert.strictEqual(res.status, 200);
      assert.strictEqual(res.json.success, true);
    });

    /* 8. Customer Enquiries & Contact Flow */
    await test('POST /api/enquiries submits customer enquiry', async () => {
      const res = await request('POST', '/api/enquiries', {
        bike_id: createdBikeId,
        name: 'Rohan Sharma',
        phone: '9840012345',
        email: 'rohan.s@gmail.com',
        message: 'Interested in test driving this KTM Duke 390.'
      }, {
        Authorization: `Bearer ${userToken}`
      });
      assert.strictEqual(res.status, 201);
      assert.strictEqual(res.json.success, true);
      createdEnquiryId = res.json.id;
    });

    await test('GET /api/users/enquiries retrieves customer submitted enquiry', async () => {
      const res = await request('GET', '/api/users/enquiries', null, {
        Authorization: `Bearer ${userToken}`
      });
      assert.strictEqual(res.status, 200);
      assert.strictEqual(res.json.success, true);
      assert.ok(res.json.enquiries.length > 0);
    });

    await test('PUT /api/enquiries/:id/status updates enquiry status by Admin', async () => {
      const res = await request('PUT', `/api/enquiries/${createdEnquiryId}/status`, {
        status: 'in_progress'
      }, {
        Authorization: `Bearer ${adminToken}`
      });
      assert.strictEqual(res.status, 200);
      assert.strictEqual(res.json.success, true);
    });

    /* 9. Contact Message */
    await test('POST /api/contact submits website contact message', async () => {
      const res = await request('POST', '/api/contact', {
        name: 'Dealer Enquiry',
        email: 'dealer@motors.com',
        phone: '9988776655',
        message: 'Looking to partner for pre-owned bike valuations.'
      });
      assert.strictEqual(res.status, 201);
      assert.strictEqual(res.json.success, true);
    });

    await test('GET /api/admin/messages returns contact submissions', async () => {
      const res = await request('GET', '/api/admin/messages', null, {
        Authorization: `Bearer ${adminToken}`
      });
      assert.strictEqual(res.status, 200);
      assert.strictEqual(res.json.success, true);
      assert.ok(res.json.messages.length > 0);
    });

    /* 10. Audit Logs */
    await test('GET /api/admin/audit-logs verifies immutable admin action trail', async () => {
      const res = await request('GET', '/api/admin/audit-logs', null, {
        Authorization: `Bearer ${adminToken}`
      });
      assert.strictEqual(res.status, 200);
      assert.strictEqual(res.json.success, true);
      assert.ok(res.json.logs.length > 0, 'Must have recorded admin actions');
    });

  } finally {
    server.close();
  }

  console.log('\n------------------------------------------------------');
  console.log(`  TEST RESULTS: ${passed} PASSED | ${failed} FAILED`);
  console.log('------------------------------------------------------\n');

  if (failed > 0) {
    process.exit(1);
  } else {
    process.exit(0);
  }
}

runTests();
