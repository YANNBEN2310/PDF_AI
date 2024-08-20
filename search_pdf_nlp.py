import os
import fitz  # PyMuPDF
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from flask import session
import spacy

nlp = spacy.load("en_core_web_sm")

def search_pdfs_in_folder(keyword, folder_path):
    matched_pdfs = []
    total_files = 0

    keyword = keyword.lower()  # Convert the keyword to lowercase

    # Count the total number of PDF files first
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(".pdf"):
                total_files += 1

    if total_files == 0:
        session['progress'] = 100  # No PDFs found, so progress is complete
        return matched_pdfs

    # Update the session with the total number of files
    session['total_files'] = total_files

    processed_files = 0

    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if not file.lower().endswith(".pdf"):
                print(f"Skipped non-PDF file: {file}")
                continue

            pdf_path = os.path.join(root, file)
            try:
                text, pages = extract_text_from_pdf(pdf_path)
                text = text.lower()  # Convert text to lowercase
                print(f"Extracted text from {file}: {len(text)} characters")
            except Exception as e:
                print(f"Error extracting text from {file}: {e}")
                continue
            
            if text:
                # Direct string matching as a debug check
                if keyword in text:
                    print(f"Keyword '{keyword}' found in {file}.")
                
                score, matching_pages = calculate_similarity(keyword, text, pages)
                print(f"Calculated similarity for {file}: Best Score = {score}, Matching Pages = {matching_pages}")
                
                if score >= 0.0:  # Set this to the appropriate threshold
                    matched_pdfs.append({
                        "filename": file,
                        "path": pdf_path,
                        "score": score,
                        "pages": matching_pages,
                        "total_pages": len(pages)
                    })

            processed_files += 1
            session['processed_files'] = processed_files
            session['progress'] = (processed_files / total_files) * 100
            session.modified = True  # Ensure session updates are saved

    session['progress'] = 100
    return matched_pdfs

def extract_text_from_pdf(pdf_path):
    try:
        document = fitz.open(pdf_path)
        text = ""
        pages = []

        for page_num in range(len(document)):
            page = document.load_page(page_num)
            page_text = page.get_text("text")
            text += page_text
            pages.append(page_text)

        return text, pages
    except Exception as e:
        print(f"Error extracting text from PDF {pdf_path}: {str(e)}")
        return "", []

def calculate_similarity(keyword, text, pages):
    try:
        # Convert everything to lowercase for case-insensitivity
        keyword = keyword.lower()
        pages = [page.lower() for page in pages]

        # Direct match checking
        if keyword in text:
            print(f"Keyword '{keyword}' found directly in the text.")

        # Use TfidfVectorizer to calculate similarity
        vectorizer = TfidfVectorizer().fit_transform([keyword] + pages)
        vectors = vectorizer.toarray()
        cosine_matrix = cosine_similarity(vectors)
        similarity_scores = cosine_matrix[0, 1:]

        # Detect pages with high similarity
        matching_pages = [i + 1 for i, score in enumerate(similarity_scores) if score >= 0.0]  # Match all pages
        best_score = max(similarity_scores)

        return best_score, matching_pages
    except Exception as e:
        print(f"Error calculating similarity: {str(e)}")
        return 0, []

# Example keyword match handling
def process_pdf_file(pdf_path, keyword):
    try:
        text, pages = extract_text_from_pdf(pdf_path)
        if text:
            # Direct string matching for keyword occurrence
            if keyword.lower() in text.lower():
                print(f"Keyword '{keyword}' found directly in {os.path.basename(pdf_path)}.")
            
            # Calculate similarity
            score, matching_pages = calculate_similarity(keyword, text, pages)
            if score >= 0.0:  # Match all relevant results
                return {
                    "filename": os.path.basename(pdf_path),
                    "path": pdf_path,
                    "score": score,
                    "pages": matching_pages,
                    "total_pages": len(pages)
                }
    except Exception as e:
        print(f"Error processing PDF file {pdf_path}: {str(e)}")
    return None
