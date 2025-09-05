from curl_cffi import requests
import fake_useragent
import json
import os
import asyncio

async def fetch_html_for_test(url: str, output_file: str):
    try:
        ua = fake_useragent.UserAgent()
        headers = {
            "User-Agent": ua.random,
            "Accept": "text/html,application/json,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9,ko;q=0.8,ja;q=0.7,zh-CN;q=0.6,zh;q=0.5",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Pragma": "no-cache",
        }

        async with requests.AsyncSession(impersonate="chrome124") as session:
            response = await session.get(
                url,
                headers=headers,
                timeout=25,
                allow_redirects=True,
                verify=True,
            )

            response.raise_for_status() # Raise an exception for bad status codes

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(response.text)

            print(f"Successfully fetched HTML to {output_file}")
            return True

    except Exception as e:
        print(f"Failed to fetch HTML: {e}")
        return False

if __name__ == "__main__":
    buywisely_url = "https://www.buywisely.com.au/product/motorola-moto-g75-5g-256gb-grey-with-buds"
    output_file = os.path.join(os.path.dirname(__file__), "buywisely_fetched.html")
    asyncio.run(fetch_html_for_test(buywisely_url, output_file))
