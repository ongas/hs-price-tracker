
import re
import json
import logging

_LOGGER = logging.getLogger(__name__)

class NextJSHydrationDataExtractor:
    """
    Extracts Next.js hydration data from HTML, supporting both legacy <script id="__NEXT_DATA__"> and new self.__next_f.push formats.
    """
    def parse(self, html: str):
        print("[DIAG][NextJSHydrationDataExtractor] parse() called", flush=True)
        results = []
        print(f"[DIAG][NextJSHydrationDataExtractor] HTML input: {html}", flush=True)
        next_data = re.findall(r'<script[^>]*id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>', html, re.DOTALL)
        print(f"[DIAG][NextJSHydrationDataExtractor] Regex match for __NEXT_DATA__: {next_data}", flush=True)
        if not next_data:
            print(f"[DIAG][NextJSHydrationDataExtractor] No match for minimal regex. HTML length: {len(html)}", flush=True)
            # Try a more permissive regex
            next_data = re.findall(r'<script[^>]*id=["\']__NEXT_DATA__["\'][^>]*>([\s\S]*?)</script>', html, re.DOTALL)
            print(f"[DIAG][NextJSHydrationDataExtractor] Regex match for permissive regex: {next_data}", flush=True)
        print(f"[DIAG][NextJSHydrationDataExtractor] HTML input: {html}", flush=True)
        next_data = re.findall(r'<script[^>]*id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>', html, re.DOTALL)
        print(f"[DIAG][NextJSHydrationDataExtractor] Regex match for __NEXT_DATA__: {next_data}", flush=True)
        if not next_data:
            print(f"[DIAG][NextJSHydrationDataExtractor] No match for minimal regex. HTML length: {len(html)}", flush=True)
            # Try a more permissive regex
            next_data = re.findall(r'<script[^>]*id=["\']__NEXT_DATA__["\'][^>]*>([\s\S]*?)</script>', html, re.DOTALL)
            print(f"[DIAG][NextJSHydrationDataExtractor] Regex match for permissive regex: {next_data}", flush=True)
        if not next_data:
            # Try matching even if attributes are in different order or with newlines
            next_data = re.findall(r'<script[^>]*id=["\']__NEXT_DATA__["\'][^>]*type=["\']application/json["\'][^>]*>(.*?)</script>', html, re.DOTALL | re.IGNORECASE)
            _LOGGER.info(f"[DIAG][NextJSHydrationDataExtractor] Regex match for __NEXT_DATA__ with type after id: {next_data}")
        if not next_data:
            # Try matching with type before id
            next_data = re.findall(r'<script[^>]*type=["\']application/json["\'][^>]*id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>', html, re.DOTALL | re.IGNORECASE)
            _LOGGER.info(f"[DIAG][NextJSHydrationDataExtractor] Regex match for __NEXT_DATA__ with type before id: {next_data}")
        print(f"[DIAG][NextJSHydrationDataExtractor] Matched legacy __NEXT_DATA__ scripts: {len(next_data)}")
        import html as html_lib
        for idx, script in enumerate(next_data):
            print(f"[DIAG][NextJSHydrationDataExtractor] Legacy script {idx}: {script[:200]}...")
            try:
                # Unescape HTML entities and strip whitespace
                cleaned = html_lib.unescape(script).strip()
                data = json.loads(cleaned)
                results.append(data)
            except Exception as e:
                print(f"[DIAG][NextJSHydrationDataExtractor] Failed to parse legacy script {idx}: {e}")
                continue
        # New: <script>self.__next_f.push([1,"33:{...}"])</script>
        push_scripts = re.findall(r'self\.__next_f\.push\((\[.*?\])\)', html, re.DOTALL)
        print(f"[DIAG][NextJSHydrationDataExtractor] Matched self.__next_f.push scripts: {len(push_scripts)}")
        for idx, push in enumerate(push_scripts):
            print(f"[DIAG][NextJSHydrationDataExtractor] Push script {idx}: {push[:200]}...")
            try:
                arr = json.loads(push)
                # arr[1] is like '33:{...}'
                if len(arr) > 1 and isinstance(arr[1], str) and ':' in arr[1]:
                    chunk_id, json_str = arr[1].split(':', 1)
                    data = json.loads(json_str)
                    results.append({
                        'chunk_id': str(arr[0]),
                        'extracted_data': [{
                            'type': 'colon_separated',
                            'identifier': chunk_id,
                            'data': data
                        }],
                        'chunk_count': 1,
                        '_positions': [html.find(push)]
                    })
            except Exception as e:
                print(f"[DIAG][NextJSHydrationDataExtractor] Failed to parse push script {idx}: {e}")
                continue
        return results
