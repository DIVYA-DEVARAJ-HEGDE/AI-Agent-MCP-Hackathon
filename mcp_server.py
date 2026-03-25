import os
import json
from mcp.server.fastmcp import FastMCP
from web3 import Web3

# 1. Initialize the MCP Server
mcp = FastMCP("CarbonRegistryServer")

# 2. Connect to your Blockchain (Ganache default RPC)
# Ensure your Ganache instance is running!
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:7545'))

# Your deployed CarbonRegistry contract address (Update this after deploying to Ganache)
CONTRACT_ADDRESS = "0xYourDeployedContractAddressHere"

# Simplified ABI based on your carboncredit.sol file
CONTRACT_ABI = json.loads("""
[
    {
        "inputs": [{"internalType": "address", "name": "orgAddr", "type": "address"}],
        "name": "getOrgDetails",
        "outputs": [
            {
                "components": [
                    {"internalType": "string", "name": "name", "type": "string"},
                    {"internalType": "bool", "name": "registered", "type": "bool"},
                    {"internalType": "bool", "name": "nftIssued", "type": "bool"},
                    {"internalType": "uint256", "name": "nftId", "type": "uint256"},
                    {"internalType": "uint256", "name": "totalEmissions", "type": "uint256"},
                    {"internalType": "uint256", "name": "creditsEarned", "type": "uint256"}
                ],
                "internalType": "struct CarbonRegistry.Organization",
                "name": "",
                "type": "tuple"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "orgAddr", "type": "address"},
            {"internalType": "uint256", "name": "index", "type": "uint256"},
            {"internalType": "bool", "name": "status", "type": "bool"}
        ],
        "name": "verifyEmission",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]
""")

# Initialize the contract object
registry_contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)

# ---------------------------------------------------------
# MCP TOOL 1: Read Blockchain Data
# ---------------------------------------------------------
@mcp.tool()
def get_organization_details(wallet_address: str) -> str:
    """Fetches the registration, NFT status, and total emissions for an organization from the blockchain."""
    try:
        # Convert to checksum address for Web3
        checksum_addr = w3.to_checksum_address(wallet_address)
        
        # Call the view function on the smart contract
        org_data = registry_contract.functions.getOrgDetails(checksum_addr).call()
        
        # Format the response for the AI Agent
        result = {
            "Name": org_data[0],
            "Is Registered": org_data[1],
            "NFT Issued": org_data[2],
            "NFT Token ID": org_data[3],
            "Total Emissions (tCO2e)": org_data[4],
            "Credits Earned (CCT)": org_data[5]
        }
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error fetching organization details: {str(e)}"

# ---------------------------------------------------------
# MCP TOOL 2: Execute Smart Contract Transaction
# ---------------------------------------------------------
@mcp.tool()
def verify_emission_report(org_wallet_address: str, report_index: int, is_valid: bool) -> str:
    """Allows the Auditor to verify an organization's emission report on-chain."""
    try:
        checksum_addr = w3.to_checksum_address(org_wallet_address)
        
        # In a real environment, you would use an environment variable for the Auditor's private key
        # For Ganache testing, we use the first unlocked account assuming it's the Auditor
        auditor_account = w3.eth.accounts[0] 
        
        # Build the transaction
        tx_hash = registry_contract.functions.verifyEmission(
            checksum_addr, 
            report_index, 
            is_valid
        ).transact({'from': auditor_account})
        
        # Wait for the transaction to be mined
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return f"Successfully verified report {report_index} for {checksum_addr}. Transaction Hash: {receipt.transactionHash.hex()}"
    except Exception as e:
        return f"Blockchain transaction failed: {str(e)}"

if __name__ == "__main__":
    print("Starting Carbon Registry MCP Server...")
    # This exposes the tools via Standard Input/Output, which is how ADK agents communicate with local MCP servers.
    mcp.run()