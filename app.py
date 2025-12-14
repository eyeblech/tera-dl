# tera-dl.py - Ultimate Terabox Downloader with Retries, Longer Timeout, & Resume
import requests
import sys
import json
import time
import os
from datetime import datetime
from tqdm import tqdm  # pip install tqdm for progress bars
import random  # For jitter in retries

# ANSI color codes for beautiful output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Your cookie (kept private and built-in)
COOKIES = "ndus=YOUR_NDUS_VALUE"
API_URL = "https://terasnap.netlify.app/api/download"

def print_header(msg, color=Colors.OKCYAN):
    print(f"{color}{Colors.BOLD}{msg}{Colors.ENDC}")

def print_success(msg):
    print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {msg}{Colors.ENDC}")

def print_warning(msg):
    print(f"{Colors.WARNING}⚠ {msg}{Colors.ENDC}")

def print_error(msg):
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {msg}{Colors.ENDC}")

def get_direct_link(terabox_url):
    payload = {
        "link": terabox_url.strip(),
        "cookies": COOKIES
    }

    try:
        print(f"{Colors.OKBLUE}Fetching direct download link...{Colors.ENDC}")
        response = requests.post(API_URL, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.HTTPError as e:
        print_error(f"API Error: {e}")
        print_warning("Server response: " + response.text[:500] + "..." if len(response.text) > 500 else response.text)
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print_error(f"Network error: {e}")
        sys.exit(1)
    except json.JSONDecodeError:
        print_error("Invalid JSON received from server.")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)

def download_with_retry(url, file_name, max_retries=3, use_proxy=False):
    if use_proxy:
        print_warning("Using proxy link (may be slower but more stable).")
    
    for attempt in range(1, max_retries + 1):
        try:
            return download_file(url, file_name, use_proxy)
        except requests.exceptions.ReadTimeout:
            print_warning(f"Timeout on attempt {attempt}/{max_retries}. Retrying in {2 ** (attempt - 1)}s...")
            if attempt < max_retries:
                time.sleep(2 ** (attempt - 1) + random.uniform(0, 1))  # Exponential backoff + jitter
            else:
                raise  # Re-raise on final failure
        except requests.exceptions.RequestException as e:
            if attempt < max_retries:
                print_warning(f"Request error on attempt {attempt}/{max_retries}: {e}. Retrying...")
                time.sleep(2 ** (attempt - 1) + random.uniform(0, 1))
            else:
                raise

def download_file(url, file_name, use_proxy=False):
    start_time = time.time()
    file_path = os.path.abspath(file_name)
    resume_byte_pos = 0
    
    # Resume capability: Check if partial file exists
    if os.path.exists(file_path):
        resume_byte_pos = os.path.getsize(file_path)
        if resume_byte_pos == 0:
            print_warning(f"Empty file '{file_name}' found. Starting fresh.")
            resume_byte_pos = 0
        else:
            print_warning(f"Resuming '{file_name}' from {resume_byte_pos / (1024*1024):.2f} MB...")
    
    print(f"\n{Colors.HEADER}Starting download: {file_name}{Colors.ENDC}")
    
    try:
        headers = {}
        if resume_byte_pos > 0:
            headers['Range'] = f'bytes={resume_byte_pos}-'
        
        response = requests.get(url, headers=headers, stream=True, timeout=120)  # Increased to 120s
        response.raise_for_status()
        
        # Get total size (adjust for resume)
        total_size = int(response.headers.get('content-length', 0)) + resume_byte_pos
        content_range = response.headers.get('content-range', '')
        if content_range:
            # Parse full size from Content-Range header (e.g., bytes 0-999/1234)
            total_size = int(content_range.split('/')[-1]) if '/' in content_range else total_size
        
        block_size = 8192  # 8 KB for better performance
        
        mode = 'ab' if resume_byte_pos > 0 else 'wb'  # Append for resume
        
        with open(file_path, mode) as file, tqdm(
            desc=file_name,
            total=total_size,
            initial=resume_byte_pos,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
            bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{eta}, {rate_fmt}{postfix}]',
            colour='green'
        ) as progress_bar:
            for data in response.iter_content(block_size):
                size = len(data)
                if size == 0:
                    break  # End of stream
                file.write(data)
                progress_bar.update(size)
        
        end_time = time.time()
        duration = end_time - start_time
        
        if total_size != 0 and progress_bar.n != total_size:
            print_error("Download incomplete! Partial file saved (try resuming).")
        else:
            print_success(f"Download complete! Saved as: {file_path}")
            print(f"{Colors.OKBLUE}Time taken: {duration:.2f} seconds{Colors.ENDC}")
            if total_size > 0:
                avg_speed = total_size / duration / 1024
                print(f"{Colors.OKBLUE}Average speed: {avg_speed:.2f} KB/s{Colors.ENDC}")
            
    except requests.exceptions.ReadTimeout:
        print_error("Download timed out (file too large or connection issue).")
        print_warning("Tips: Try proxy option (1), or use aria2c/wget for better handling.")
        raise
    except requests.exceptions.RequestException as e:
        print_error(f"Download error: {e}")
        raise
    except Exception as e:
        print_error(f"Unexpected download error: {e}")
        raise

