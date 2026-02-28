import json
import time
import requests
import threading
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from web3.exceptions import BlockNotFound
import sys

# Global flag to control the monitor loop
monitor_running = False

def log_message(msg, logs_queue):
    print(msg)
    if logs_queue is not None:
        logs_queue.append(msg)

# Load configurations
def load_config(filepath='wallets.json'):
    with open(filepath, 'r') as f:
        return json.load(f)

# Connect to Web3
def connect_web3(rpc_url):
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    if not w3.is_connected():
        return None
    return w3

# Fetch latest Polymarket events
def get_polymarket_events(logs_queue=None):
    url = "https://gamma-api.polymarket.com/events?active=true&limit=10"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        events = response.json()
        return events
    except Exception as e:
        log_message(f"Error fetching Polymarket events: {e}", logs_queue)
        return []

def run_monitor(logs_queue):
    global monitor_running
    monitor_running = True

    config = load_config()
    usdc_contract_address = config.get("usdc_contract")
    rpc_url = config.get("rpc_url")
    threshold_usd = config.get("threshold", 10000)
    threshold = threshold_usd * (10 ** 6)
    whales = [w.lower() for w in config.get("whales", [])]
    abi = config.get("erc20_transfer_abi")

    w3 = connect_web3(rpc_url)
    if not w3:
        log_message("Failed to connect to Polygon network. Monitor stopped.", logs_queue)
        monitor_running = False
        return

    log_message("Connected to Polygon. Monitoring USDC transfers for whales...", logs_queue)
    usdc_contract = w3.eth.contract(address=Web3.to_checksum_address(usdc_contract_address), abi=abi)

    try:
        latest_block = w3.eth.get_block('latest').number
    except Exception as e:
        log_message(f"Error getting latest block: {e}. Monitor stopped.", logs_queue)
        monitor_running = False
        return

    log_message(f"Starting from block: {latest_block}", logs_queue)

    while monitor_running:
        try:
            current_block = w3.eth.get_block('latest').number
            if current_block > latest_block:
                for block_num in range(latest_block + 1, current_block + 1):
                    if not monitor_running:
                        break

                    # Fix: hex string topic requires '0x' prefix for some RPCs, but web3.py usually handles bytes/hex.
                    # Let's ensure it's explicitly correct.
                    logs = w3.eth.get_logs({
                        'fromBlock': block_num,
                        'toBlock': block_num,
                        'address': Web3.to_checksum_address(usdc_contract_address),
                        'topics': [w3.keccak(text="Transfer(address,address,uint256)")]
                    })

                    for log in logs:
                        try:
                            parsed_log = usdc_contract.events.Transfer().process_log(log)
                            args = parsed_log['args']
                            recipient = args['to'].lower()
                            value = args['value']

                            if recipient in whales and value >= threshold:
                                amount_usd = value / (10 ** 6)
                                alert_msg = (f"\n[!] ALERT: Large USDC transfer detected!\n"
                                             f"Recipient: {args['to']}\n"
                                             f"Amount: ${amount_usd:,.2f} USDC\n"
                                             f"Transaction Hash: {parsed_log['transactionHash'].hex()}")
                                log_message(alert_msg, logs_queue)

                                log_message("Fetching recent Polymarket events to predict deployment...", logs_queue)
                                events = get_polymarket_events(logs_queue)
                                if events:
                                    log_message("Potential targets (Recent/Active Markets):", logs_queue)
                                    for event in events:
                                        title = event.get('title', 'Unknown Title')
                                        log_message(f" - {title}", logs_queue)
                                else:
                                    log_message("Could not fetch Polymarket events.", logs_queue)
                                log_message("-" * 40, logs_queue)
                        except Exception:
                            continue

                latest_block = current_block

            time.sleep(5)

        except BlockNotFound:
            time.sleep(5)
        except Exception as e:
            log_message(f"Error during polling: {e}", logs_queue)
            time.sleep(10)

    log_message("Monitor stopped.", logs_queue)

if __name__ == "__main__":
    # If run directly, run without threading/queues
    run_monitor(None)
