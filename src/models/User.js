const mongoose = require('mongoose');

const UserSchema = new mongoose.Schema({
    walletAddress: { type: String, required: true, unique: true, lowercase: true },
    name: { type: String, required: true },
    email: { type: String, required: true, unique: true },
    role: { type: String, enum: ['Admin', 'Editor', 'Author', 'Reviewer'], default: 'Author' },
    reviewerHash: { type: String, sparse: true }
}, { timestamps: true });

module.exports = mongoose.model('User', UserSchema);
