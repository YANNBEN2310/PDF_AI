from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory
import fitz  # PyMuPDF
import spacy
from transformers import pipeline
import os
from pdf_analysis import extract_text_from_pdf, extract_images_from_pdf, count_words, plot_word_occurrences, generate_word_cloud, plot_sentence_similarities, lda_classification

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'

# Load SpaCy model for French
nlp = spacy.load("fr_core_news_sm")

# Load different models for different tasks
qa_pipeline = pipeline("question-answering", model="deepset/roberta-base-squad2")
summarization_pipeline = pipeline("summarization", model="facebook/bart-large-cnn")

def get_named_entities(text):
    doc = nlp(text)
    entities = {ent.label_: ent.text for ent in doc.ents}
    return entities

def answer_question_with_ner(question, entities):
    if "nom du client" in question.lower():
        return entities.get("ORG", "Information not found")
    elif "adresse" in question.lower():
        return entities.get("LOC", "Information not found")
    elif "date" in question.lower():
        return entities.get("DATE", "Information not found")
    return None

def answer_question(question, context, entities):
    if not context:
        return "Context is empty, unable to answer the question."
    
    ner_answer = answer_question_with_ner(question, entities)
    if ner_answer:
        return ner_answer

    result = qa_pipeline(question=question, context=context)
    return result['answer']

def chunk_text(text, chunk_size=512):
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunks.append(text[i:i+chunk_size])
    return chunks

def summarize_text(text):
    chunks = chunk_text(text)
    summaries = []
    for chunk in chunks:
        summary = summarization_pipeline(chunk, max_length=min(len(chunk)//2, 130), min_length=30, do_sample=False)
        summaries.append(summary[0]['summary_text'])
    return " ".join(summaries)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        
        action = request.form.get('action')
        if action == 'talk':
            return redirect(url_for('chat', pdf_path=file.filename))
        elif action == 'analyse':
            return redirect(url_for('analyse', pdf_path=file.filename))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/chat')
def chat():
    pdf_path = request.args.get('pdf_path')
    return render_template('chat.html', pdf_path=pdf_path)

@app.route('/chat', methods=['POST'])
def chat_post():
    data = request.json
    question = data.get('question')
    pdf_path = data.get('pdf_path')
    context = extract_text_from_pdf(os.path.join(app.config['UPLOAD_FOLDER'], pdf_path))
    if not context:
        return jsonify({'answer': "Could not extract text from the PDF."})
    
    entities = get_named_entities(context)
    
    if "résumé" in question.lower() or "resume" in question.lower():
        answer = summarize_text(context)
    else:
        answer = answer_question(question, context, entities)
    
    return jsonify({'answer': answer})

@app.route('/analyse')
def analyse():
    pdf_path = request.args.get('pdf_path')
    if not pdf_path:
        return redirect(url_for('index'))
    
    pdf_full_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_path)
    text = extract_text_from_pdf(pdf_full_path)
    word_counts = count_words(text)
    total_words = sum(word_counts.values())
    
    images = extract_images_from_pdf(pdf_full_path)
    total_images = len(images)
    
    word_occurrences_plot = plot_word_occurrences(word_counts)
    word_cloud_plot = generate_word_cloud(word_counts)
    sentence_similarities_plot = plot_sentence_similarities(text)
    lda_plot = lda_classification(text)
    
    return render_template('analyse.html', total_words=total_words, total_images=total_images,
                           images=images, word_occurrences_plot=word_occurrences_plot,
                           word_cloud_plot=word_cloud_plot, sentence_similarities_plot=sentence_similarities_plot,
                           lda_plot=lda_plot)

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)
