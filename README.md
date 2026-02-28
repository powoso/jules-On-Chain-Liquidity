# Polygon Whale Monitor & Polymarket Predictor

A beautiful, lightweight web application that monitors the Polygon network for large USDC transfers to specific "Whale" wallet addresses. When a transfer over a defined threshold is detected, it triggers an alert and cross-references recent/active events on the Polymarket Gamma API to predict where capital might be deployed.

## Features
- **Real-time Blockchain Monitoring**: Uses `web3.py` to listen for ERC20 `Transfer` events on the Polygon network.
- **Polymarket Integration**: Automatically queries the Gamma API to fetch current active markets when a whale makes a move.
- **Beautiful UI/UX**: A responsive dashboard built with Tailwind CSS to configure tracking parameters and view live logs.
- **Dynamic Configuration**: Update your tracked RPC endpoints, thresholds, and whale addresses on the fly without restarting the server.

---

## Prerequisites (macOS)

Before you begin, ensure you have the following installed on your Mac:
1. **Homebrew** (Optional but recommended for installing Python):
   Open Terminal and run:
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
2. **Python 3.10+**:
   ```bash
   brew install python
   ```

---

## Installation & Setup

1. **Clone the repository**:
   Open Terminal and run:
   ```bash
   git clone https://github.com/your-username/polygon-whale-monitor.git
   cd polygon-whale-monitor
   ```

2. **Create a Virtual Environment**:
   It is best practice to use a virtual environment to manage dependencies.
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: If `requirements.txt` is missing, run: `pip install flask web3 requests`)*

4. **Verify Configuration**:
   The `wallets.json` file holds the configuration. By default, it contains a dummy address. You can update this file directly or via the web UI.

---

## Running the Application

1. **Start the Flask Server**:
   Make sure your virtual environment is activated (`source venv/bin/activate`), then run:
   ```bash
   python3 app.py
   ```

2. **Access the Dashboard**:
   Open your web browser (Safari, Chrome, Arc, etc.) and navigate to:
   ```
   http://127.0.0.1:5000
   ```

3. **Configure & Start**:
   - In the web interface, update the **Polygon RPC URL**, **Alert Threshold**, and **Tracked Whales**.
   - Click **Save Configuration**.
   - Click **Start Monitor** to begin tracking blockchain events. Live logs will stream directly to your console on the right!

---

## Troubleshooting

- **Failed to connect to Polygon network**: Public RPC endpoints can be rate-limited. If you encounter this, try signing up for a free private RPC key via [Alchemy](https://www.alchemy.com/), [Infura](https://infura.io/), or [Ankr](https://www.ankr.com/), and update the RPC URL in the Configuration panel.
- **Port already in use**: If port 5000 is blocked, you can change the port in `app.py` by modifying the `app.run` line to `app.run(debug=True, port=8080)`.
