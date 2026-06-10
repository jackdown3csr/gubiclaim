"""
claim_gubi.py - Claim gUBI rewards on Galactica Mainnet

Just run:
    python claim_gubi.py

The script will install missing dependencies and guide you step by step.
"""

import subprocess
import sys


def ensure_dependencies():
    packages = ["web3", "eth-abi", "eth-account", "requests"]
    missing = []
    for pkg in packages:
        import_name = pkg.replace("-", "_").split("==")[0]
        # special cases
        if pkg == "eth-abi":
            import_name = "eth_abi"
        elif pkg == "eth-account":
            import_name = "eth_account"
        try:
            __import__(import_name)
        except ImportError:
            missing.append(pkg)

    if missing:
        print(f"Missing packages: {', '.join(missing)}")
        answer = input("Install them now? (y/n): ").strip().lower()
        if answer != "y":
            print("Cannot continue without dependencies. Exiting.")
            sys.exit(1)
        print("Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
        print("Done. Restarting script...\n")
        # Re-exec so imports work
        subprocess.check_call([sys.executable] + sys.argv)
        sys.exit(0)


ensure_dependencies()

import getpass  # noqa: E402
import requests  # noqa: E402
from eth_abi import encode  # noqa: E402
from eth_account import Account  # noqa: E402
from eth_utils import keccak  # noqa: E402
from web3 import Web3  # noqa: E402

RPC_URL = "https://galactica-mainnet.g.alchemy.com/public"
GUBI_DISTRIBUTOR = Web3.to_checksum_address("0x07297E1aA709C85e81c1a9498080AE010bE91D80")
CHAIN_ID = 613419

ABI = [
    {
        "inputs": [{"components": [
            {"internalType": "uint256", "name": "leafIndex", "type": "uint256"},
            {"internalType": "address", "name": "account", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
            {"internalType": "bytes32[]", "name": "merkleProof", "type": "bytes32[]"},
        ], "internalType": "struct RewardDistributor.ClaimInput", "name": "claimInput", "type": "tuple"}],
        "name": "claimReward", "outputs": [], "stateMutability": "nonpayable", "type": "function",
    },
    {
        "inputs": [{"internalType": "address", "name": "", "type": "address"}],
        "name": "userTotalRewardClaimed", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view", "type": "function",
    },
    {
        "inputs": [], "name": "rewardMerkleRoot",
        "outputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}],
        "stateMutability": "view", "type": "function",
    },
    {
        "inputs": [], "name": "currentEpoch",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view", "type": "function",
    },
    {
        "inputs": [{"internalType": "address", "name": "", "type": "address"}],
        "name": "userLastClaimedEpoch", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view", "type": "function",
    },
]


def build_leaf(leaf_index, account, amount):
    return keccak(encode(["uint256", "address", "uint256"], [leaf_index, account, amount]))


def compute_root(leaf_hash, proof):
    current = leaf_hash
    for proof_item in proof:
        proof_bytes = bytes.fromhex(proof_item[2:])
        left, right = (current, proof_bytes) if current < proof_bytes else (proof_bytes, current)
        current = keccak(left + right)
    return current.hex()


def fmt(value_wei):
    return f"{value_wei / 1e18:,.4f}"


def separator():
    print("-" * 50)


def main():
    print("=" * 56)
    print("   gUBI Claim Tool — Galactica Mainnet")
    print("=" * 56)
    print()
    print("  This tool lets you claim your gUBI token rewards")
    print("  directly from the Galactica blockchain.")
    print()
    print("  gUBI is distributed monthly to veGNET holders based")
    print("  on their SoulScore and voting power.")
    print()

    # --- wallet address ---
    print("STEP 1: Enter your wallet address")
    print("  Your public wallet address starts with 0x")
    print("  Example: 0x85830f211C5534eABAFd83b346eb61128a6995c9")
    print()
    while True:
        raw = input("  Wallet address: ").strip()
        if Web3.is_address(raw):
            address = Web3.to_checksum_address(raw)
            break
        print("  ! That doesn't look like a valid address. Try again.")
    print()

    print("STEP 2: Checking your rewards...")
    print("  Connecting to Galactica network...")
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        print()
        print("  ERROR: Could not connect to Galactica network.")
        print("  Please check your internet connection and try again.")
        input("\nPress Enter to exit...")
        sys.exit(1)

    print("  Fetching your claim data from Galactica API...")
    api_url = f"https://admin-panel.galactica.com/api/claim/gubi/{address.lower()}?chainId={CHAIN_ID}"
    try:
        response = requests.get(api_url, timeout=20)
    except requests.RequestException as exc:
        print(f"\n  ERROR: Network error: {exc}")
        input("\nPress Enter to exit...")
        sys.exit(1)

    if response.status_code == 404:
        print()
        print("  This address has no gUBI rewards to claim.")
        print("  Make sure you have veGNET locked and a SoulScore.")
        input("\nPress Enter to exit...")
        sys.exit(1)
    response.raise_for_status()
    data = response.json()

    contract = w3.eth.contract(address=GUBI_DISTRIBUTOR, abi=ABI)
    claim_input = (
        int(data["leafIndex"]),
        Web3.to_checksum_address(data["account"]),
        int(data["amount"]),
        data["merkleProof"],
    )

    current_epoch = contract.functions.currentEpoch().call()
    claimed_wei = contract.functions.userTotalRewardClaimed(address).call()
    last_claimed_epoch = contract.functions.userLastClaimedEpoch(address).call()
    onchain_root = contract.functions.rewardMerkleRoot().call().hex()
    computed_root = compute_root(build_leaf(claim_input[0], claim_input[1], claim_input[2]), claim_input[3])
    claimable_wei = max(claim_input[2] - claimed_wei, 0)

    print()
    separator()
    print(f"  Wallet address:   {address}")
    print(f"  Current epoch:    {current_epoch}  (rewards are distributed each epoch)")
    print(f"  Last claimed:     epoch {last_claimed_epoch}")
    print(f"  Already claimed:  {fmt(claimed_wei)} gUBI  (lifetime total)")
    print(f"  Total entitled:   {fmt(claim_input[2])} gUBI  (cumulative from all epochs)")
    print(f"  Claimable now:    {fmt(claimable_wei)} gUBI")
    separator()

    if computed_root.lower() != onchain_root.lower():
        print()
        print("  NOTE: The reward data is being updated on-chain right now.")
        print("  This happens after each epoch. Please try again in a few minutes.")
        input("\nPress Enter to exit...")
        sys.exit(2)

    if claimable_wei <= 0:
        print()
        print("  You have nothing to claim right now.")
        print("  Rewards become claimable after each epoch update.")
        print(f"  You are on epoch {last_claimed_epoch}, current is {current_epoch}.")
        input("\nPress Enter to exit...")
        return

    print()
    print(f"STEP 3: Claim {fmt(claimable_wei)} gUBI")
    print()
    answer = input("  Do you want to proceed with the claim? (y/n): ").strip().lower()
    if answer != "y":
        print("  Cancelled. No transaction was sent.")
        input("\nPress Enter to exit...")
        return

    print()
    print("STEP 4: Sign the transaction with your private key")
    print()
    print("  Your private key is required to authorize the transaction.")
    print("  It is a 64-character hex string, usually starting with 0x.")
    print("  You can find it in MetaMask: Account Details -> Export Private Key")
    print()
    print("  IMPORTANT: Your key is never stored, logged, or sent anywhere.")
    print("  It is used only to sign the transaction locally on your computer.")
    print("  When you type it, the characters will NOT be visible (hidden input).")
    print()
    while True:
        private_key = getpass.getpass("  Private key (hidden): ").strip()
        if not private_key:
            print("  ! No key entered. Try again.")
            continue
        if not private_key.startswith("0x"):
            private_key = f"0x{private_key}"
        try:
            signer = Account.from_key(private_key)
        except Exception:
            print("  ! Invalid private key format. Make sure you copied the full key.")
            continue
        if signer.address.lower() != address.lower():
            print(f"  ! This key belongs to a different address: {signer.address}")
            print(f"  ! Expected address:                        {address}")
            print("  ! Make sure you are using the correct key for the wallet above.")
            retry = input("  Try a different key? (y/n): ").strip().lower()
            if retry != "y":
                print("  Cancelled.")
                input("\nPress Enter to exit...")
                sys.exit(0)
            continue
        print("  Key verified — address matches.")
        break

    print()
    print("STEP 5: Sending transaction...")
    print("  Running a test simulation first to make sure it will succeed...")
    try:
        contract.functions.claimReward(claim_input).call({"from": address})
    except Exception as exc:
        print(f"\n  ERROR: Transaction simulation failed: {exc}")
        print("  The transaction would revert on-chain. Nothing was sent.")
        input("\nPress Enter to exit...")
        sys.exit(3)

    gas_price = w3.eth.gas_price
    estimated_gas = contract.functions.claimReward(claim_input).estimate_gas({"from": address})
    gas_cost = estimated_gas * gas_price / 1e18

    print(f"  Simulation passed. Estimated gas fee: {gas_cost:.8f} GNET (very small)")
    print("  Broadcasting transaction to the network...")
    print()

    tx = contract.functions.claimReward(claim_input).build_transaction({
        "from": address,
        "chainId": CHAIN_ID,
        "nonce": w3.eth.get_transaction_count(address),
        "gas": int(estimated_gas * 1.2),
        "gasPrice": gas_price,
        "value": 0,
    })
    signed = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)

    print("=" * 56)
    print(f"  SUCCESS!")
    print(f"  Claimed {fmt(claimable_wei)} gUBI to your wallet.")
    print()
    print(f"  Transaction ID:")
    print(f"  {tx_hash.hex()}")
    print()
    print(f"  View on explorer:")
    print(f"  https://explorer.galactica.com/tx/{tx_hash.hex()}")
    print("=" * 56)
    print()
    print("  The gUBI tokens should appear in your wallet shortly.")
    print("  You can add the token to MetaMask manually:")
    print("  Token address: 0xFEa4F549eFB1F8B2cBA8d029e6845Ee431e142AA")
    input("\nPress Enter to exit...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(0)
