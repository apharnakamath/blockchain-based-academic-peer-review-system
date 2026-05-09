# 📚 Blockchain Academic Peer Review System

A transparent, tamper-proof academic peer review system built on a blockchain ledger with IPFS document storage and MongoDB metadata caching.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Frontend                        │
│          (Role-based: Admin / Author / Reviewer / Editor)   │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP REST API
┌────────────────────────▼────────────────────────────────────┐
│               Node.js + Express Backend                      │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────────┐  │
│  │  paperRoutes │  │  userRoutes   │  │   auth middleware│  │
│  └──────┬───────┘  └──────┬────────┘  └──────────────────┘  │
│         │                 │                                   │
│  ┌──────▼───────┐  ┌──────▼────────┐                         │
│  │paperController│  │userController │                         │
│  └──────┬───────┘  └──────┬────────┘                         │
└─────────┼─────────────────┼──────────────────────────────────┘
          │                 │
   ┌──────▼──────┐   ┌──────▼──────┐   ┌───────────────┐
   │  Blockchain  │   │   MongoDB   │   │   IPFS/Pinata │
   │  (PoA Net)   │   │ (Metadata)  │   │  (PDF Storage)│
   └─────────────┘   └─────────────┘   └───────────────┘
```

## Consensus Algorithm: Proof of Authority (PoA — Clique)

**Choice:** Clique PoA (as used in Ethereum Goerli, private networks via Geth/Besu)

**Justification:**
- **Permissioned network:** Academic institutions are known entities — PoA is appropriate because validators are pre-approved, aligning with the trust model.
- **Low latency:** Block finality in seconds (vs. minutes for PoW), critical for interactive review workflows.
- **No mining waste:** Zero computational overhead, suitable for institutional deployment budgets.
- **Deterministic finality:** Once a block is sealed, it cannot be reorganized — ideal for immutable record-keeping.
- **Sybil resistance:** Validators must be whitelisted, preventing anonymous actors from corrupting the ledger.

---

## Directory Structure

```
peer-review-system/
├── backend/
│   ├── config/
│   │   ├── abi.json          ← Smart contract ABI
│   │   ├── db.js             ← MongoDB connection
│   │   └── web3.js           ← Ethers.js provider + contract
│   ├── controllers/
│   │   ├── paperController.js ← All paper logic
│   │   └── userController.js  ← User registration & lookup
│   ├── middlewares/
│   │   └── auth.js            ← Wallet signature verification
│   ├── models/
│   │   ├── Paper.js           ← Mongoose schema (with reviews, revisions)
│   │   └── User.js            ← Mongoose user schema
│   ├── routes/
│   │   ├── paperRoutes.js
│   │   └── userRoutes.js
│   ├── services/
│   │   ├── contract.js        ← Blockchain interaction helpers
│   │   └── ipfs.js            ← Pinata upload helper
│   ├── app.js
│   ├── server.js
│   ├── package.json
│   └── .env.example
└── frontend/
    ├── app.py                 ← Streamlit multi-role dashboard
    └── requirements.txt
```

---

## API Endpoints

### Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/users/register` | Register user on-chain + DB |
| GET | `/api/users/:address` | Get user profile |
| GET | `/api/users/all` | List all registered users |
| GET | `/api/users/reviewers` | List all reviewers |

### Papers
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/papers/submit` | Submit new paper (on-chain + DB) |
| GET | `/api/papers/` | Get all papers |
| GET | `/api/papers/:paperHash` | Get paper details |
| POST | `/api/papers/assign` | Assign reviewer (on-chain + DB) |
| POST | `/api/papers/review` | Submit review score (on-chain + DB) |
| POST | `/api/papers/decision` | Finalize editorial decision |
| POST | `/api/papers/revise` | Submit revised manuscript |
| GET | `/api/papers/author/:wallet` | Get papers by author |
| GET | `/api/papers/assigned/:wallet` | Get papers assigned to reviewer |
| GET | `/api/papers/revisions/:hash` | Get revision chain |

---

## Setup & Running

### 1. Backend

```bash
cd backend
cp .env.example .env
# Edit .env with your values
npm install
npm start
```

### 2. Frontend

```bash
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

The Streamlit app connects to `http://localhost:3000` by default. Change `API_BASE` at the top of `app.py` if needed.

---

## Role-Based Workflow

```
Admin
  └─→ registers Author, Reviewer (with anonymous hash), Editor wallets on-chain

Author
  └─→ submits paper (IPFS CID → hash stored on-chain)
  └─→ tracks review status
  └─→ submits revision (if editor requests one)

Editor
  └─→ views all papers
  └─→ assigns reviewer (reviewer hash recorded, not wallet)
  └─→ finalizes decision (irreversible on-chain transaction)

Reviewer
  └─→ sees only assigned papers
  └─→ submits score (0–10) + comments
  └─→ score recorded against anonymous hash, not wallet
```

---

## Key Security Properties

- **Immutability:** Once a decision is finalized, the contract rejects any further state changes.
- **Reviewer anonymity:** Only `keccak256(reviewerId)` is stored on-chain — never the wallet.
- **Role enforcement:** Smart contract checks caller role before accepting any transaction.
- **Revision chain:** Each revision generates a new hash linked to the original, creating a verifiable history.
- **Off-chain metadata:** Titles and abstracts stored in MongoDB; only hashes go on-chain, preserving privacy.
