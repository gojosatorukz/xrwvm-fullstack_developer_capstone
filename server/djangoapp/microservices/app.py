"""VADER sentiment service using the lexicon bundled with the course."""
import os
from pathlib import Path
from flask import Flask, jsonify

os.environ.setdefault('NLTK_DATA', str(Path(__file__).resolve().parent))
from nltk.sentiment import SentimentIntensityAnalyzer  # noqa: E402

app = Flask(__name__)
sia = SentimentIntensityAnalyzer()


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
