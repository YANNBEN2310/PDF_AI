import fitz  # PyMuPDF
from collections import Counter
from wordcloud import WordCloud
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.decomposition import LatentDirichletAllocation as LDA
import numpy as np
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
import re
import plotly.express as px
import plotly.graph_objects as go
import os

# Ensure you have necessary NLTK data
nltk.download('punkt')
nltk.download('stopwords')

def extract_text_from_pdf(pdf_path):
    document = fitz.open(pdf_path)
    text = ""
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        text += page.get_text()
    return text.strip()

def extract_images_from_pdf(pdf_path, output_folder='static/images'):
    document = fitz.open(pdf_path)
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    images = []
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        image_list = page.get_images(full=True)
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = document.extract_image(xref)
            image_bytes = base_image["image"]
            image_filename = f"image_{page_num}_{img_index}.png"
            image_path = os.path.join(output_folder, image_filename)
            with open(image_path, "wb") as img_file:
                img_file.write(image_bytes)
            images.append(image_filename)
    return images

def count_words(text):
    words = word_tokenize(text.lower())
    words = [word for word in words if word.isalpha()]
    stop_words = set(stopwords.words('english'))
    words = [word for word in words if word not in stop_words]
    word_counts = Counter(words)
    return word_counts

def plot_word_occurrences(word_counts):
    most_common_words = word_counts.most_common(20)
    words = [word for word, count in most_common_words]
    counts = [count for word, count in most_common_words]
    fig = px.bar(x=counts, y=words, orientation='h', labels={'x': 'Count', 'y': 'Word'},
                 title='Top 20 Words by Frequency')
    fig.update_layout(yaxis={'categoryorder': 'total ascending'})
    return fig.to_html(full_html=False)

def generate_word_cloud(word_counts):
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate_from_frequencies(word_counts)
    fig = go.Figure(go.Image(z=wordcloud.to_array()))
    fig.update_layout(title='Word Cloud')
    return fig.to_html(full_html=False)

def plot_sentence_similarities(text):
    sentences = sent_tokenize(text)
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(sentences)
    pca = PCA(n_components=3)
    X_reduced = pca.fit_transform(X.toarray())
    
    kmeans = KMeans(n_clusters=5)
    labels = kmeans.fit_predict(X_reduced)
    
    fig = px.scatter_3d(
        x=X_reduced[:, 0], y=X_reduced[:, 1], z=X_reduced[:, 2],
        color=labels, title='3D Plot of Sentence Similarities',
        labels={'x': 'PCA1', 'y': 'PCA2', 'z': 'PCA3'},
        hover_data={'sentence': sentences}
    )
    return fig.to_html(full_html=False)

def lda_classification(text):
    sentences = sent_tokenize(text)
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(sentences)
    
    lda = LDA(n_components=5, random_state=0)
    lda_results = lda.fit_transform(X)
    lda_labels = np.argmax(lda_results, axis=1)
    
    fig = px.scatter_3d(
        x=lda_results[:, 0], y=lda_results[:, 1], z=lda_results[:, 2],
        color=lda_labels, title='3D Plot of LDA Classification',
        labels={'x': 'Topic 1', 'y': 'Topic 2', 'z': 'Topic 3'},
        hover_data={'sentence': sentences}
    )
    return fig.to_html(full_html=False)
