# Blockchain-Based Academic Peer Review System

 A decentralised application (DApp) that brings **transparency**, **immutability**, and **accountability** to academic peer review powered by Ethereum smart contracts, IPFS, and a Node.js + Streamlit full-stack architecture.

---

## Overview

Traditional academic peer review is plagued by opacity, bias, and the absence of tamper-proof audit trails. This project reimagines the process by anchoring every critical workflow event - paper submission, reviewer assignment, review score, and editorial decision as an immutable, publicly verifiable on-chain transaction.

No single party can alter historical records. Every stakeholder can independently verify the integrity of the process.

---

## Table of Contents

- [Features](#-features)
- [System Architecture](#-system-architecture)
- [Technology Stack](#-technology-stack)
- [Smart Contract Design](#-smart-contract-design)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Setup](#environment-setup)
  - [Running the Application](#running-the-application)
- [API Reference](#-api-reference)
- [Role-Based Workflow](#-role-based-workflow)
- [Security](#-security)
- [Testing](#-testing)
- [Known Limitations](#-known-limitations)
- [Future Work](#-future-work)
- [Team](#-team)

---

## Features

| Feature | Description |
|---|---|
|  On-chain audit trail | Every submission, assignment, review, and decision is recorded as an immutable blockchain transaction |
|  Role-based access control | Authors, Reviewers, Editors, and Admins — enforced at the smart contract level |
|  IPFS document storage | Paper PDFs are stored on IPFS; only their keccak256 hash is anchored on-chain |
|  Pseudonymous review | Reviewers are identified by an anonymous hash — wallet addresses are never exposed |
|  Terminal-state immutability | Once a paper is Accepted or Rejected, no further state changes are possible — by anyone |
|  Revision history | Each revision is cryptographically linked to the original submission, forming an auditable chain |
|  Role-specific dashboards | Streamlit UI renders tailored interfaces for Authors, Reviewers, Editors, and Admins |
|  Transaction hash transparency | Every on-chain action surfaces its txHash so users can independently verify it on a block explorer |

---

##  System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        Streamlit Frontend                        │
│       Author Dashboard │ Reviewer Dashboard │ Editor Dashboard   │
└─────────────────────────────┬────────────────────────────────────┘
                              │ HTTP (REST)
┌─────────────────────────────▼────────────────────────────────────┐
│                   Node.js / Express API                          │
│   JWT Auth │ Helmet Security │ CORS │ Morgan Logging             │
│                                                                  │
│   ┌────────────────────┐   ┌───────────────────────────────┐     │
│   │ MongoDB (off-chain)│   │     ethers.js (on-chain)      │     │
│   │  Paper metadata    │   │   sonRpcProvider + Wallet     │     │
│   │  User profiles     │   │  PeerReviewSystem Contract    │     │
│   │  Review comments   │   └──────────────┬────────────────┘     │
│   └────────────────────┘                  │                      │
└───────────────────────────────────────────┼──────────────────────┘
                                            │ EVM Transactions
┌───────────────────────────────────────────▼───────────────────────┐
│              Ethereum-Compatible Blockchain (EVM)                 │
│         Hardhat / Ganache (dev) │ Sepolia / Mumbai (staging)      │
│                PeerReviewSystem.sol                               │
└───────────────────────────────────────────────────────────────────┘
                     │
         ┌───────────▼───────────┐
         │  IPFS (Document Store)│
         │ Content-addressed PDFs│
         └───────────────────────┘
```

**Hybrid Storage Strategy:**
- **On-chain:** Document hashes, reviewer hashes, scores, statuses, decisions — immutable and publicly verifiable
- **Off-chain (MongoDB):** Paper titles, abstracts, review comments, user metadata — flexible and queryable
- **IPFS:** Full paper PDFs decentralised, content-addressed, version-locked

---

##  Technology Stack

| Layer | Technology | Version |
|---|---|---|
| Smart Contract | Solidity | ^0.8.x |
| Blockchain Interaction | ethers.js | v6.16.0 |
| Backend Framework | Node.js + Express | v4.18.2 |
| Database (Off-chain) | MongoDB + Mongoose | v7.5.0 |
| Security Middleware | Helmet + CORS | v7.0.0 |
| Logging | Morgan | v1.10.0 |
| Document Storage | IPFS | CID-based |
| Frontend UI | Streamlit (Python) | Latest |
| Environment Config | dotenv | v16.3.1 |
| Dev Server | nodemon | v3.0.1 |
| Dev Blockchain | Hardhat / Ganache | — |

---

##  Smart Contract Design

The `PeerReviewSystem` Solidity contract is the backbone of the system. It enforces all state transitions and stores document hashes immutably.

### Data Structures

```solidity
enum Role       { Author, Reviewer, Editor, Admin }
enum PaperStatus { Submitted, UnderReview, Reviewed, Accepted, Rejected, RevisionRequired }
enum Decision   { Pending, Accepted, Rejected, RevisionRequired }

struct PaperRecord {
    bytes32 originalHash;   // keccak256 of IPFS CID
    address author;         // Submitting wallet
    PaperStatus status;     // Current lifecycle stage
    Decision finalDecision; // Editor's final verdict
}
```

### Core Functions

| Function | Access | On-Chain Effect |
|---|---|---|
| `registerUser(wallet, role, reviewerHash)` | Admin only | Maps wallet to role; stores reviewer identity hash |
| `submitPaper(documentHash)` | Author | Creates PaperRecord; status → Submitted |
| `assignReviewer(paperHash, reviewerHash)` | Admin / Editor | Links reviewer to paper; status → UnderReview |
| `submitReview(paperHash, score)` | Assigned Reviewer | Records score (0–10); status → Reviewed |
| `finalizeDecision(paperHash, decision)` | Admin / Editor | Records verdict; enforces terminal immutability |
| `submitRevision(originalHash, newHash)` | Original Author | Appends revision hash; status → Submitted |
| `getPaperRevisions(paperHash)` | Public (view) | Returns chronological revision hash array |
| `getReviewScore(paperHash, reviewerHash)` | Public (view) | Returns numeric score |

### Paper Lifecycle State Machine

```
          [Author submits]
               │
           Submitted
               │
     [Editor assigns reviewer]
               │
          UnderReview
               │
      [Reviewer submits score]
               │
            Reviewed
               │
     [Editor finalizes decision]
          ┌────┴────┐
       Accepted   Rejected   RevisionRequired
     (terminal) (terminal)        │
                          [Author submits revision]
                                  │
                              Submitted ──► (cycle repeats)
```

---

##  Project Structure

```
peer-review-backend/
├── src/
│   ├── app.js                  # Express app setup (middleware, routes)
│   ├── server.js               # Entry point
│   ├── config/
│   │   ├── web3.js             # ethers.js provider, wallet, contract instance
│   │   ├── db.js               # MongoDB connection
│   │   └── abi.json            # Deployed contract ABI
│   ├── controllers/
│   │   ├── paperController.js  # All paper-related logic (submit, assign, review, decide, revise)
│   │   └── userController.js   # User registration and JWT authentication
│   ├── models/
│   │   ├── Paper.js            # Mongoose Paper schema
│   │   └── User.js             # Mongoose User schema
│   ├── routes/
│   │   ├── paperRoutes.js      # /api/papers/* route definitions
│   │   └── userRoutes.js       # /api/users/* route definitions
│   └── middlewares/
│       └── authMiddleware.js   # JWT verification middleware
├── frontend/
│   └── app.py                  # Streamlit UI (all role dashboards)
├── contracts/
│   └── PeerReviewSystem.sol    # Solidity smart contract
├── scripts/
│   └── deploy.js               # Hardhat deployment script
├── .env                        # Environment variables (never commit this)
├── .env.example                # Template for environment setup
├── hardhat.config.js           # Hardhat configuration
└── package.json
```

---

##  Getting Started

### Prerequisites

Make sure you have the following installed:

- [Node.js](https://nodejs.org/) >= 18.x
- [Python](https://www.python.org/) >= 3.9
- [MongoDB](https://www.mongodb.com/) (local or Atlas)
- [Hardhat](https://hardhat.org/) or [Ganache](https://trufflesuite.com/ganache/)
- [IPFS Desktop](https://docs.ipfs.tech/install/ipfs-desktop/) or access to a pinning service (Pinata / Infura)
- [MetaMask](https://metamask.io/) (for interacting with the UI on a testnet)

### Installation

**1. Clone the repository**

```bash
git clone https://github.com/apharnakamath/blockchain-based-academic-peer-review-system.git
cd blockchain-based-academic-peer-review-system
```

**2. Install backend dependencies**

```bash
npm install
```

**3. Install Streamlit frontend dependencies**

```bash
pip install streamlit requests
```

**4. Install Hardhat (if not already installed)**

```bash
npm install --save-dev hardhat
```

### Environment Setup

Copy the example environment file and fill in your values:

```bash
cp .env.example .env
```

```env
# .env

# Blockchain
RPC_URL=http://127.0.0.1:8545         # Local Hardhat node (or testnet RPC URL)
PRIVATE_KEY=0x<your_admin_private_key> # Admin wallet private key — keep this secret!
CONTRACT_ADDRESS=0x<deployed_address>  # Set after deploying the contract

# Database
MONGODB_URI=mongodb://localhost/peer-review-db

# Auth
JWT_SECRET=your_jwt_secret_here
```

>  **Never commit your `.env` file.** It is already listed in `.gitignore`.

### Running the Application

**Step 1: Start a local Ethereum node**

```bash
npx hardhat node
```

This starts a local Hardhat network at `http://127.0.0.1:8545` with pre-funded test accounts.

**Step 2: Compile and deploy the smart contract**

```bash
npx hardhat compile
npx hardhat run scripts/deploy.js --network localhost
```

Copy the printed contract address into your `.env` file as `CONTRACT_ADDRESS`. Copy the generated ABI to `src/config/abi.json`.

**Step 3: Start MongoDB**

```bash
mongod
```

Or use your MongoDB Atlas connection string in `.env`.

**Step 4: Start the backend API**

```bash
npm run dev       # Development (nodemon hot-reload)
# or
npm start         # Production
```

The API will be available at `http://localhost:3000`.

**Step 5: Register the initial admin user**

The very first admin must be bootstrapped via a direct API call (only the admin can register others):

```bash
curl -X POST http://localhost:3000/api/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "walletAddress": "0x<your_admin_wallet>",
    "name": "Admin Name",
    "email": "admin@example.com",
    "role": "Admin"
  }'
```

**Step 6: Start the Streamlit frontend**

```bash
cd frontend
streamlit run app.py
```

The UI will open at `http://localhost:8501`.

---

##  API Reference

### Paper Endpoints (`/api/papers`)

| Method | Endpoint | Description | Access |
|---|---|---|---|
| `POST` | `/submit` | Submit a new paper (triggers `submitPaper` on-chain) | Author |
| `GET` | `/all` | Retrieve all papers from MongoDB | Any |
| `GET` | `/:paperHash` | Get paper details with on-chain state | Any |
| `GET` | `/author/:wallet` | Get all papers by a specific author | Any |
| `GET` | `/reviewer/:wallet` | Get all papers assigned to a reviewer | Any |
| `POST` | `/assign` | Assign a reviewer to a paper (on-chain) | Editor / Admin |
| `POST` | `/review` | Submit a review score (on-chain) | Assigned Reviewer |
| `POST` | `/decide` | Finalize editorial decision (on-chain) | Editor / Admin |
| `POST` | `/revise` | Submit a manuscript revision (on-chain) | Original Author |
| `GET` | `/:hash/revisions` | Get the full revision history for a paper | Any |

### User Endpoints (`/api/users`)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/register` | Register a user in MongoDB and on-chain |
| `POST` | `/login` | Authenticate user and receive a JWT |
| `GET` | `/reviewers` | List all registered reviewers |

### Example: Submit a Paper

```bash
curl -X POST http://localhost:3000/api/papers/submit \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <jwt_token>" \
  -d '{
    "title": "Federated Learning in Healthcare",
    "abstract": "This paper explores...",
    "ipfsCid": "QmExampleCID123",
    "walletAddress": "0x<author_wallet>"
  }'
```

**Response:**
```json
{
  "message": "Paper submitted successfully",
  "paperHash": "0x...",
  "txHash": "0x..."
}
```

---

##  Role-Based Workflow

### Admin
- Registers all users (authors, reviewers, editors) on-chain
- Can look up any paper by hash
- Manages the system via the Admin Dashboard

### Author
1. Upload paper PDF to IPFS and get the CID
2. Submit the paper via the Author Dashboard (title, abstract, IPFS CID)
3. Track the paper status (Submitted → Under Review → Reviewed)
4. If "Revision Required" — upload a revised PDF to IPFS and submit the new CID
5. Each revision creates a new hash cryptographically linked to the original on-chain

### Reviewer
1. Log in with your registered wallet address
2. View papers assigned to you in the Reviewer Dashboard
3. Submit a score (0–10) and optional comments
4. Your identity is protected — only your anonymous hash is recorded on-chain, never your wallet address

### Editor
1. View all submitted papers with filter-by-status support
2. Assign a registered reviewer to any submitted paper (triggers on-chain status change)
3. After a review score is submitted, finalize the decision: **Accept**, **Reject**, or **Request Revision**
4. Terminal decisions (Accept/Reject) are permanently immutable — no wallet can change them afterward

---

##  Security

### Smart Contract Security

| Threat | Mitigation |
|---|---|
| Unauthorised state changes | `onlyAdmin`, `onlyEditor`, `onlyAssignedReviewer` modifiers; violations revert transactions |
| Double-decision attacks | Terminal state check in `finalizeDecision()` blocks any post-decision changes |
| Hash collision | `keccak256` with 2²⁵⁶ collision resistance |
| Reentrancy | No ETH holdings, no external contract calls; reentrancy not applicable |
| Integer overflow | Solidity ^0.8.x has built-in overflow protection; `uint8` enforces score range |
| Replay attacks | Ethereum transaction nonces make each transaction unique |

### API & Off-Chain Security

- **Helmet Middleware** — sets X-Frame-Options, X-XSS-Protection, Content-Security-Policy, and HSTS headers
- **CORS** — cross-origin requests restricted to whitelisted origins
- **Input Validation** — all endpoints validate required fields before touching the blockchain
- **JWT Authentication** — sensitive endpoints require a valid JWT issued on login
- **Private Key Management** — admin key stored in `.env`; never exposed in logs or API responses

>  **For production:** Replace `.env`-based key storage with a dedicated KMS (AWS KMS, HashiCorp Vault, or a hardware wallet / multi-sig setup).

---

##  Testing

### Smart Contract Tests

Run the Hardhat test suite:

```bash
npx hardhat test
```

Key scenarios covered:

| Test Case | Expected Result |
|---|---|
| Register Author | `userRoles[wallet] = Author` |
| Submit Paper | `PaperRecord` created, `status = Submitted` |
| Assign Reviewer | `assignedReviewers` updated, `status = UnderReview` |
| Submit Review (wrong reviewer) | Transaction reverts |
| Submit Review (valid, score = 8) | Score stored on-chain, `status = Reviewed` |
| Finalize Decision (Accept) | `finalDecision = Accepted`, state immutable |
| Submit Review after Accept | Transaction reverts (terminal state) |
| Submit Revision | New hash appended, `status = Submitted` |
| Get Revisions | Returns array of revision hashes |

### API Tests

Use the Postman collection or `curl` to test all endpoints. Key validations:

- Missing required fields → `400` with descriptive error
- Non-existent reviewer assignment → `404`
- Wrong reviewer submitting review → `403 Forbidden`
- Score out of range (0–10) → `400`
- Modifying a terminal-state paper → `400 "immutable record"`

### End-to-End Workflow

```
Register Admin, Author, Reviewer, Editor
    ↓
Author uploads PDF to IPFS → gets CID
    ↓
Author submits paper via API
    ↓
Editor assigns reviewer (on-chain: UnderReview)
    ↓
Reviewer submits score (on-chain: Reviewed)
    ↓
Editor finalizes decision (on-chain: Accepted / Rejected / RevisionRequired)
    ↓
Verify immutability — attempt second review → contract reverts ✓
    ↓
Query GET /api/papers/:hash → full on-chain audit trail ✓
```

### Performance

| Operation | Latency |
|---|---|
| Local Hardhat tx confirmation | < 1 second |
| Public Ethereum testnet tx | 12–15 seconds (avg) |
| MongoDB metadata queries | 5–20 ms |

---

##  Known Limitations

- **Single admin key** — all transactions are signed by one wallet. A multi-signature wallet is recommended for production deployments.
- **Off-chain/on-chain binding** — MongoDB metadata is not cryptographically linked to on-chain hashes in the current implementation. A Merkle root or signed commitment would strengthen this.
- **IPFS availability** — content addressing guarantees integrity but not availability. Use pinning services (Pinata, Infura IPFS) in production.
- **Gas costs** — deployment on Ethereum mainnet may incur significant gas fees; consider Layer 2 networks.

---

##  Future Work

- **Layer 2 deployment** — migrate to Polygon zkEVM or Arbitrum to reduce gas costs
- **zk-proof reviewer anonymity** — use zero-knowledge proofs to cryptographically prove reviewer credentials without exposing identity
- **IPFS pinning integration** — integrate Pinata or Infura IPFS for guaranteed document persistence
- **Multi-sig admin governance** — replace single admin key with a Gnosis Safe or DAO-style governance for editorial decisions
- **Merkle-anchored off-chain data** — cryptographically bind MongoDB records to on-chain state via Merkle roots

---