def display_info(data):
    print("\n" + Colors.BOLD + "═" * 70 + Colors.ENDC)
    print(f"{Colors.HEADER}{Colors.BOLD}              TERABOX FILE READY - Choose Action Below{Colors.ENDC}")
    print(Colors.BOLD + "═" * 70 + Colors.ENDC)

    file_name = data.get("file_name", "Unknown File")
    file_size = data.get("file_size", "Unknown")
    download_link = data.get("download_link") or data.get("direct_link")
    proxy_link = data.get("proxy_url", "")

    print(f"{Colors.OKCYAN}File Name     : {Colors.ENDC}{Colors.BOLD}{file_name}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Size          : {Colors.ENDC}{file_size}")
    print(f"{Colors.OKCYAN}Fetched At    : {Colors.ENDC}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(Colors.BOLD + "─" * 70 + Colors.ENDC)

    if download_link:
        print(f"{Colors.OKGREEN}Direct Link   : {Colors.ENDC}")
        print(f"{download_link}")
        print(f"{Colors.OKBLUE}💡 Tip: Copy to browser, IDM, or use CLI below{Colors.ENDC}")

    if proxy_link:
        print(f"\n{Colors.WARNING}Proxy Link (stable fallback): {Colors.ENDC}")
        print(f"{proxy_link}")

    print(f"\n{Colors.OKBLUE}Quick CLI Downloads:{Colors.ENDC}")
    if download_link:
        print(f"   {Colors.OKGREEN}aria2c --timeout=60 --max-tries=3 --continue=true \"{download_link}\"{Colors.ENDC}")
        print(f"   {Colors.OKGREEN}wget -c --timeout=60 -O \"{file_name}\" \"{download_link}\"{Colors.ENDC}")

    print(Colors.BOLD + "═" * 70 + Colors.ENDC)
    
    return file_name, download_link, proxy_link

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print_error("Missing Terabox link!")
        print(f"{Colors.OKCYAN}Usage:{Colors.ENDC} python tera-dl.py <terabox_link>")
        print(f"{Colors.OKCYAN}Example:{Colors.ENDC} python tera-dl.py https://1024terabox.com/s/1Oyg16qKA0ZhcVSFJ11y35w")
        sys.exit(1)

    link = sys.argv[1].strip()
    if not link.startswith('http'):
        print_error("Invalid URL! Must start with http/https.")
        sys.exit(1)

    data = get_direct_link(link)
    file_name, download_link, proxy_link = display_info(data)

    if not download_link:
        print_error("No direct link found in response. Exiting.")
        sys.exit(1)

    # Interactive choice with beauty
    print(f"\n{Colors.WARNING}{Colors.BOLD}What next?{Colors.ENDC}")
    print(f"{Colors.OKGREEN}0 (Enter){Colors.ENDC} - Download direct (with retries, supports resume)")
    print(f"{Colors.OKBLUE}1{Colors.ENDC} - Download via proxy (more stable for timeouts)")
    print(Colors.BOLD + "─" * 70 + Colors.ENDC)
    
    while True:
        choice = input(f"{Colors.OKBLUE}Enter choice (0/1) [default: 0]: {Colors.ENDC}").strip()
        if choice == '':
            choice = '0'
        
        if choice == '0':
            try:
                download_with_retry(download_link, file_name)
            except Exception:
                print_warning("Direct download failed after retries. Trying proxy...")
                if proxy_link:
                    download_with_retry(proxy_link, file_name, use_proxy=True)
                else:
                    print_error("No proxy available. Use CLI tips above.")
            break
        elif choice == '1':
            if proxy_link:
                try:
                    download_with_retry(proxy_link, file_name, use_proxy=True)
                except Exception:
                    print_error("Proxy download failed. Check your connection or try CLI.")
            else:
                print_error("No proxy link available.")
            break
        else:
            print_warning("Invalid choice! Try 0 or 1.")
