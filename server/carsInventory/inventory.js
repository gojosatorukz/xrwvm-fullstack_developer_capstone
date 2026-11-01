'use strict';
const mongoose = require('mongoose');
module.exports = mongoose.model('cars', new mongoose.Schema({dealer_id: {type:Number,required:true,index:true},make:String,model:String,bodyType:String,year:Number,mileage:Number,price:Number}));
