'use strict';
const express = require('express');
const mongoose = require('mongoose');
const Cars = require('./inventory');
const app = express();
const route = handler => (req,res,next) => Promise.resolve(handler(req,res)).catch(next);
function number(value) {const n=Number(value);if(!Number.isSafeInteger(n)||n<=0){const e=new Error('A positive integer is required.');e.status=400;throw e;}return n;}
function band(value,step,max){const n=number(value);if(n>max)return {$gt:max};return n<=step?{$lte:n}:{$gt:n-step,$lte:n};}
function filters(id,query){const result={dealer_id:number(id)};for(const field of ['make','model'])if(query[field])result[field]=String(query[field]);if(query.year)result.year={$gte:number(query.year)};if(query.mileage)result.mileage=band(query.mileage,50000,200000);if(query.price)result.price=band(query.price,20000,80000);return result;}
app.get('/',(_req,res)=>res.send('Welcome to the Mongoose Car Inventory API'));
app.get('/health',(_req,res)=>res.status(mongoose.connection.readyState===1?200:503).json({ready:mongoose.connection.readyState===1}));
app.get('/cars/:id',route(async(req,res)=>res.json(await Cars.find(filters(req.params.id,req.query)).lean())));
[['carsbymake','make'],['carsbymodel','model'],['carsbymaxmileage','mileage'],['carsbyprice','price'],['carsbyyear','year']].forEach(([path,field])=>app.get('/'+path+'/:id/:value',route(async(req,res)=>res.json(await Cars.find(filters(req.params.id,{[field]:req.params.value})).lean()))));
app.use((error,_req,res,_next)=>res.status(error.status||500).json({error:error.status?error.message:'Inventory service unavailable.'}));
async function start(){await mongoose.connect(process.env.MONGODB_URI||'mongodb://mongo_db:27017/carsInventory',{serverSelectionTimeoutMS:15000});if(await Cars.countDocuments()===0)await Cars.insertMany(require('./data/car_records.json').cars);const server=app.listen(Number(process.env.PORT||3050),()=>console.log('Inventory API listening on port 3050'));process.on('SIGTERM',()=>server.close(()=>mongoose.disconnect().then(()=>process.exit(0))));}
if(require.main===module)start().catch(error=>{console.error(error.message);process.exitCode=1;});
module.exports={app,start,filters};
