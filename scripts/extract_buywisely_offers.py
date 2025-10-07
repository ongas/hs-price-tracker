#!/usr/bin/env python3
"""
Utility script to extract and analyze RAW unfiltered BuyWisely offer data.
Extracts all offers directly from NextJS hydration data without any filtering.

Usage:
    python scripts/extract_buywisely_offers.py

This script reads URLs from scripts/product_urls.yaml and creates TSV files in the scripts directory.
"""

import sys
import asyncio
from pathlib import Path
import os
import yaml

# Add the custom_components path to sys.path
script_dir = Path(__file__).parent
repo_root = script_dir.parent
sys.path.insert(0, str(repo_root / "custom_components" / "price_tracker"))

from services.buywisely.hydration_parser import extract_and_parse_all_hydration_data

# Import the fetch utility from the same directory
sys.path.insert(0, str(script_dir))
from fetch_buywisely_html import fetch_buywisely_html


async def extract_offers(source: str, output_file: str = None):
    """Extract ALL raw unfiltered offers from a BuyWisely URL."""

    print(f"=== Fetching live HTML from: {source} ===\n")
    html = await fetch_buywisely_html(source)
    if not html:
        print("Error: Failed to fetch HTML from URL")
        return None

    source_name = source.split("/")[-1] or "buywisely_product"
    print(f"=== Extracting RAW UNFILTERED offers from: {source_name} ===\n")

    # Extract all hydration data
    hydration_blocks = extract_and_parse_all_hydration_data(html)

    # Find the block with offers
    hydration_data = None
    for block in hydration_blocks:
        if isinstance(block, dict) and "offers" in block:
            hydration_data = block
            break

    if not hydration_data:
        print("Error: Could not find offers in hydration data")
        return None

    # Display product info
    product_title = hydration_data.get("title", "N/A")
    print(f"Product Title: {product_title}")

    # Extract raw offers (NO FILTERING)
    offers = hydration_data.get("offers", [])
    print(f"\nTotal RAW offers in hydration data: {len(offers)}")

    if not offers:
        print("No offers found in the HTML")
        return None

    # Prepare TSV output - save in scripts directory if no path specified
    if output_file:
        if not os.path.isabs(output_file):
            output_path = script_dir / output_file
        else:
            output_path = Path(output_file)
        with open(output_path, "w", encoding="utf-8") as f:
            # Write header - now with ALL nested fields from hydration data
            f.write(
                "Index\tSeller_Name\tSeller_ID\tBase_Price\tShipping\tCALC_Total_Price\t"
            )
            f.write("Created_At\tCondition\tCALC_Has_Shopback\tCALC_Has_Cashrewards\t")
            f.write("Seller_URL\tProduct_URL\tOffer_ID\tPID\tCountry_Code\t")
            # Shopback fields (all available)
            f.write("Shopback_ID\tShopback_Name\tShopback_URL\tShopback_Commission\t")
            f.write("Shopback_Created_At\tShopback_Updated_At\tShopback_Hostname\t")
            # Cashrewards fields (all available)
            f.write(
                "Cashrewards_ID\tCashrewards_Name\tCashrewards_Commission_String\tCashrewards_Commission\t"
            )
            f.write(
                "Cashrewards_Hyphenated_Name\tCashrewards_Logo\tCashrewards_Online\tCashrewards_Instore\t"
            )
            f.write(
                "Cashrewards_Hostname\tCashrewards_Created_At\tCashrewards_Updated_At\n"
            )

            # Write each offer
            for idx, offer in enumerate(offers, 1):
                base_price = offer.get("base_price", 0)
                shipping = offer.get("shipping", 0)
                total_price = base_price + shipping
                seller = offer.get("seller", {})
                seller_name = seller.get("name", "Unknown")
                seller_id = seller.get("seller_id", "N/A")
                seller_url = seller.get("url", "N/A")

                # Check for affiliate markers
                shopback_obj = seller.get("shopback")
                cashrewards_obj = seller.get("cashrewards")
                has_shopback = shopback_obj is not None
                has_cashrewards = cashrewards_obj is not None

                # Extract ALL shopback details
                shopback_id = (
                    shopback_obj.get("sb_id", "N/A") if shopback_obj else "N/A"
                )
                shopback_name = (
                    shopback_obj.get("sb_name", "N/A") if shopback_obj else "N/A"
                )
                shopback_url = shopback_obj.get("url", "N/A") if shopback_obj else "N/A"
                shopback_commission = (
                    shopback_obj.get("commission", "N/A") if shopback_obj else "N/A"
                )
                shopback_created_at = (
                    shopback_obj.get("created_at", "N/A") if shopback_obj else "N/A"
                )
                shopback_updated_at = (
                    shopback_obj.get("updated_at", "N/A") if shopback_obj else "N/A"
                )
                shopback_hostname = (
                    shopback_obj.get("hostname", "N/A") if shopback_obj else "N/A"
                )

                # Extract ALL cashrewards details
                cashrewards_id = (
                    cashrewards_obj.get("cr_id", "N/A") if cashrewards_obj else "N/A"
                )
                cashrewards_name = (
                    cashrewards_obj.get("name", "N/A") if cashrewards_obj else "N/A"
                )
                cashrewards_commission_string = (
                    cashrewards_obj.get("commission_string", "N/A")
                    if cashrewards_obj
                    else "N/A"
                )
                cashrewards_commission = (
                    cashrewards_obj.get("commission", "N/A")
                    if cashrewards_obj
                    else "N/A"
                )
                cashrewards_hyphenated_name = (
                    cashrewards_obj.get("hyphenated_name", "N/A")
                    if cashrewards_obj
                    else "N/A"
                )
                cashrewards_logo = (
                    cashrewards_obj.get("logo", "N/A") if cashrewards_obj else "N/A"
                )
                cashrewards_online = (
                    cashrewards_obj.get("online", "N/A") if cashrewards_obj else "N/A"
                )
                cashrewards_instore = (
                    cashrewards_obj.get("instore", "N/A") if cashrewards_obj else "N/A"
                )
                cashrewards_hostname = (
                    cashrewards_obj.get("hostname", "N/A") if cashrewards_obj else "N/A"
                )
                cashrewards_created_at = (
                    cashrewards_obj.get("created_at", "N/A")
                    if cashrewards_obj
                    else "N/A"
                )
                cashrewards_updated_at = (
                    cashrewards_obj.get("updated_at", "N/A")
                    if cashrewards_obj
                    else "N/A"
                )

                # Extract other fields
                created_at = offer.get("created_at", "N/A")
                condition = offer.get("condition", "N/A")
                product_url = offer.get("seller_product_url", "N/A")
                offer_id = offer.get("offer_id", "N/A")
                pid = offer.get("pid", "N/A")
                country_code = offer.get("country_code", "N/A")

                # Write row
                f.write(
                    f"{idx}\t{seller_name}\t{seller_id}\t{base_price}\t{shipping}\t{total_price:.2f}\t"
                )
                f.write(
                    f"{created_at}\t{condition}\t{has_shopback}\t{has_cashrewards}\t"
                )
                f.write(
                    f"{seller_url}\t{product_url}\t{offer_id}\t{pid}\t{country_code}\t"
                )
                # Shopback data (all fields)
                f.write(
                    f"{shopback_id}\t{shopback_name}\t{shopback_url}\t{shopback_commission}\t"
                )
                f.write(
                    f"{shopback_created_at}\t{shopback_updated_at}\t{shopback_hostname}\t"
                )
                # Cashrewards data (all fields)
                f.write(
                    f"{cashrewards_id}\t{cashrewards_name}\t{cashrewards_commission_string}\t{cashrewards_commission}\t"
                )
                f.write(
                    f"{cashrewards_hyphenated_name}\t{cashrewards_logo}\t{cashrewards_online}\t{cashrewards_instore}\t"
                )
                f.write(
                    f"{cashrewards_hostname}\t{cashrewards_created_at}\t{cashrewards_updated_at}\n"
                )

        print(f"\nTSV output written to: {output_path}")
        print(f"Total offers written: {len(offers)}")

    return offers


async def main():
    # Always use config file
    config_file = script_dir / "product_urls.yaml"
    if not config_file.exists():
        print(f"Error: Config file not found at {config_file}")
        sys.exit(1)

    with open(config_file, "r") as f:
        config = yaml.safe_load(f)

    product_urls = config.get("product_urls", [])
    if not product_urls:
        print("No product URLs found in config file")
        sys.exit(1)

    # Process all URLs from config
    for idx, url in enumerate(product_urls):
        slug = url.rstrip("/").split("/")[-1]
        output_file = f"{slug}_raw_offers.tsv"
        print(f"\n{'='*80}")
        print(f"Processing URL {idx+1}/{len(product_urls)}: {url}")
        print(f"{'='*80}")
        await extract_offers(url, output_file)


if __name__ == "__main__":
    asyncio.run(main())
