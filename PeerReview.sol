// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title AcademicPeerReview
 * @notice Blockchain-based academic peer review system with immutable audit trail.
 *
 * Consensus Choice: Proof-of-Authority (PoA) / Clique (Ethereum-compatible)
 * ─────────────────────────────────────────────────────────────────────────
 * Rationale: Academic peer review involves a known, trusted consortium
 * (universities, journals, funding bodies). PoA is ideal because:
 *   1. Validators are pre-approved institutions — aligns with real-world trust.
 *   2. Deterministic finality: once a block is sealed, it is final — no forks
 *      that could allow re-ordering of review decisions.
 *   3. High throughput at negligible cost — no expensive PoW mining or large
 *      PoS stake needed; academic networks are not high-volume financial chains.
 *   4. Energy-efficient — important for academic/public-good infrastructure.
 *   5. Sybil-resistant by identity, not capital — consistent with academia's
 *      credential-based trust model.
 * Deployment target: a private/consortium Ethereum chain (e.g., Hyperledger
 * Besu with Clique consensus), or a public testnet for prototyping.
 */
contract AcademicPeerReview {

    // ─── Enumerations ────────────────────────────────────────────────────────

    enum Role        { None, Author, Reviewer, Editor, Admin }
    enum PaperStatus { Submitted, UnderReview, Revised, Accepted, Rejected }

    // ─── Structs ─────────────────────────────────────────────────────────────

    struct Paper {
        bytes32  paperHash;          // keccak256 of manuscript content
        address  author;
        uint256  submittedAt;
        PaperStatus status;
        uint8    versionCount;       // starts at 1
        bytes32  originalPaperId;   // 0x0 for v1; points to root for revisions
        bool     finalized;          // locks all further writes
    }

    struct ReviewAssignment {
        bytes32  reviewerIdHash;     // keccak256(reviewerAddress + salt) — anonymous on-chain
        uint256  assignedAt;
        bool     completed;
    }

    struct ReviewScore {
        bytes32  reviewerIdHash;
        uint8    score;              // 1–10
        string   recommendation;    // "Accept" | "Minor Revision" | "Major Revision" | "Reject"
        uint256  submittedAt;
    }

    struct Decision {
        string   outcome;            // "Accepted" | "Rejected" | "Revision Required"
        address  editor;
        uint256  decidedAt;
    }

    // ─── State Variables ─────────────────────────────────────────────────────

    address public admin;
    uint256 private _paperCounter;

    mapping(address => Role)                          public  roles;
    mapping(uint256 => Paper)                         public  papers;
    mapping(uint256 => ReviewAssignment[])            private _assignments;   // paperId → assignments
    mapping(uint256 => ReviewScore[])                 private _scores;        // paperId → scores
    mapping(uint256 => Decision)                      private _decisions;     // paperId → final decision
    // reviewer wallet → salt (set once by admin, used to derive reviewerIdHash)
    mapping(address => bytes32)                       private _reviewerSalts;
    // paperId → reviewerIdHash → assigned? (for access control)
    mapping(uint256 => mapping(bytes32 => bool))      private _assignedReviewer;

    // ─── Events ───────────────────────────────────────────────────────────────

    event RoleGranted(address indexed account, Role role, uint256 timestamp);
    event PaperSubmitted(uint256 indexed paperId, bytes32 paperHash, address indexed author, uint8 version, uint256 timestamp);
    event ReviewerAssigned(uint256 indexed paperId, bytes32 reviewerIdHash, uint256 timestamp);
    event ScoreSubmitted(uint256 indexed paperId, bytes32 reviewerIdHash, uint8 score, string recommendation, uint256 timestamp);
    event DecisionRecorded(uint256 indexed paperId, string outcome, address indexed editor, uint256 timestamp);
    event RevisionSubmitted(uint256 indexed newPaperId, uint256 indexed originalPaperId, bytes32 newHash, uint256 timestamp);

    // ─── Modifiers ────────────────────────────────────────────────────────────

    modifier onlyAdmin() {
        require(roles[msg.sender] == Role.Admin, "Only admin");
        _;
    }
    modifier onlyEditor() {
        require(roles[msg.sender] == Role.Editor || roles[msg.sender] == Role.Admin, "Only editor");
        _;
    }
    modifier onlyAuthor() {
        require(roles[msg.sender] == Role.Author || roles[msg.sender] == Role.Admin, "Only author");
        _;
    }
    modifier onlyReviewer() {
        require(roles[msg.sender] == Role.Reviewer || roles[msg.sender] == Role.Admin, "Only reviewer");
        _;
    }
    modifier paperExists(uint256 paperId) {
        require(papers[paperId].submittedAt != 0, "Paper does not exist");
        _;
    }
    modifier notFinalized(uint256 paperId) {
        require(!papers[paperId].finalized, "Paper is finalized — no changes permitted");
        _;
    }

    // ─── Constructor ─────────────────────────────────────────────────────────

    constructor() {
        admin = msg.sender;
        roles[msg.sender] = Role.Admin;
        emit RoleGranted(msg.sender, Role.Admin, block.timestamp);
    }

    // ─── Admin Functions ──────────────────────────────────────────────────────

    /**
     * @notice Register an account with a specific role.
     * @param account  Wallet address to register.
     * @param role     Role to assign (Author=1, Reviewer=2, Editor=3).
     * @param salt     For reviewers: secret salt used to derive anonymous ID hash.
     */
    function registerAccount(address account, Role role, bytes32 salt) external onlyAdmin {
        require(role != Role.None && role != Role.Admin, "Invalid role");
        roles[account] = role;
        if (role == Role.Reviewer) {
            _reviewerSalts[account] = salt;
        }
        emit RoleGranted(account, role, block.timestamp);
    }

    // ─── Author Functions ─────────────────────────────────────────────────────

    /**
     * @notice Submit a new manuscript (version 1).
     * @param paperHash  keccak256 hash of the manuscript file/content.
     */
    function submitPaper(bytes32 paperHash) external onlyAuthor returns (uint256 paperId) {
        _paperCounter++;
        paperId = _paperCounter;

        papers[paperId] = Paper({
            paperHash:      paperHash,
            author:         msg.sender,
            submittedAt:    block.timestamp,
            status:         PaperStatus.Submitted,
            versionCount:   1,
            originalPaperId: 0,
            finalized:      false
        });

        emit PaperSubmitted(paperId, paperHash, msg.sender, 1, block.timestamp);
    }

    /**
     * @notice Submit a revised manuscript linked to the original paper.
     * @param originalPaperId  The paperId of the first (or previous) version.
     * @param newPaperHash     keccak256 hash of the revised manuscript.
     */
    function submitRevision(uint256 originalPaperId, bytes32 newPaperHash)
        external
        onlyAuthor
        paperExists(originalPaperId)
    {
        Paper storage original = papers[originalPaperId];
        require(original.author == msg.sender, "Not your paper");
        require(
            original.status == PaperStatus.Revised ||
            original.status == PaperStatus.Submitted ||
            original.status == PaperStatus.UnderReview,
            "Revision not allowed at this stage"
        );
        require(!original.finalized, "Original paper is finalized");

        _paperCounter++;
        uint256 newPaperId = _paperCounter;

        // Root always points to v1
        uint256 root = (original.originalPaperId == 0) ? originalPaperId : original.originalPaperId;

        papers[newPaperId] = Paper({
            paperHash:      newPaperHash,
            author:         msg.sender,
            submittedAt:    block.timestamp,
            status:         PaperStatus.Revised,
            versionCount:   original.versionCount + 1,
            originalPaperId: root,
            finalized:      false
        });

        emit RevisionSubmitted(newPaperId, root, newPaperHash, block.timestamp);
        emit PaperSubmitted(newPaperId, newPaperHash, msg.sender, original.versionCount + 1, block.timestamp);
    }

    // ─── Editor Functions ─────────────────────────────────────────────────────

    /**
     * @notice Assign a reviewer to a paper using their anonymous ID hash.
     * @dev    The editor supplies the reviewer wallet; the contract derives the hash.
     * @param paperId          Target paper.
     * @param reviewerWallet   Reviewer's wallet address (not stored on-chain).
     */
    function assignReviewer(uint256 paperId, address reviewerWallet)
        external
        onlyEditor
        paperExists(paperId)
        notFinalized(paperId)
    {
        require(roles[reviewerWallet] == Role.Reviewer, "Not a registered reviewer");
        require(_reviewerSalts[reviewerWallet] != bytes32(0), "Reviewer salt not set");

        bytes32 reviewerIdHash = keccak256(abi.encodePacked(reviewerWallet, _reviewerSalts[reviewerWallet]));
        require(!_assignedReviewer[paperId][reviewerIdHash], "Reviewer already assigned");

        _assignedReviewer[paperId][reviewerIdHash] = true;
        _assignments[paperId].push(ReviewAssignment({
            reviewerIdHash: reviewerIdHash,
            assignedAt:     block.timestamp,
            completed:      false
        }));

        papers[paperId].status = PaperStatus.UnderReview;
        emit ReviewerAssigned(paperId, reviewerIdHash, block.timestamp);
    }

    /**
     * @notice Record a final editorial decision. Permanently locks the paper.
     * @param paperId   Target paper.
     * @param outcome   "Accepted" | "Rejected" | "Revision Required"
     */
    function recordDecision(uint256 paperId, string calldata outcome)
        external
        onlyEditor
        paperExists(paperId)
        notFinalized(paperId)
    {
        require(bytes(outcome).length > 0, "Outcome cannot be empty");

        bool validOutcome = (
            keccak256(bytes(outcome)) == keccak256(bytes("Accepted")) ||
            keccak256(bytes(outcome)) == keccak256(bytes("Rejected")) ||
            keccak256(bytes(outcome)) == keccak256(bytes("Revision Required"))
        );
        require(validOutcome, "Invalid outcome value");

        _decisions[paperId] = Decision({
            outcome:    outcome,
            editor:     msg.sender,
            decidedAt:  block.timestamp
        });

        if (keccak256(bytes(outcome)) == keccak256(bytes("Accepted"))) {
            papers[paperId].status = PaperStatus.Accepted;
        } else if (keccak256(bytes(outcome)) == keccak256(bytes("Rejected"))) {
            papers[paperId].status = PaperStatus.Rejected;
        } else {
            papers[paperId].status = PaperStatus.Revised;
        }

        // Lock the paper — no further score or decision changes are permitted
        papers[paperId].finalized = true;

        emit DecisionRecorded(paperId, outcome, msg.sender, block.timestamp);
    }

    // ─── Reviewer Functions ───────────────────────────────────────────────────

    /**
     * @notice Submit a review score for an assigned paper.
     * @dev    Only reviewers assigned to this paper may call this.
     * @param paperId        Target paper.
     * @param score          Numerical score 1–10.
     * @param recommendation "Accept" | "Minor Revision" | "Major Revision" | "Reject"
     */
    function submitScore(uint256 paperId, uint8 score, string calldata recommendation)
        external
        onlyReviewer
        paperExists(paperId)
        notFinalized(paperId)
    {
        require(score >= 1 && score <= 10, "Score must be 1–10");
        require(bytes(recommendation).length > 0, "Recommendation required");

        bytes32 salt = _reviewerSalts[msg.sender];
        require(salt != bytes32(0), "Reviewer salt not set");

        bytes32 reviewerIdHash = keccak256(abi.encodePacked(msg.sender, salt));
        require(_assignedReviewer[paperId][reviewerIdHash], "Not assigned to this paper");

        // Check not already scored
        ReviewScore[] storage scores = _scores[paperId];
        for (uint256 i = 0; i < scores.length; i++) {
            require(scores[i].reviewerIdHash != reviewerIdHash, "Score already submitted");
        }

        _scores[paperId].push(ReviewScore({
            reviewerIdHash: reviewerIdHash,
            score:          score,
            recommendation: recommendation,
            submittedAt:    block.timestamp
        }));

        // Mark assignment as completed
        ReviewAssignment[] storage assignments = _assignments[paperId];
        for (uint256 i = 0; i < assignments.length; i++) {
            if (assignments[i].reviewerIdHash == reviewerIdHash) {
                assignments[i].completed = true;
                break;
            }
        }

        emit ScoreSubmitted(paperId, reviewerIdHash, score, recommendation, block.timestamp);
    }

    // ─── View Functions ───────────────────────────────────────────────────────

    function getPaper(uint256 paperId) external view paperExists(paperId)
        returns (
            bytes32 paperHash,
            address author,
            uint256 submittedAt,
            PaperStatus status,
            uint8 versionCount,
            uint256 originalPaperId,
            bool finalized
        )
    {
        Paper storage p = papers[paperId];
        return (p.paperHash, p.author, p.submittedAt, p.status, p.versionCount, p.originalPaperId, p.finalized);
    }

    function getAssignments(uint256 paperId) external view paperExists(paperId)
        returns (ReviewAssignment[] memory)
    {
        return _assignments[paperId];
    }

    function getScores(uint256 paperId) external view paperExists(paperId)
        returns (ReviewScore[] memory)
    {
        return _scores[paperId];
    }

    function getDecision(uint256 paperId) external view paperExists(paperId)
        returns (string memory outcome, address editor, uint256 decidedAt)
    {
        Decision storage d = _decisions[paperId];
        return (d.outcome, d.editor, d.decidedAt);
    }

    function getPaperCount() external view returns (uint256) {
        return _paperCounter;
    }

    /**
     * @notice Derive the anonymous reviewer ID hash for a given wallet.
     *         Useful for editors to verify an assignment off-chain.
     */
    function getReviewerIdHash(address reviewerWallet) external view onlyAdmin returns (bytes32) {
        bytes32 salt = _reviewerSalts[reviewerWallet];
        require(salt != bytes32(0), "Reviewer not registered");
        return keccak256(abi.encodePacked(reviewerWallet, salt));
    }
}
