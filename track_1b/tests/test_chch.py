from datetime import UTC, datetime

from newcomer_qa.chch import Passage, parse_page

URL = "https://www.example.ch/de/wohnen/umzug/"

HTML = """<!doctype html><html lang="de"><head>
<script type="application/ld+json">{"@graph": [{"@type": "WebSite"}, {"@type": "WebPage", "dateModified": "2025-07-30T06:30:42.439Z"}]}</script>
</head><body>
<ul><li><a class="uppercase" href="/de/wohnen/umzug/">DE</a></li>
<li><a class="uppercase" href="/fr/logement/demenagement/">FR</a></li></ul>
<div data-component="title"><h1>Moving house</h1></div>
<div data-component="lead"><p>Tell the  commune
 when you move.</p></div>
<div data-component="infobox">Note<div data-component="p"><div>Register within 14 days.</div>
<div><ul style="display:none;"><li><a href="https://canton-a.example/">Register online</a></li></ul>
<ul style="display:none;"><li><a href="https://canton-b.example/">Register online</a></li></ul></div></div></div>
<div data-component="collapsible"><button>Open all</button>
  <div class="accordion-item"><label><span>In person</span><span class="icon-plus"></span></label>
    <div><div data-component="p"><div>Bring these documents:</div></div>
    <div data-component="list"><ul><li><p>Passport</p></li><li><p>Rental contract</p></li></ul></div></div>
  </div>
</div>
<div data-component="list"><ul><li><a href="/de/related/">Related page</a></li><li><a href="/de/other/">Other page</a></li></ul></div>
<div data-component="subtitle"><h2>Empty section</h2></div>
<div data-component="p"><div>   </div></div>
</body></html>"""


def test_parse_page_keeps_reading_order_and_the_nearest_heading():
    page = parse_page(HTML, URL)

    assert page.lang == "de"
    assert page.title == "Moving house"
    assert page.modified_at == datetime(2025, 7, 30, 6, 30, 42, 439000, tzinfo=UTC)
    assert page.passages == [
        Passage(heading="Moving house", text="Tell the commune when you move."),
        Passage(heading="Moving house", text="Register within 14 days."),
        Passage(heading="In person", text="Bring these documents:\nPassport\nRental contract"),
    ]


def test_parse_page_resolves_language_switcher_links():
    assert parse_page(HTML, URL).alternates == {
        "de": "https://www.example.ch/de/wohnen/umzug/",
        "fr": "https://www.example.ch/fr/logement/demenagement/",
    }
