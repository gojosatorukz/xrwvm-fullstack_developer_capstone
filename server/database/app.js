'use strict';
const express = require('express');
const mongoose = require('mongoose');
const fs = require('node:fs');
const path = require('node:path');
const Reviews = require('./review');
const Dealerships = require('./dealership');
const app = express();
app.use(express.json({limit: '32kb'}));
const Counter = mongoose.model('review_counter', new mongoose.Schema({_id: String, value: Number}));
const route = handler => (req, res, next) => Promise.resolve(handler(req, res)).catch(next);
function id(value) {
  const number = Number(value);
  if (!Number.isSafeInteger(number) || number <= 0) {
    const error = new Error('A positive integer ID is required.'); error.status = 400; throw error;
  }
  return number;
}
app.get('/', (_req, res) => res.send('Welcome to the Mongoose API'));
app.get('/health', (_req, res) => res.status(mongoose.connection.readyState === 1 ? 200 : 503).json({ready: mongoose.connection.readyState === 1}));
app.get('/fetchReviews', route(async (_req, res) => res.json(await Reviews.find().sort({id: 1}).lean())));
app.get('/fetchReviews/dealer/:id', route(async (req, res) => res.json(await Reviews.find({dealership: id(req.params.id)}).sort({id: 1}).lean())));
app.get('/fetchDealers', route(async (_req, res) => res.json(await Dealerships.find().sort({id: 1}).lean())));
app.get('/fetchDealers/:state', route(async (req, res) => res.json(await Dealerships.find({state: req.params.state}).sort({id: 1}).lean())));
app.get('/fetchDealer/:id', route(async (req, res) => res.json(await Dealerships.find({id: id(req.params.id)}).lean())));
app.post('/insert_review', route(async (req, res) => {
  const data = req.body;
  const dealership = id(data.dealership);
  if (!await Dealerships.exists({id: dealership})) return res.status(404).json({error: 'Dealership not found.'});
  for (const field of ['name', 'review', 'purchase_date', 'car_make', 'car_model']) {
    if (typeof data[field] !== 'string' || !data[field].trim() || data[field].length > (field === 'review' ? 5000 : 200)) return res.status(400).json({error: `Invalid ${field}.`});
  }
  if (typeof data.purchase !== 'boolean' || !Number.isInteger(data.car_year) || data.car_year < 2015 || data.car_year > 2023 || !/^\d{4}-\d{2}-\d{2}$/.test(data.purchase_date) || Number.isNaN(Date.parse(data.purchase_date))) return res.status(400).json({error: 'Invalid purchase details.'});
  const counter = await Counter.findOneAndUpdate({_id: 'reviews'}, {$inc: {value: 1}}, {new: true});
  const saved = await Reviews.create({id: counter.value, dealership, name: data.name.trim(), review: data.review.trim(), purchase: data.purchase, purchase_date: data.purchase_date, car_make: data.car_make, car_model: data.car_model, car_year: data.car_year});
  res.status(201).json(saved);
}));
app.use((error, _req, res, _next) => {
  const status = error.status || (error.name === 'ValidationError' ? 400 : 500);
  if (status >= 500) console.error(error.message);
  res.status(status).json({error: status >= 500 ? 'Database service unavailable.' : error.message});
});
async function start() {
  await mongoose.connect(process.env.MONGODB_URI || 'mongodb://mongo_db:27017/dealershipsDB', {serverSelectionTimeoutMS: 15000});
  const load = name => JSON.parse(fs.readFileSync(path.join(__dirname, 'data', name + '.json'), 'utf8'));
  if (await Dealerships.countDocuments() === 0) await Dealerships.insertMany(load('dealerships').dealerships);
  if (await Reviews.countDocuments() === 0) await Reviews.insertMany(load('reviews').reviews);
  const latest = await Reviews.findOne().sort({id: -1}).lean();
  await Counter.updateOne({_id: 'reviews'}, {$max: {value: (latest && latest.id) || 0}}, {upsert: true});
  const server = app.listen(Number(process.env.PORT || 3030), () => console.log('Dealership API listening on port ' + (process.env.PORT || 3030)));
  process.on('SIGTERM', () => server.close(() => mongoose.disconnect().then(() => process.exit(0))));
}
if (require.main === module) start().catch(error => {console.error(error.message); process.exitCode = 1;});
module.exports = {app, start};
