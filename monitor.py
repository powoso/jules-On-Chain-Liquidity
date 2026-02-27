import json
import time
import requests
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from web3.exceptions import BlockNotFound
import sys

# Load configurations
def load_config(filepath='wallets.json'):
    with open(filepath, 'r') as f:
        return json.load(f)

# Connect to Web3
def connect_web3(rpc_url):
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    if not w3.is_connected():
        print("Failed to connect to Polygon network.")
        sys.exit(1)
    return w3

# Fetch latest Polymarket events
def get_polymarket_events():
    # Attempting to fetch recent/active events to cross-reference
    # We query for active events and take the most recent ones.
    url = "https://gamma-api.polymarket.com/events?active=true&limit=10"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        events = response.json()
        return events
    except Exception as e:
        print(f"Error fetching Polymarket events: {e}")
        return []

def main():
    config = load_config()

    usdc_contract_address = config.get("usdc_contract")
    rpc_url = config.get("rpc_url")
    threshold_usd = config.get("threshold", 10000)
    # USDC has 6 decimals
    threshold = threshold_usd * (10 ** 6)

    whales = [w.lower() for w in config.get("whales", [])]
    abi = config.get("erc20_transfer_abi")

    w3 = connect_web3(rpc_url)
    print(f"Connected to Polygon. Monitoring USDC transfers for whales...")

    # Instantiate the contract
    usdc_contract = w3.eth.contract(address=Web3.to_checksum_address(usdc_contract_address), abi=abi)

    # We will poll for new blocks
    try:
        latest_block = w3.eth.get_block('latest').number
    except Exception as e:
        print(f"Error getting latest block: {e}")
        sys.exit(1)

    print(f"Starting from block: {latest_block}")

    # Set up event filter for Transfers
    # Note: polling using createFilter is sometimes unsupported on public RPCs,
    # so we will manually fetch logs block by block

    while True:
        try:
            current_block = w3.eth.get_block('latest').number
            if current_block > latest_block:
                for block_num in range(latest_block + 1, current_block + 1):
                    # Fetch logs for the specific block
                    logs = w3.eth.get_logs({
                        'fromBlock': block_num,
                        'toBlock': block_num,
                        'address': Web3.to_checksum_address(usdc_contract_address),
                        # Topic 0 for Transfer(address,address,uint256)
                        'topics': [w3.keccak(text="Transfer(address,address,uint256)").hex()]
                    })

                    for log in logs:
                        try:
                            # Parse the log using the contract ABI
                            parsed_log = usdc_contract.events.Transfer().process_log(log)
                            args = parsed_log['args']
                            recipient = args['to'].lower()
                            value = args['value']

                            # Check if recipient is a whale and amount >= threshold
                            if recipient in whales and value >= threshold:
                                amount_usd = value / (10 ** 6)
                                print(f"\n[!] ALERT: Large USDC transfer detected!")
                                print(f"Recipient: {args['to']}")
                                print(f"Amount: ${amount_usd:,.2f} USDC")
                                print(f"Transaction Hash: {parsed_log['transactionHash'].hex()}")

                                # Fetch Polymarket events for cross-referencing
                                print("Fetching recent Polymarket events to predict deployment...")
                                events = get_polymarket_events()
                                if events:
                                    print("Potential targets (Recent/Active Markets):")
                                    for event in events:
                                        title = event.get('title', 'Unknown Title')
                                        print(f" - {title}")
                                else:
                                    print("Could not fetch Polymarket events.")
                                print("-" * 40)
                        except Exception as e:
                            # Some logs might not perfectly match if they're not standard transfers, ignore
                            continue

                latest_block = current_block

            # Sleep to avoid spamming the RPC
            time.sleep(5)

        except BlockNotFound:
            time.sleep(5)
        except Exception as e:
            print(f"Error during polling: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
