# gUBI Claim Tool — Galactica Mainnet

A simple Python script to claim your **gUBI token rewards** on the [Galactica](https://galactica.com) network.

gUBI is distributed monthly to veGNET holders based on their SoulScore and voting power.
This script does the same thing as the [gUBI webapp](https://app.galactica.com) — but from your command line, which is useful if MetaMask blocks the transaction due to its security scanner.

---

## Is this safe to use?

Yes. Here is exactly what this script does:

1. Fetches your Merkle proof from the official Galactica API (`admin-panel.galactica.com`)
2. Reads your claim status from the on-chain contract
3. Verifies the proof matches the live on-chain Merkle root before doing anything
4. Runs a **local simulation** of the transaction to confirm it will succeed
5. Signs and broadcasts the `claimReward()` transaction

**Your private key is:**
- Entered via a hidden input prompt (characters are not visible when you type)
- Used only locally to sign the transaction
- Never stored anywhere on disk
- Never sent to any server

You can verify every line of the source code in `claim_gubi.py` — it is ~250 lines with no obfuscation.

**Contract addresses (fully verifiable on the explorer):**

| Contract | Address |
|---|---|
| gUBI Reward Distributor (proxy) | [`0x07297E1aA709C85e81c1a9498080AE010bE91D80`](https://explorer.galactica.com/address/0x07297E1aA709C85e81c1a9498080AE010bE91D80) |
| gUBI token | [`0xFEa4F549eFB1F8B2cBA8d029e6845Ee431e142AA`](https://explorer.galactica.com/address/0xFEa4F549eFB1F8B2cBA8d029e6845Ee431e142AA) |

---

## Requirements

- Python 3.9 or newer
- Internet connection

The script will automatically offer to install missing Python packages on first run.

If you prefer to install manually:

```
pip install web3 eth-abi eth-account requests
```

---

## How to use

1. Download `claim_gubi.py`
2. Open a terminal (Command Prompt or PowerShell on Windows)
3. Navigate to the folder where you saved the file
4. Run:

```
python claim_gubi.py
```

The script will guide you through each step interactively.

---

## Step-by-step walkthrough

```
========================================================
   gUBI Claim Tool — Galactica Mainnet
========================================================

STEP 1: Enter your wallet address
  Wallet address: 0xYOUR_ADDRESS

STEP 2: Checking your rewards...
  --------------------------------------------------
  Wallet address:   0xYOUR_ADDRESS
  Current epoch:    77
  Last claimed:     epoch 75
  Already claimed:  144,263.2718 gUBI
  Total entitled:   153,097.4709 gUBI
  Claimable now:    8,834.1991 gUBI
  --------------------------------------------------

STEP 3: Claim 8,834.1991 gUBI?  (y/n): y

STEP 4: Sign the transaction with your private key
  Private key (hidden): ********************************

STEP 5: Sending transaction...
  Simulation passed. Estimated gas fee: 0.00000775 GNET
  Broadcasting transaction to the network...

========================================================
  SUCCESS!
  Claimed 8,834.1991 gUBI to your wallet.

  Transaction ID:
  0xabc123...

  View on explorer:
  https://explorer.galactica.com/tx/0xabc123...
========================================================
```

---

## Troubleshooting

**"This address has no gUBI rewards to claim"**
Your address is not in the current gUBI distribution. Make sure you have veGNET locked and a valid SoulScore.

**"The reward data is being updated on-chain right now"**
A new epoch was just published. Wait a few minutes and try again.

**"Transaction simulation failed"**
The transaction would revert. Most likely cause: the Merkle root was updated between the API fetch and the simulation. Run the script again.

**Script exits with an error about missing modules**
Run `pip install web3 eth-abi eth-account requests` manually and try again.

---

## Network info

- Chain: Galactica Mainnet (Chain ID: 613419)
- RPC: `https://galactica-mainnet.g.alchemy.com/public`
- Explorer: `https://explorer.galactica.com`
