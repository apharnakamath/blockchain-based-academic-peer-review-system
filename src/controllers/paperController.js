const Paper = require('../models/Paper');
const User = require('../models/User');
const { contract } = require('../config/web3');
const { ethers } = require('ethers');

const cidToBytes32 = (cid) => ethers.keccak256(ethers.toUtf8Bytes(cid));

// ─── SUBMIT PAPER ────────────────────────────────────────────────────────────
exports.submitPaper = async (req, res) => {
    const { title, abstract, authorWallet, ipfsCID } = req.body;
    if (!title || !abstract || !authorWallet || !ipfsCID)
        return res.status(400).json({ error: "title, abstract, authorWallet, and ipfsCID are required" });

    try {
        const paperHash = cidToBytes32(ipfsCID);

        const tx = await contract.submitPaper(paperHash);
        await tx.wait();

        const newPaper = new Paper({
            originalHash: paperHash,
            title,
            abstract,
            authorWallet,
            ipfsCID,
            revisions: [{ revisionHash: paperHash, ipfsCID }]
        });
        await newPaper.save();

        res.status(201).json({
            success: true,
            message: "Paper submitted successfully",
            txHash: tx.hash,
            paperHash
        });
    } catch (error) {
        console.error("Submission Error:", error);
        res.status(500).json({ error: error.message || "Failed to submit paper" });
    }
};

// ─── GET PAPER DETAILS ───────────────────────────────────────────────────────
exports.getPaperDetails = async (req, res) => {
    const { paperHash } = req.params;
    try {
        const paperMeta = await Paper.findOne({ originalHash: paperHash });
        if (!paperMeta) return res.status(404).json({ error: "Paper not found" });

        let blockchainState = null;
        try {
            const onChainData = await contract.papers(paperHash);
            blockchainState = {
                status: Number(onChainData.status),
                decision: Number(onChainData.finalDecision)
            };
        } catch (_) {}

        res.status(200).json({
            originalHash: paperMeta.originalHash,
            title: paperMeta.title,
            abstract: paperMeta.abstract,
            author: paperMeta.authorWallet,
            ipfsCID: paperMeta.ipfsCID,
            status: paperMeta.status,
            assignedReviewer: paperMeta.assignedReviewer,
            finalDecision: paperMeta.finalDecision,
            reviews: paperMeta.reviews,
            revisions: paperMeta.revisions,
            createdAt: paperMeta.createdAt,
            blockchainState
        });
    } catch (error) {
        res.status(500).json({ error: "Error fetching paper details" });
    }
};

// ─── GET ALL PAPERS ──────────────────────────────────────────────────────────
exports.getAllPapers = async (req, res) => {
    try {
        const papers = await Paper.find({}).sort({ createdAt: -1 });
        res.status(200).json({ papers });
    } catch (error) {
        res.status(500).json({ error: "Error fetching papers" });
    }
};

// ─── GET PAPERS BY AUTHOR ─────────────────────────────────────────────────────
exports.getMyPapers = async (req, res) => {
    const { walletAddress } = req.params;
    try {
        const papers = await Paper.find({ authorWallet: walletAddress.toLowerCase() }).sort({ createdAt: -1 });
        res.status(200).json({ papers });
    } catch (error) {
        res.status(500).json({ error: "Error fetching your papers" });
    }
};

// ─── GET PAPERS ASSIGNED TO REVIEWER ─────────────────────────────────────────
exports.getAssignedPapers = async (req, res) => {
    const { walletAddress } = req.params;
    try {
        const papers = await Paper.find({
            assignedReviewer: walletAddress.toLowerCase(),
            status: { $in: ['Under Review', 'Reviewed'] }
        }).sort({ createdAt: -1 });
        res.status(200).json({ papers });
    } catch (error) {
        res.status(500).json({ error: "Error fetching assigned papers" });
    }
};

// ─── ASSIGN REVIEWER ─────────────────────────────────────────────────────────
exports.assignReviewer = async (req, res) => {
    const { paperHash, reviewerWallet } = req.body;
    if (!paperHash || !reviewerWallet)
        return res.status(400).json({ error: "paperHash and reviewerWallet are required" });

    try {
        // Look up the reviewer's hash from DB
        const reviewer = await User.findOne({ walletAddress: reviewerWallet.toLowerCase(), role: 'Reviewer' });
        if (!reviewer) return res.status(404).json({ error: "Reviewer not found or not a reviewer role" });
        if (!reviewer.reviewerHash) return res.status(400).json({ error: "Reviewer has no hash registered" });

        const tx = await contract.assignReviewer(paperHash, reviewer.reviewerHash);
        await tx.wait();

        const paper = await Paper.findOneAndUpdate(
            { originalHash: paperHash },
            {
                assignedReviewer: reviewerWallet.toLowerCase(),
                assignedReviewerHash: reviewer.reviewerHash,
                status: 'Under Review'
            },
            { new: true }
        );
        if (!paper) return res.status(404).json({ error: "Paper not found" });

        res.status(200).json({ success: true, message: "Reviewer assigned", paper });
    } catch (error) {
        console.error("Assignment Error:", error);
        res.status(500).json({ error: error.message });
    }
};

