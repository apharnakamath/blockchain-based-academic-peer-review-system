const { ethers } = require('ethers');

const verifyWalletSignature = (req, res, next) => {
    const { signature, message, walletaddress } = req.headers;
    if (!signature || !message || !walletaddress) return next();
    try {
        const recoveredAddress = ethers.verifyMessage(message, signature);
        if (recoveredAddress.toLowerCase() !== walletaddress.toLowerCase())
            return res.status(401).json({ error: "Signature verification failed" });
        req.userWallet = recoveredAddress.toLowerCase();
        next();
    } catch (err) {
        res.status(400).json({ error: "Invalid signature format" });
    }
};

module.exports = verifyWalletSignature;
