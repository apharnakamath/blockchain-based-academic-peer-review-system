const axios = require('axios');
require('dotenv').config();

const IPFSService = {
    uploadToIPFS: async (fileBuffer, fileName) => {
        const url = `https://api.pinata.cloud/pinning/pinFileToIPFS`;
        let data = new FormData();
        data.append('file', fileBuffer, fileName);
        const response = await axios.post(url, data, {
            headers: {
                'pinata_api_key': process.env.PINATA_API_KEY,
                'pinata_secret_api_key': process.env.PINATA_SECRET_KEY,
            }
        });
        return response.data.IpfsHash;
    }
};

module.exports = IPFSService;
