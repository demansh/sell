import os
import re
import yaml
import logging
from collections import Counter

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

POSTS_DIR = '_posts'
DATA_DIR = '_data'
OUTPUT_FILE = os.path.join(DATA_DIR, 'top_keywords.yml')

# Add any keywords here you want to ignore
BLACKLIST = {'другое', 'разное', 'прочее', 'смартфон'}

def update_top_keywords():
    keyword_counts = Counter()
    
    if not os.path.exists(POSTS_DIR):
        logger.error(f"Directory {POSTS_DIR} not found!")
        return

    os.makedirs(DATA_DIR, exist_ok=True)

    for filename in os.listdir(POSTS_DIR):
        if not filename.endswith(".md"):
            continue
        
        try:
            with open(os.path.join(POSTS_DIR, filename), 'r', encoding='utf-8') as f:
                content = f.read()
                match = re.search(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
                if match:
                    data = yaml.safe_load(match.group(1))
                    keywords = data.get('keywords', [])
                    if isinstance(keywords, list):
                        for k in keywords:
                            clean_k = str(k).strip().lower()
                            if clean_k and clean_k not in BLACKLIST:
                                keyword_counts.update([clean_k])
        except Exception as e:
            logger.warning(f"Could not parse {filename}: {e}")

    # most_common(10) ensures the list never exceeds 10 items
    top_10 = [item[0] for item in keyword_counts.most_common(10)]

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        # allow_unicode=True ensures Russian characters aren't escaped as \uXXXX
        yaml.dump(top_10, f, allow_unicode=True, default_flow_style=False)
    
    logger.info(f"Top 10 updated in {OUTPUT_FILE}: {top_10}")

if __name__ == "__main__":
    update_top_keywords()