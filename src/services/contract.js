const { ethers } = require('ethers');
const { contract } = require('../config/web3');

const ContractService = {
    registerOnChain: async (userAddress, roleIndex, reviewerHash = ethers.ZeroHash) => {
        try {
            const tx = await contract.registerUser(userAddress, roleIndex, reviewerHash);
            return await tx.wait();
        } catch (error) {
            throw new Error(`Blockchain Registration Failed: ${error.message}`);
        }
    },
    submitPaperHash: async (paperHash) => {
        try {
            const tx = await contract.submitPaper(paperHash);
            return await tx.wait();
        } catch (error) {
            throw new Error(`Blockchain Submission Failed: ${error.message}`);
        }
    }
};

module.exports = ContractService;
