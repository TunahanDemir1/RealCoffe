import json
import re
import requests
from bs4 import BeautifulSoup
from database import save_scraped_data

def extract_weight_grams(title: str, default: int = 250) -> int:
    """
    Ürün başlığından gramaj bilgisini regex ile ayıklar.
    Örnekler:
      - '1 kg', '1kg', '1.5 kg' -> 1000, 1500
      - '500g', '500 gr', '500 gram' -> 500
      - '2x250g', '2 x 250 gr' -> 500
    """
    if not title:
        return default

    clean_title = title.lower()

    # Çoklu paket kontrolü: 2x250g, 3 x 250 gr
    multipack = re.search(r'(\d+)\s*[xX*]\s*(\d+)\s*(?:g|gr|gram)\b', clean_title)
    if multipack:
        count = int(multipack.group(1))
        weight = int(multipack.group(2))
        total = count * weight
        if 50 <= total <= 10000:
            return total

    # Kilogram tespiti: 1 kg, 1.5 kg, 2 kilo
    kg_match = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:kg|kilo)\b', clean_title)
    if kg_match:
        val_str = kg_match.group(1).replace(",", ".")
        try:
            val_kg = float(val_str)
            grams = int(val_kg * 1000)
            if 500 <= grams <= 10000:
                return grams
        except ValueError:
            pass

    # Gram tespiti: 1000 gr, 500g, 250 gram vb.
    g_match = re.search(r'(\d+)\s*(?:g|gr|gram)\b', clean_title)
    if g_match:
        try:
            grams = int(g_match.group(1))
            if 30 <= grams <= 5000:
                return grams
        except ValueError:
            pass

    return default

class KahhveComScraper:
    def __init__(self):
        self.base_url = "https://kahhve.com"
        self.target_url = "https://kahhve.com/kahveler"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://kahhve.com/"
        }

    def scrape(self, max_pages: int = 5) -> list[dict]:
        """
        Belirtilen sayfa adedi kadar gezip tüm ürünleri toplar.
        """
        products_list = []

        for page in range(1, max_pages + 1):
            url = f"{self.target_url}?pg={page}"
            print(f"Sayfa {page} taranıyor: {url}")
            
            try:
                response = requests.get(url, headers=self.headers, timeout=15)
                if response.status_code != 200:
                    print(f"Uyarı: Sayfa {page} HTTP {response.status_code} koduyla döndü.")
                    break
            except Exception as e:
                print(f"Hata oluştu ({url}): {e}")
                break

            soup = BeautifulSoup(response.content, "html.parser")
            product_divs = soup.find_all("div", class_=lambda c: c and "productsImpressions" in c)
            
            # Sayfada ürün kalmadıysa döngüyü sonlandır
            if not product_divs:
                print("Daha fazla ürün bulunamadı, tarama tamamlandı.")
                break

            for div in product_divs:
                raw_data = div.get("data-enhanced")
                if not raw_data:
                    continue
                try:
                    item_data = json.loads(raw_data)
                except Exception:
                    continue

                title = item_data.get("name", "").strip()
                price = float(item_data.get("fiyat", 0.0))
                brand = item_data.get("marka", "Bilinmiyor").strip()

                link_tag = div.find("a", href=True)
                if link_tag:
                    href = link_tag["href"]
                    prod_url = self.base_url + href if href.startswith("/") else href
                else:
                    prod_url = f"{self.base_url}/urun/{item_data.get('id', '')}"

                if title and price > 0:
                    # Gramajı başlıktan akıllıca ayıkla
                    detected_weight = extract_weight_grams(title, default=250)

                    products_list.append({
                        "platform": "KahhveCom",
                        "title": title,
                        "roaster": brand,
                        "weight_g": detected_weight,
                        "price": price,
                        "url": prod_url,
                        "in_stock": True
                    })

        return products_list

if __name__ == "__main__":
    scraper = KahhveComScraper()
    print("kahhve.com üzerinden canlı veri çekiliyor...")
    products = scraper.scrape(max_pages=2)
    
    if products:
        print(f"Toplam {len(products)} adet ürün ayrıştırıldı.")
        save_scraped_data(products)
    else:
        print("Ürün bulunamadı.")