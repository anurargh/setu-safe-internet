import os
from flask import Flask, render_template, request, redirect, url_for, session
import google.generativeai as genai
import datetime
import requests
import xml.etree.ElementTree as ET

# --- Configuration ---
genai.configure(api_key="AIzaSyCyNbqv1AhKyBMlkVFM5zD9fskfpAQyRX4") 
model = genai.GenerativeModel('models/gemini-2.0-flash')

app = Flask(__name__)
app.secret_key = 'supersecretkeyforhackathon'

# --- Data Storage (for demo purposes, in-memory) ---
parent_dashboard_data = {
    'queries': [], # Stores dicts: {'query', 'age', 'status', 'explanation', 'citation', 'alternatives', 'timestamp'}
    'risky_count': 0,
    'blocked_count': 0
}

# --- PubMed API Functions ---
def search_pubmed(query_keywords):
    """
    Searches PubMed using ESearch API for relevant articles.
    Returns a list of PubMed IDs (PMIDs).
    """
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    esearch_url = f"{base_url}esearch.fcgi?db=pubmed&term={query_keywords}&retmax=3&sort=relevance"
    
    try:
        response = requests.get(esearch_url, timeout=5)
        response.raise_for_status() # Raise an exception for HTTP errors
        
        root = ET.fromstring(response.content)
        pmids = [id_elem.text for id_elem in root.findall(".//IdList/Id")]
        return pmids
    except requests.exceptions.RequestException as e:
        print(f"PubMed ESearch API error: {e}")
        return []
    except ET.ParseError as e:
        print(f"PubMed ESearch XML parse error: {e}")
        return []

def fetch_pubmed_details(pmids):
    """
    Fetches details for given PubMed IDs using EFetch API.
    Returns a list of dictionaries with citation details.
    """
    if not pmids:
        return []

    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    efetch_url = f"{base_url}efetch.fcgi?db=pubmed&id={','.join(pmids)}&retmode=xml"

    citations = []
    try:
        response = requests.get(efetch_url, timeout=10)
        response.raise_for_status() # Raise an exception for HTTP errors
        
        root = ET.fromstring(response.content)
        for article in root.findall(".//PubmedArticle"):
            # Extract basic info
            title_elem = article.find(".//ArticleTitle")
            title = title_elem.text.strip() if title_elem is not None and title_elem.text else "N/A"

            authors = []
            for author_elem in article.findall(".//AuthorList/Author"):
                last_name_elem = author_elem.find("LastName")
                initials_elem = author_elem.find("Initials")
                if last_name_elem is not None and last_name_elem.text:
                    author_name = last_name_elem.text
                    if initials_elem is not None and initials_elem.text:
                        author_name += f" {initials_elem.text}"
                    authors.append(author_name)
            
            journal_elem = article.find(".//Journal/Title")
            journal = journal_elem.text.strip() if journal_elem is not None and journal_elem.text else "N/A"

            pub_year_elem = article.find(".//PubDate/Year")
            pub_year = pub_year_elem.text.strip() if pub_year_elem is not None and pub_year_elem.text else "N/A"
            
            pmid_elem = article.find(".//PMID")
            pmid = pmid_elem.text.strip() if pmid_elem is not None and pmid_elem.text else ""
            pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "N/A"

            citations.append({
                "title": title,
                "authors": ", ".join(authors) if authors else "N/A",
                "journal": journal,
                "year": pub_year,
                "url": pubmed_url
            })
        return citations
    except requests.exceptions.RequestException as e:
        print(f"PubMed EFetch API error: {e}")
        return []
    except ET.ParseError as e:
        print(f"PubMed EFetch XML parse error: {e}")
        return []


