const express = require('express');
const router = express.Router();
const paperController = require('../controllers/paperController');

router.get('/', paperController.getAllPapers);
router.post('/submit', paperController.submitPaper);
router.post('/assign', paperController.assignReviewer);
router.post('/review', paperController.submitReview);
router.post('/decision', paperController.finalizeDecision);
router.post('/revise', paperController.submitRevision);
router.get('/author/:walletAddress', paperController.getMyPapers);
router.get('/assigned/:walletAddress', paperController.getAssignedPapers);
router.get('/revisions/:paperHash', paperController.getPaperRevisions);
router.get('/:paperHash', paperController.getPaperDetails);

module.exports = router;
