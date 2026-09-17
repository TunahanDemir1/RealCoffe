import json
import requests
from bs4 import BeautifulSoup
from database import save_scraped_data

class KahhveComScraper:
    def __init__(self):
        self.base_url = "https://kahhve.com"
        self.target_url = "https://kahhve.com/kahveler"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "tr-TR,tr;q=0.9"
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
                    break
            except Exception as e:
                print(f"Hata oluştu: {e}")
                break

            soup = BeautifulSoup(response.content, "html.parser")
            product_divs = soup.find_all("div", class_=lambda c: c and "productsImpressions" in c)
            
            # Sayfada ürün kalmadıysa döngüyü sonlandır
            if not product_divs:
                print("Daha fazla ürün bulunamadı, tarama bitti.")
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
                    products_list.append({
                        "platform": "KahhveCom",
                        "title": title,
                        "roaster": brand,
                        "weight_g": 250,
                        "price": price,
                        "url": prod_url,
                        "in_stock": True
                    })

        return products_list

if __name__ == "__main__":
    scraper = KahhveComScraper()
    print("kahhve.com üzerinden çok sayfalı canlı veri çekiliyor...")
    # İlk 5 sayfayı çekmek için:
    products = scraper.scrape(max_pages=7)
    
    if products:
        print(f"Toplam {len(products)} adet ürün ayrıştırıldı.")
        save_scraped_data(products)
    else:
        print("Ürün bulunamadı.")