# --- AI Interaction Function ---
def evaluate_query_with_ai(child_query, child_age):
    # Step 1: AI evaluates and suggests keywords if needed
    prompt = f"""
    Evaluate the following internet search query from a child and determine its safety.
    Child's age: {child_age} years old.
    Search query: "{child_query}"

    Determine if the query is "Allowed", "Risky", or "Blocked".
    
    If "Allowed", provide up to 3 safe alternative website suggestions related to the query.
    If "Risky" or "Blocked", provide a short explanation (1-2 sentences) about why it's unsafe. 
    Crucially, also suggest 3-5 concise, relevant keywords that could be used to find supporting *academic research* on topics related to the safety or developmental appropriateness of this query. Separate keywords with commas.

    Example Allowed Output:
    Status: Allowed
    Explanation: This query is generally safe for a {child_age}-year-old.
    Keywords: N/A
    Alternatives: ["https://www.examplekidslearning.com", "https://www.safekidsscience.org"]

    Example Risky Output:
    Status: Risky
    Explanation: This query could lead to content inappropriate for a {child_age}-year-old, potentially impacting psychological development.
    Keywords: child psychology, internet safety for children, developmental appropriateness, adolescent risk behavior
    Alternatives: N/A

    Example Blocked Output:
    Status: Blocked
    Explanation: This query is highly likely to expose a {child_age}-year-old to sexually explicit material, posing severe risks to child welfare.
    Keywords: child sexual abuse prevention, internet filtering effectiveness, child online protection, explicit content exposure
    Alternatives: N/A

    Your response should strictly follow this format, including "N/A" for missing fields.
    """

    ai_status = "Unknown"
    ai_explanation = "Could not parse AI response."
    ai_keywords = "N/A"
    ai_alternatives = []

    try:
        response = model.generate_content(prompt)
        text_response = response.text.strip()
        
        lines = text_response.split('\n')
        for line in lines:
            if line.startswith("Status:"):
                ai_status = line.split(":", 1)[1].strip()
            elif line.startswith("Explanation:"):
                ai_explanation = line.split(":", 1)[1].strip()
            elif line.startswith("Keywords:"):
                ai_keywords = line.split(":", 1)[1].strip()
            elif line.startswith("Alternatives:"):
                alt_str = line.split(":", 1)[1].strip()
                if alt_str != "N/A" and alt_str.startswith('[') and alt_str.endswith(']'):
                    try:
                        ai_alternatives = eval(alt_str) # Safely evaluate list string
                    except:
                        ai_alternatives = [alt_str] # Fallback if eval fails
        
        # Step 2: If Risky/Blocked, search PubMed for real citations
        final_citation_info = "N/A"
        if ai_status in ["Risky", "Blocked"] and ai_keywords != "N/A":
            pubmed_pmids = search_pubmed(ai_keywords)
            if pubmed_pmids:
                pubmed_citations = fetch_pubmed_details(pubmed_pmids[:1]) # Get details for the top 1 result
                if pubmed_citations:
                    # Format a single citation from PubMed
                    cite = pubmed_citations[0]
                    final_citation_info = f"{cite['authors']} ({cite['year']}), {cite['title']} - {cite['journal']}, {cite['url']}"
            
        return ai_status, ai_explanation, final_citation_info, ai_alternatives

    except Exception as e:
        print(f"Error in evaluate_query_with_ai: {e}")
        return "Error", "Failed to process query due to AI/API error.", "N/A", []

# --- Routes ---

@app.route('/', methods=['GET', 'POST'])
def index():
    query_result = None
    if request.method == 'POST':
        child_query = request.form['query'].strip()
        child_age = int(request.form['age'])

        if not child_query:
            query_result = {
                'status': 'Error',
                'explanation': 'Query cannot be empty.',
                'citation': 'N/A',
                'alternatives': []
            }
        else:
            status, explanation, citation, alternatives = evaluate_query_with_ai(child_query, child_age)
            query_result = {
                'status': status,
                'explanation': explanation,
                'citation': citation,
                'alternatives': alternatives
            }

            # Log to parent dashboard
            log_entry = {
                'query': child_query,
                'age': child_age,
                'status': status,
                'explanation': explanation,
                'citation': citation,
                'alternatives': alternatives,
                'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            parent_dashboard_data['queries'].append(log_entry)

            if status == "Risky":
                parent_dashboard_data['risky_count'] += 1
            elif status == "Blocked":
                parent_dashboard_data['blocked_count'] += 1

    return render_template('index.html', query_result=query_result)

@app.route('/dashboard')
def dashboard():
    total_risky_blocked = parent_dashboard_data['risky_count'] + parent_dashboard_data['blocked_count']
    alert_message = "Child's browsing is clean"
    if total_risky_blocked > 10:
        alert_message = "Unsafe pattern detected"

    return render_template(
        'dashboard.html',
        data=parent_dashboard_data['queries'],
        risky_count=parent_dashboard_data['risky_count'],
        blocked_count=parent_dashboard_data['blocked_count'],
        alert_message=alert_message
    )

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)