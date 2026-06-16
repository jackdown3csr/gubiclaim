# Galactica Token Tools: Claim and Burn gUBI

Python scripts for managing **gUBI tokens** on the [Galactica](https://galactica.com) network.

These tools do the same thing as the [Galactica webapp](https://app.galactica.com) — but from your command line, which is useful when MetaMask blocks transactions due to its Blockaid security scanner.

| Script | What it does |
|---|---|
| `claim_gubi.py` | Claim your monthly gUBI rewards (veGNET holders) |
| `burn_gubi.py` | Burn gUBI to redeem proportional WGNET + ARCHAI from the IndexPool |

---

## Security

**Your private key is:**
- Entered via a hidden input prompt (characters are not visible when you type)
- Used only locally to sign transactions on your own machine
- Never stored anywhere on disk
- Never sent to any server

Both scripts are short, unobfuscated Python — you can read every line before running them.

**Contract addresses (fully verifiable on the explorer):**

| Contract | Address |
|---|---|
| gUBI token | [`0xFEa4F549eFB1F8B2cBA8d029e6845Ee431e142AA`](https://explorer.galactica.com/address/0xFEa4F549eFB1F8B2cBA8d029e6845Ee431e142AA) |
| gUBI Reward Distributor (proxy) | [`0x07297E1aA709C85e81c1a9498080AE010bE91D80`](https://explorer.galactica.com/address/0x07297E1aA709C85e81c1a9498080AE010bE91D80) |
| IndexPool vault (burn target) | [`0x50AF2AAb1455C1C06B3b8e623549dDE437F54EeF`](https://explorer.galactica.com/address/0x50AF2AAb1455C1C06B3b8e623549dDE437F54EeF) |
| WGNET | [`0x690F1eEf8AcEaD09Ac695d9111Af081045c6d5b7`](https://explorer.galactica.com/address/0x690F1eEf8AcEaD09Ac695d9111Af081045c6d5b7) |
| ARCHAI | [`0x22b48a764d2aAAe14d751aD2B5fcdf6C0A4d95D7`](https://explorer.galactica.com/address/0x22b48a764d2aAAe14d751aD2B5fcdf6C0A4d95D7) |

---

## Requirements

- Python 3.9 or newer
- Internet connection

Both scripts will automatically offer to install missing Python packages on first run.

If you prefer to install manually:

```
pip install web3 eth-account
```

(`claim_gubi.py` also needs `eth-abi requests`)

---

## claim_gubi.py

Claim your accumulated gUBI token rewards.

gUBI is distributed monthly to veGNET holders based on their SoulScore and voting power. Each claim covers all unclaimed epochs at once.

**How it works:**
1. Fetches your Merkle proof from the official Galactica API (`admin-panel.galactica.com`)
2. Reads your claim status from the on-chain contract
3. Verifies the proof matches the live on-chain Merkle root before doing anything
4. Runs a local simulation of the transaction to confirm it will succeed
5. Signs and broadcasts the `claimReward()` transaction

**Usage:**

```
python claim_gubi.py
```

**Example session:**

```
========================================================
   gUBI Claim Tool - Galactica Mainnet
========================================================

STEP 1: Enter your wallet address
  Wallet address: 0xYOUR_ADDRESS

STEP 2: Checking your rewards...
  --------------------------------------------------------
  Wallet address:   0xYOUR_ADDRESS
  Current epoch:    81
  Last claimed:     epoch 80
  Already claimed:  162,000.0000 gUBI
  Total entitled:   163,185.0000 gUBI
  Claimable now:    1,185.0000 gUBI
  --------------------------------------------------------

STEP 3: Claim 1,185.0000 gUBI?  (y/n): y

STEP 4: Sign the transaction with your private key
  Private key (hidden): ********************************

STEP 5: Sending transaction...
  Simulation passed. Estimated gas fee: 0.00000775 GNET
  Broadcasting transaction to the network...

========================================================
  SUCCESS!
  Claimed 1,185.0000 gUBI to your wallet.

  Transaction ID:
  0xabc123...

  View on explorer:
  https://explorer.galactica.com/tx/0xabc123...
========================================================
```

**Troubleshooting:**

- **"This address has no gUBI rewards to claim"** — Your address is not in the current distribution. Make sure you have veGNET locked and a valid SoulScore.
- **"The reward data is being updated on-chain right now"** — A new epoch was just published. Wait a few minutes and try again.
- **"Transaction simulation failed"** — The Merkle root was likely updated between the API fetch and the simulation. Run the script again.
- **Script exits with an error about missing modules** — Run `pip install web3 eth-abi eth-account requests` manually and try again.

---

## burn_gubi.py

Burn gUBI tokens to redeem your proportional share of WGNET + ARCHAI from the IndexPool vault.

The IndexPool holds a basket of WGNET and ARCHAI. When you burn gUBI, you receive back a share proportional to the fraction of the total gUBI supply you are burning.

**How it works:**
1. Fetches live pool balances and your gUBI balance from the chain
2. Shows an estimate of how much WGNET + ARCHAI you will receive
3. Asks for confirmation before doing anything
4. Approves the IndexPool to spend your gUBI (only if needed, separate TX)
5. Calls `burnIndexToken()` to execute the burn
6. Both steps simulate locally before broadcasting

**Usage:**

```
python burn_gubi.py
```

**Example session:**

```
========================================================
   gUBI Burn Tool - Galactica Mainnet
========================================================

STEP 1: Enter your wallet address
  Wallet address: 0xYOUR_ADDRESS

STEP 2: Checking balances...
  --------------------------------------------------------
  Wallet address:   0xYOUR_ADDRESS
  gUBI balance:     18,201.0000 gUBI
  IndexPool holds:  9,850,432.1234 WGNET
                    1,999,018.5678 ARCHAI
  --------------------------------------------------------

STEP 3: Enter amount to burn
  Enter a number or type "all" to burn your full balance
  (18,201.0000 gUBI)

  Amount to burn: 10000

  --------------------------------------------------------
  Burn:             10,000.0000 gUBI
  Share of supply:  0.0192%

  Estimated payout (proportional):
    WGNET:          ~1,891.2830 WGNET
    ARCHAI:         ~384.0516 ARCHAI
  --------------------------------------------------------

  Do you want to proceed with the burn? (y/n): y

STEP 4: Sign the transaction with your private key
  Private key (hidden): ********************************

STEP 5/6: Approving gUBI spend...
  Approval TX: 0xdef789...
  Approved successfully.

STEP 6/6: Burning gUBI...
  Simulation passed. Estimated gas fee: 0.00001240 GNET
  Broadcasting transaction to the network...

  Waiting for confirmation...

========================================================
SUCCESS!
  Burned 10,000.0000 gUBI.
  WGNET and ARCHAI have been sent to your wallet.

  Transaction ID:
  0xabc456...

  View on explorer:
  https://explorer.galactica.com/tx/0xabc456...
========================================================
```

**Troubleshooting:**

- **"Transaction simulation failed"** — The pool state changed between the estimate and the burn. Run the script again.
- **Amount exceeds balance** — The script will warn you and ask again. Type `all` to burn your full balance.
- **Approval step fails** — Rare; retry the script. The approval is a separate transaction from the burn.

---

## Network info

- Chain: Galactica Mainnet (Chain ID: 613419)
- RPC: `https://galactica-mainnet.g.alchemy.com/public`
- Explorer: `https://explorer.galactica.com`
