from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory, session
from werkzeug.utils import secure_filename
import os
import spacy
import traceback
from pdf_analysis import extract_text_from_pdf
from search_pdf_nlp import search_pdfs_in_folder

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024 * 1024  # 5 GB limit
app.secret_key = 'your_secret_key'  # Required for session management

# Load SpaCy model for French
nlp = spacy.load("fr_core_news_sm")

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
    if file and file.filename.lower().endswith('.pdf'):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        action = request.form.get('action')
        if action == 'talk':
            return redirect(url_for('chat', pdf_path=filename))
        elif action == 'analyse':
            return redirect(url_for('analyse', pdf_path=filename))
    else:
        return "Only PDF files are allowed.", 400

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/chat')
def chat():
    pdf_path = request.args.get('pdf_path')
    return render_template('chat.html', pdf_path=pdf_path)

@app.route('/analyse')
def analyse():
    pdf_path = request.args.get('pdf_path')
    if not pdf_path:
        return redirect(url_for('index'))
    
    pdf_full_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_path)
    text = extract_text_from_pdf(pdf_full_path)
    # Further analysis omitted for brevity
    return render_template('analyse.html')

@app.route('/search_pdfs', methods=['POST'])
def search_pdfs():
    try:
        # Get keyword from the form data
        keyword = request.form.get('keyword')
        files = request.files.getlist('pdf_folder')

        if not keyword or not files:
            print("Error: Folder path or keyword missing.")
            return jsonify({"error": "Folder path and keyword are required"}), 400

        print(f"Keyword received: {keyword}")

        # Save each uploaded PDF file to the uploads folder and process them
        for file in files:
            if not file.filename.lower().endswith('.pdf'):
                print(f"Skipped non-PDF file: {file.filename}")
                continue

            filename = secure_filename(file.filename)
            subdir_path = os.path.join(app.config['UPLOAD_FOLDER'], os.path.dirname(filename))
            os.makedirs(subdir_path, exist_ok=True)

            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(pdf_path)
            print(f"PDF saved to: {pdf_path}")

        # Call the search function to process all PDFs in the uploads folder
        matched_pdfs = search_pdfs_in_folder(keyword, app.config['UPLOAD_FOLDER'])
        session['results'] = matched_pdfs  # Save results in session
        print(f"Matched PDFs: {matched_pdfs}")

        if not matched_pdfs:
            print("No PDFs matched the search criteria.")
            return jsonify({"message": "No matches found."}), 200

        return jsonify({"message": "Search completed"}), 200

    except Exception as e:
        print(f"Error during search: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/search_results')
def search_results():
    results = session.get('results', [])
    return render_template('pdf_search_result.html', results=results)

@app.route('/progress')
def progress():
    return jsonify({
        "progress": session.get('progress', 0),
        "processed_files": session.get('processed_files', 0),
        "total_files": session.get('total_files', 0)
    })

@app.route('/view_pdf/<path:filename>')
def view_pdf(filename):
    pdf_url = url_for('uploaded_file', filename=filename)
    return render_template('view_pdf.html', pdf_url=pdf_url)

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)
