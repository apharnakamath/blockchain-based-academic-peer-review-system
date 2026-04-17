const User = require('../models/User');
const ContractService = require('../services/contract');
const { ethers } = require('ethers');

exports.registerUser = async (req, res) => {
    const { walletAddress, name, email, role, reviewerId } = req.body;
    if (!walletAddress || !name || !email || !role)
        return res.status(400).json({ error: "walletAddress, name, email, and role are required" });

    try {
        const rolesMap = { "Admin": 1, "Editor": 2, "Author": 3, "Reviewer": 4 };
        const roleIndex = rolesMap[role];
        if (!roleIndex) return res.status(400).json({ error: "Invalid role. Use Admin, Editor, Author, or Reviewer" });

        let reviewerHash = ethers.ZeroHash;
        if (role === "Reviewer") {
            if (!reviewerId) return res.status(400).json({ error: "reviewerId is required for Reviewer role" });
            reviewerHash = ethers.keccak256(ethers.toUtf8Bytes(reviewerId));
        }

       await ContractService.registerOnChain(walletAddress, roleIndex, reviewerHash);

        const user = new User({
            walletAddress,
            name,
            email,
            role,
            reviewerHash: role === "Reviewer" ? reviewerHash : null
        });
        await user.save();

        res.status(201).json({ success: true, message: `${role} registered on-chain and in database` });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
};

exports.getProfile = async (req, res) => {
    try {
        const user = await User.findOne({ walletAddress: req.params.address.toLowerCase() });
        if (!user) return res.status(404).json({ error: "User not found" });
        res.json(user);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
};

exports.getAllReviewers = async (req, res) => {
    try {
        const reviewers = await User.find({ role: 'Reviewer' }, 'walletAddress name email');
        res.json({ reviewers });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
};

exports.getAllUsers = async (req, res) => {
    try {
        const users = await User.find({}, 'walletAddress name email role createdAt');
        res.json({ users });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
};
