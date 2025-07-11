from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
import csv
import time
import pandas as pd

# Setup Selenium
options = Options()
options.add_argument("--headless")
options.add_argument('--disable-dev-shm-usage')
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--log-level=3")
options.add_argument("--enable-unsafe-swiftshader")

service = Service("./chromedriver.exe")
driver = webdriver.Chrome(service=service, options=options)


def scrape_berita(tag, data):
    page = 1
    while True:
        print(f"[{tag}] Page ke", page)
        url = f"https://www.kompas.com/tag/{tag}?page={page}&type=artikel"
        driver.get(url)

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, "sectionBox"))
        )
        sections = driver.find_elements(By.CLASS_NAME, "sectionBox")

        if len(sections) == 2:
            print(f"[{tag}] Tidak ada artikel baru.")
            break

        main_article = sections[0].find_element(
            By.CSS_SELECTOR, ".articleList.-list")

        list_artikel = main_article.find_elements(By.CLASS_NAME, "articleItem")
        print(f"[{tag}] Jumlah artikel: {len(list_artikel)}")

        for article_item in list_artikel:
            try:
                article = {"tag": tag}
                article["link"] = article_item.find_element(
                    By.TAG_NAME, 'a').get_attribute('href')
                print(f"[{tag}] Link: {article['link']}")
                article["date"] = article_item.find_element(
                    By.CLASS_NAME, 'articlePost-date').text.strip()
                print(f"[{tag}] Tanggal: {article['date']}")
                article["title"] = article_item.find_element(
                    By.CLASS_NAME, 'articleTitle').text.strip()
                print(f"[{tag}] Judul: {article['title']}")

                data.append(article)

            except Exception as e:
                print(f"[{tag}] Error in section parsing: {e}")

        page += 1
        time.sleep(2)


def scrape_article_contents(data):
    for article in data:
        try:
            driver.get(article["link"])

            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )

            title = driver.find_element(
                By.CLASS_NAME, 'read__title').text.strip()

            content_elements = driver.find_element(
                By.CLASS_NAME, 'read__content'
            ).find_elements(By.TAG_NAME, 'p')

            content = ' '.join([
                p.text.strip()
                for p in content_elements
                if not p.text.lower().startswith(('baca juga', '(baca:'))
            ])

            article['title'] = title
            article['content'] = content

        except Exception as e:
            print(f"Gagal mengambil konten dari {article['link']}: {e}")

        time.sleep(2)


def save_to_csv(data, filename):
    fieldnames = ["tag", "title", "link", "date"]
    with open(filename, 'w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            if all(row.get(field) for field in ["title", "link", "date"]):
                writer.writerow(row)
    print(f"✅ Data berhasil disimpan ke {filename}")


def generate_wordcloud_from_csv(filename):
    df = pd.read_csv(filename)
    all_titles = ' '.join(df['title'].dropna().tolist())

    custom_stopwords = set(STOPWORDS)
    custom_stopwords.update(
        ['sepeda', 'rental', 'sewa', 'kompas'])  # kamu bisa ubah ini

    wordcloud = WordCloud(
        width=800,
        height=400,
        background_color='white',
        stopwords=custom_stopwords,
        collocations=False
    ).generate(all_titles)

    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.title('Word Cloud dari Judul Artikel Kompas')
    plt.tight_layout()
    plt.show()

    wordcloud.to_file("wordcloud_title.png")
    print("✅ Word cloud disimpan sebagai 'wordcloud_title.png'")


# =============================
# MAIN PROCESS
# =============================
try:
    all_data = []
    tags = ['rental-sepeda', 'komunitas-sepeda', 'sewa-sepeda',
            'sepeda-onthel', 'sepeda-listrik', 'sepeda-lipat']
    for tag in tags:
        scrape_berita(tag, all_data)

    # scrape_article_contents(all_data)

    filename = "data_sepeda_kompas.csv"
    save_to_csv(all_data, filename)

    # generate_wordcloud_from_csv(filename)

finally:
    driver.quit()
