import requests
from bs4 import BeautifulSoup
import time
import genanki
import random

def scrape_vocab(url):
    base_url = "https://jpdb.io"
    vocab_dict = {}
    deck_name = "JPDB Vocabulary Export test"
    while url:
        response = requests.get(url)
        response.raise_for_status()
        response.encoding = "utf-8"
        soup = BeautifulSoup(response.text, "html.parser")
        body = soup.body
        container_div = body.find("div", class_="container bugfix")
        
        # Get deck name from <h4> if present
        if container_div:
            h4 = container_div.find("h4")
            if h4 and "Vocabulary list:" in h4.text:
                deck_name_candidate = h4.text.split("Vocabulary list:")[-1].strip()
                if deck_name_candidate:
                    deck_name = deck_name_candidate

        vocab_list_div = container_div.find("div", class_="vocabulary-list") if container_div else None
        if vocab_list_div:
            entries = vocab_list_div.find_all("div", class_="entry")
            for entry in entries:
                ruby_tags = entry.find_all("ruby")
                # Build spelling and reading in parallel, character by character
                spelling = ""
                reading_parts = []
                for ruby in ruby_tags:
                    # Get the base text (kanji/kana)
                    base_text = "".join([t for t in ruby.contents if isinstance(t, str)]).strip()
                    rt_tag = ruby.find("rt")
                    spelling += base_text
                    if base_text:
                        if rt_tag:
                            reading_parts.append(f"{base_text}[{rt_tag.get_text(strip=True)}]")
                        else:
                            reading_parts.append(base_text)
                rt_value = "".join(reading_parts) if reading_parts else None

                meaning_divs = entry.find_all("div", recursive=False)
                meaning = None
                if meaning_divs:
                    inner_divs = meaning_divs[0].find_all("div", recursive=False)
                    if len(inner_divs) > 1:
                        meaning = inner_divs[1].get_text(strip=True)
                    else:
                        for div in meaning_divs[0].find_all("div"):
                            text = div.get_text(strip=True)
                            if ";" in text:
                                meaning = text
                                break
                if spelling and meaning:
                    if rt_value is not None:
                        vocab_dict[spelling] = [meaning, rt_value]
                    else:
                        vocab_dict[spelling] = [meaning]
        # Find the next page URL from pagination
        next_url = None
        pagination_div = container_div.find("div", class_="pagination without-prev") \
            or container_div.find("div", class_="pagination")
        if pagination_div:
            a_tags = pagination_div.find_all("a", href=True)
            next_a = None
            for a in a_tags:
                if "Next page" in a.get_text(strip=True):
                    next_a = a
                    break
            if next_a:
                next_url = base_url + next_a["href"]
        if next_url:
            time.sleep(0.5)
        url = next_url
    return vocab_dict, deck_name

def create_anki_deck(vocab_dict, filename, deck_name):
    model_id = random.randint(1, 2**32-1)
    deck_id = random.randint(1, 2**32-1)
    my_model = genanki.Model(
        model_id,
        'Test Model',
        fields=[
            {'name': 'Expression'},
            {'name': 'Reading'},
            {'name': 'Meaning'},
        ],
        templates=[
            {
                'name': 'Recognition',
                'qfmt': """
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: flex-start; padding-top: 2em;">
                    <span style="font-size: 3em;">
                        {{Expression}}
                    </span>
                </div>
                """,
                'afmt': """
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: flex-start; padding-top: 2em;">
                    <span style="font-size: 3em;">
                        {{#Reading}}{{furigana:Reading}}{{/Reading}}
                    </span>
                    <hr id="answer" style="width: 100%;">
                    <span style="font-size: 3em;">
                        {{Meaning}}
                    </span>
                </div>
                """,
            },
        ],
        css="""
        rt {
            font-size: 0.625em;
        }
        """
    )
    my_deck = genanki.Deck(
        deck_id,
        deck_name
    )
    for spelling, value in vocab_dict.items():
        meaning = value[0]
        reading = value[1] if len(value) > 1 else ""
        note = genanki.Note(
            model=my_model,
            fields=[spelling, reading, meaning]
        )
        my_deck.add_note(note)
    genanki.Package(my_deck).write_to_file(filename)