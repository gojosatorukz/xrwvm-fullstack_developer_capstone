"""VADER sentiment service using the lexicon bundled with the course."""
from pathlib import Path
from zipfile import ZipFile
from flask import Flask, jsonify
from nltk.sentiment import SentimentIntensityAnalyzer

app = Flask(__name__)
lexicon_archive = Path(__file__).parent / 'sentiment' / 'vader_lexicon.zip'
lexicon_dir = Path(__file__).parent / '.lexicon'
lexicon_file = lexicon_dir / 'vader_lexicon.txt'
if not lexicon_file.exists():
    lexicon_dir.mkdir(exist_ok=True)
    with ZipFile(lexicon_archive) as archive:
        lexicon_file.write_bytes(archive.read('vader_lexicon/vader_lexicon.txt'))
sia = SentimentIntensityAnalyzer(lexicon_file=str(lexicon_file))


@app.get('/')
def home():
    return jsonify(service='BestCars sentiment analyzer', ready=True)


@app.get('/analyze/<path:input_txt>')
def analyze_sentiment(input_txt):
    if len(input_txt) > 5000:
        return jsonify(error='Review is too long.'), 400
    compound = sia.polarity_scores(input_txt)['compound']
    sentiment = 'positive' if compound >= 0.05 else 'negative' if compound <= -0.05 else 'neutral'
    return jsonify(sentiment=sentiment)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050)
