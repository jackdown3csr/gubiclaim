"""
burn_gubi.py - Burn gUBI tokens to redeem WGNET + ARCHAI on Galactica Mainnet

Just run:
    python burn_gubi.py

The script will install missing dependencies and guide you step by step.
"""

import subprocess
import sys


def ensure_dependencies():
    packages = ["web3", "eth-account"]
    missing = []
    for pkg in packages:
        import_name = pkg.replace("-", "_").split("==")[0]
        if pkg == "eth-account":
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
        subprocess.check_call([sys.executable] + sys.argv)
        sys.exit(0)


ensure_dependencies()

import getpass  # noqa: E402

from eth_account import Account  # noqa: E402
from web3 import Web3  # noqa: E402

RPC_URL  = "https://galactica-mainnet.g.alchemy.com/public"
CHAIN_ID = 613419

VAULT  = Web3.to_checksum_address("0x50AF2AAb1455C1C06B3b8e623549dDE437F54EeF")
GUBI   = Web3.to_checksum_address("0xFEa4F549eFB1F8B2cBA8d029e6845Ee431e142AA")
WGNET  = Web3.to_checksum_address("0x690F1eEf8AcEaD09Ac695d9111Af081045c6d5b7")
ARCHAI = Web3.to_checksum_address("0x22b48a764d2aAAe14d751aD2B5fcdf6C0A4d95D7")

ERC20_ABI = [
    {"inputs": [{"name": "account", "type": "address"}], "name": "balanceOf",
     "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "totalSupply",
     "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}],
     "name": "approve", "outputs": [{"type": "bool"}],
     "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}],
     "name": "allowance", "outputs": [{"type": "uint256"}],
     "stateMutability": "view", "type": "function"},
]

VAULT_ABI = [
    {"inputs": [{"name": "amount", "type": "uint256"}], "name": "burnIndexToken",
     "outputs": [], "stateMutability": "nonpayable", "type": "function"},
]


def fmt(wei: int, decimals: int = 18) -> str:
    return f"{wei / 10 ** decimals:,.4f}"


def separator():
    print("-" * 56)


