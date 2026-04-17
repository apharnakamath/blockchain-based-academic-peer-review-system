const mongoose = require('mongoose');

const ReviewSchema = new mongoose.Schema({
    reviewerHash: { type: String, required: true },
    reviewerWallet: { type: String, lowercase: true },
    score: { type: Number, min: 0, max: 10 },
    comments: { type: String },
    submittedAt: { type: Date, default: Date.now }
});

const PaperSchema = new mongoose.Schema({
    originalHash: { type: String, required: true, unique: true },
    title: { type: String, required: true },
    abstract: { type: String, required: true },
    authorWallet: { type: String, required: true, lowercase: true },
    ipfsCID: { type: String, required: true },
    status: {
        type: String,
        enum: ['Submitted', 'Under Review', 'Reviewed', 'Accepted', 'Rejected', 'Revision Required'],
        default: 'Submitted'
    },
    assignedReviewer: { type: String, lowercase: true, default: null },
    assignedReviewerHash: { type: String, default: null },
    finalDecision: { type: String, default: null },
    reviews: [ReviewSchema],
    revisions: [{
        revisionHash: String,
        ipfsCID: String,
        submittedAt: { type: Date, default: Date.now }
    }]
}, { timestamps: true });

module.exports = mongoose.model('Paper', PaperSchema);