// ─── SUBMIT REVIEW ───────────────────────────────────────────────────────────
exports.submitReview = async (req, res) => {
    const { paperHash, reviewerWallet, score, comments } = req.body;
    if (!paperHash || !reviewerWallet || score === undefined)
        return res.status(400).json({ error: "paperHash, reviewerWallet, and score are required" });
    if (score < 0 || score > 10)
        return res.status(400).json({ error: "Score must be between 0 and 10" });

    try {
        const paper = await Paper.findOne({ originalHash: paperHash });
        if (!paper) return res.status(404).json({ error: "Paper not found" });
        if (paper.assignedReviewer !== reviewerWallet.toLowerCase())
            return res.status(403).json({ error: "You are not assigned to review this paper" });
        if (paper.status === 'Accepted' || paper.status === 'Rejected')
            return res.status(400).json({ error: "Decision already finalized; no changes permitted" });

        const reviewer = await User.findOne({ walletAddress: reviewerWallet.toLowerCase() });
        if (!reviewer?.reviewerHash) return res.status(400).json({ error: "Reviewer hash not found" });

        const tx = await contract.submitReview(paperHash, score);
        await tx.wait();

        paper.reviews.push({
            reviewerHash: reviewer.reviewerHash,
            reviewerWallet: reviewerWallet.toLowerCase(),
            score,
            comments: comments || ''
        });
        paper.status = 'Reviewed';
        await paper.save();

        res.status(200).json({ success: true, message: "Review submitted successfully", txHash: tx.hash });
    } catch (error) {
        console.error("Review Error:", error);
        res.status(500).json({ error: error.message });
    }
};

// ─── FINALIZE DECISION ───────────────────────────────────────────────────────
exports.finalizeDecision = async (req, res) => {
    const { paperHash, decision } = req.body;
    // decision: 0=Pending, 1=Accepted, 2=Rejected, 3=RevisionRequired
    if (!paperHash || decision === undefined)
        return res.status(400).json({ error: "paperHash and decision are required" });

    const decisionMap = { 0: 'Pending', 1: 'Accepted', 2: 'Rejected', 3: 'Revision Required' };
    if (!decisionMap[decision]) return res.status(400).json({ error: "Invalid decision value (use 1=Accept, 2=Reject, 3=RevisionRequired)" });

    try {
        const paper = await Paper.findOne({ originalHash: paperHash });
        if (!paper) return res.status(404).json({ error: "Paper not found" });
        if (paper.status === 'Accepted' || paper.status === 'Rejected')
            return res.status(400).json({ error: "Decision already finalized; immutable record cannot be changed" });

        const tx = await contract.finalizeDecision(paperHash, decision);
        await tx.wait();

        paper.finalDecision = decisionMap[decision];
        paper.status = decisionMap[decision];
        await paper.save();

        res.status(200).json({ success: true, message: `Decision recorded: ${decisionMap[decision]}`, txHash: tx.hash });
    } catch (error) {
        console.error("Decision Error:", error);
        res.status(500).json({ error: error.message });
    }
};

// ─── SUBMIT REVISION ─────────────────────────────────────────────────────────
exports.submitRevision = async (req, res) => {
    const { originalHash, newIpfsCID, authorWallet } = req.body;
    if (!originalHash || !newIpfsCID || !authorWallet)
        return res.status(400).json({ error: "originalHash, newIpfsCID, and authorWallet are required" });

    try {
        const paper = await Paper.findOne({ originalHash });
        if (!paper) return res.status(404).json({ error: "Original paper not found" });
        if (paper.authorWallet !== authorWallet.toLowerCase())
            return res.status(403).json({ error: "Only the original author can submit a revision" });
        if (paper.status === 'Accepted' || paper.status === 'Rejected')
            return res.status(400).json({ error: "Decision is already finalized; no revisions permitted" });

        const newRevisionHash = cidToBytes32(newIpfsCID);

        const tx = await contract.submitRevision(originalHash, newRevisionHash);
        await tx.wait();

        paper.revisions.push({ revisionHash: newRevisionHash, ipfsCID: newIpfsCID });
        paper.ipfsCID = newIpfsCID;
        paper.status = 'Submitted';
        paper.assignedReviewer = null;
        paper.assignedReviewerHash = null;
        await paper.save();

        res.status(200).json({
            success: true,
            message: "Revision submitted. Paper re-enters review queue.",
            newRevisionHash,
            txHash: tx.hash
        });
    } catch (error) {
        console.error("Revision Error:", error);
        res.status(500).json({ error: error.message });
    }
};

// ─── GET PAPER REVISIONS ─────────────────────────────────────────────────────
exports.getPaperRevisions = async (req, res) => {
    const { paperHash } = req.params;
    try {
        const paper = await Paper.findOne({ originalHash: paperHash });
        if (!paper) return res.status(404).json({ error: "Paper not found" });

        let onChainRevisions = [];
        try {
            onChainRevisions = await contract.getPaperRevisions(paperHash);
        } catch (_) {}

        res.status(200).json({
            title: paper.title,
            revisions: paper.revisions,
            onChainRevisions
        });
    } catch (error) {
        res.status(500).json({ error: "Error fetching revisions" });
    }
};