def main() -> None:
    print("=" * 56)
    print("   gUBI Burn Tool — Galactica Mainnet")
    print("=" * 56)
    print()
    print("  This tool burns your gUBI tokens via the IndexPool")
    print("  contract and redeems proportional WGNET + ARCHAI.")
    print()
    print("  gUBI is Galactica's Universal Basic Income token.")
    print("  Burning it redeems your share of the IndexPool vault.")
    print()

    # STEP 1: wallet address
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

    # STEP 2: connect and fetch balances
    print("STEP 2: Checking balances...")
    print("  Connecting to Galactica network...")
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        print()
        print("  ERROR: Could not connect to Galactica network.")
        print("  Please check your internet connection and try again.")
        input("\nPress Enter to exit...")
        sys.exit(1)

    gubi_c   = w3.eth.contract(address=GUBI,   abi=ERC20_ABI)
    wgnet_c  = w3.eth.contract(address=WGNET,  abi=ERC20_ABI)
    archai_c = w3.eth.contract(address=ARCHAI, abi=ERC20_ABI)

    gubi_balance_wei    = gubi_c.functions.balanceOf(address).call()
    gubi_supply_wei     = gubi_c.functions.totalSupply().call()
    wgnet_in_vault_wei  = wgnet_c.functions.balanceOf(VAULT).call()
    archai_in_vault_wei = archai_c.functions.balanceOf(VAULT).call()

    print()
    separator()
    print(f"  Wallet address:   {address}")
    print(f"  gUBI balance:     {fmt(gubi_balance_wei)} gUBI")
    print(f"  IndexPool holds:  {fmt(wgnet_in_vault_wei)} WGNET")
    print(f"                    {fmt(archai_in_vault_wei)} ARCHAI")
    separator()
    print()

    if gubi_balance_wei == 0:
        print("  You have no gUBI to burn.")
        input("\nPress Enter to exit...")
        return

    # STEP 3: amount to burn
    print("STEP 3: Enter amount to burn")
    print(f'  Enter a number or type "all" to burn your full balance')
    print(f"  ({fmt(gubi_balance_wei)} gUBI)")
    print()
    while True:
        raw_amount = input("  Amount to burn: ").strip()
        if raw_amount.lower() == "all":
            burn_wei = gubi_balance_wei
            break
        try:
            from decimal import Decimal
            burn_amount = Decimal(raw_amount)
            if burn_amount <= 0:
                print("  ! Amount must be greater than zero.")
                continue
            burn_wei = int(burn_amount * 10 ** 18)
            if burn_wei > gubi_balance_wei:
                print(f"  ! Amount exceeds your balance of {fmt(gubi_balance_wei)} gUBI.")
                continue
            break
        except Exception:
            print("  ! Invalid amount. Enter a number (e.g. 1000) or 'all'.")

    share = burn_wei / gubi_supply_wei
    wgnet_out_wei  = int(wgnet_in_vault_wei  * share)
    archai_out_wei = int(archai_in_vault_wei * share)

    print()
    separator()
    print(f"  Burn:             {fmt(burn_wei)} gUBI")
    print(f"  Share of supply:  {share * 100:.4f}%")
    print()
    print(f"  Estimated payout (proportional):")
    print(f"    WGNET:          ~{fmt(wgnet_out_wei)} WGNET")
    print(f"    ARCHAI:         ~{fmt(archai_out_wei)} ARCHAI")
    separator()
    print()
    print("  NOTE: The actual payout depends on the pool composition")
    print("  at execution time and may differ slightly from the estimate.")
    print()

    answer = input("  Do you want to proceed with the burn? (y/n): ").strip().lower()
    if answer != "y":
        print("  Cancelled. No transaction was sent.")
        input("\nPress Enter to exit...")
        return

    # STEP 4: private key
    print()
    print("STEP 4: Sign the transactions with your private key")
    print()
    print("  Your private key is required to authorize the transaction.")
    print("  It is a 64-character hex string, usually starting with 0x.")
    print("  You can find it in MetaMask: Account Details -> Export Private Key")
    print()
    print("  IMPORTANT: Your key is never stored, logged, or sent anywhere.")
    print("  It is used only to sign transactions locally on your computer.")
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

    gas_price = w3.eth.gas_price
    vault_c = w3.eth.contract(address=VAULT, abi=VAULT_ABI)

    # STEP 5: approve if needed
    print()
    allowance = gubi_c.functions.allowance(address, VAULT).call()
    if allowance < burn_wei:
        print("STEP 5/6: Approving gUBI spend...")
        approve_fn = gubi_c.functions.approve(VAULT, burn_wei)
        estimated  = approve_fn.estimate_gas({"from": address})
        tx = approve_fn.build_transaction({
            "from": address,
            "chainId": CHAIN_ID,
            "nonce": w3.eth.get_transaction_count(address),
            "gas": int(estimated * 1.2),
            "gasPrice": gas_price,
        })
        signed   = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash  = w3.eth.send_raw_transaction(signed.raw_transaction)
        print(f"  Approval TX: {tx_hash.hex()}")
        print("  Waiting for confirmation...")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
        if receipt.status != 1:
            print("  Approval transaction failed. Aborting.")
            input("\nPress Enter to exit...")
            sys.exit(2)
        print("  Approved successfully.")
    else:
        print("STEP 5/6: gUBI already approved for this amount.")

    # STEP 6: burn
    print()
    print("STEP 6/6: Burning gUBI...")
    print("  Running simulation first...")
    burn_fn = vault_c.functions.burnIndexToken(burn_wei)
    try:
        burn_fn.call({"from": address})
    except Exception as exc:
        print(f"\n  ERROR: Transaction simulation failed: {exc}")
        print("  The burn would revert. No transaction was sent.")
        input("\nPress Enter to exit...")
        sys.exit(3)

    estimated = burn_fn.estimate_gas({"from": address})
    gas_cost_wei = int(estimated * 1.2) * gas_price
    print(f"  Simulation passed. Estimated gas fee: {gas_cost_wei / 1e18:.8f} GNET")
    print("  Broadcasting transaction to the network...")

    tx = burn_fn.build_transaction({
        "from": address,
        "chainId": CHAIN_ID,
        "nonce": w3.eth.get_transaction_count(address),
        "gas": int(estimated * 1.2),
        "gasPrice": gas_price,
    })
    signed  = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)

    print()
    print("  Waiting for confirmation...")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)

    print()
    print("=" * 56)
    if receipt.status == 1:
        print("SUCCESS!")
        print(f"  Burned {fmt(burn_wei)} gUBI.")
        print(f"  WGNET and ARCHAI have been sent to your wallet.")
        print()
        print(f"  Transaction ID:")
        print(f"  {tx_hash.hex()}")
        print()
        print(f"  View on explorer:")
        print(f"  https://explorer.galactica.com/tx/{tx_hash.hex()}")
    else:
        print("FAILED: Transaction was reverted on-chain.")
        print(f"  TX: {tx_hash.hex()}")
    print("=" * 56)

    input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
