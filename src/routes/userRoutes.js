const express = require('express');
const router = express.Router();
const userController = require('../controllers/userController');

router.post('/register', userController.registerUser);
router.get('/all', userController.getAllUsers);
router.get('/reviewers', userController.getAllReviewers);
router.get('/:address', userController.getProfile);

module.exports = router;
