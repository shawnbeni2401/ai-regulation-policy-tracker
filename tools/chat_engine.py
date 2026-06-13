import sqlite3
import re
import os
import urllib.parse
import requests
from html.parser import HTMLParser
import dotenv

# Load environment variables from .env file
dotenv.load_dotenv()

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "policies.db")

class DDGParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.results = []
        self.in_result = False
        self.in_title = False
        self.in_snippet = False
        self.temp_title = ""
        self.temp_snippet = ""
        self.temp_link = ""

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        class_name = attrs_dict.get('class', '')
        
        if tag == 'div' and 'result' in class_name.split():
            self.in_result = True
            self.temp_title = ""
            self.temp_snippet = ""
            self.temp_link = ""
            
        elif tag == 'a' and 'result__a' in class_name.split():
            self.in_title = True
            self.temp_link = attrs_dict.get('href', '')
            
        elif tag == 'a' and 'result__snippet' in class_name.split():
            self.in_snippet = True

    def handle_endtag(self, tag):
        if tag == 'a' and self.in_title:
            self.in_title = False
        elif tag == 'a' and self.in_snippet:
            self.in_snippet = False
            if self.temp_title and self.temp_link:
                link = self.temp_link
                if "uddg=" in link:
                    parts = urllib.parse.parse_qs(urllib.parse.urlparse(link).query)
                    if "uddg" in parts:
                        link = parts["uddg"][0]
                
                self.results.append({
                    "title": self.temp_title.strip(),
                    "link": link,
                    "snippet": self.temp_snippet.strip()
                })
            self.in_result = False

    def handle_data(self, data):
        if self.in_title:
            self.temp_title += data
        elif self.in_snippet:
            self.temp_snippet += data

def search_web_ddg(query):
    url = "https://html.duckduckgo.com/html/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.0.0 Safari/537.36"
    }
    try:
        r = requests.post(url, data={"q": query}, headers=headers, timeout=8)
        parser = DDGParser()
        parser.feed(r.text)
        return parser.results[:4]
    except Exception:
        return []

def query_policies(search_term):
    """Query policies from database matching search term."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = "%" + search_term + "%"
    cursor.execute(
        "SELECT policy_name, jurisdiction, status, last_updated, source_url, summary_ai_generated FROM policies WHERE policy_name LIKE ? OR jurisdiction LIKE ? OR summary_ai_generated LIKE ?",
        (query, query, query)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_all_policies():
    """Get list of all policies in the database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT policy_name, jurisdiction, status FROM policies")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def markdown_to_html(text):
    """Simple parser to convert basic markdown and tags into safe HTML."""
    # Convert headers
    text = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^#### (.*?)$', r'<h4>\1</h4>', text, flags=re.MULTILINE)
    
    # Convert bold text **word** to <strong>word</strong>
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    
    # Convert links [text](url) to <a href="\2" target="_blank" rel="noopener noreferrer">\1</a>
    text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>', text)
    
    # Convert list items - item to <li>item</li>
    lines = text.split('\n')
    in_list = False
    new_lines = []
    for line in lines:
        if line.strip().startswith('- '):
            if not in_list:
                new_lines.append('<ul>')
                in_list = True
            content = line.strip()[2:]
            new_lines.append(f'<li>{content}</li>')
        else:
            if in_list:
                new_lines.append('</ul>')
                in_list = False
            new_lines.append(line)
    if in_list:
        new_lines.append('</ul>')
    text = '\n'.join(new_lines)
    
    # Convert paragraphs
    paragraphs = text.split('\n\n')
    html_paragraphs = []
    for p in paragraphs:
        p_clean = p.strip()
        if p_clean:
            if p_clean.startswith('<h') or p_clean.startswith('<ul') or p_clean.startswith('<details') or p_clean.startswith('</details') or p_clean.startswith('<summary'):
                html_paragraphs.append(p_clean)
            else:
                html_paragraphs.append(f'<p>{p_clean}</p>')
    return '\n'.join(html_paragraphs)

def query_gemini_api(api_key, prompt):
    """Call Google Gemini 2.5 Flash API directly using HTTP POST."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    # Inject system context for AI regulation role
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": f"You are Lexis AI Policy Assistant, a helpful AI regulation expert. Answer the user's question clearly, focusing on AI policy, safety, and legal compliance. Keep formatting clean using standard Markdown.\n\nUser Question: {prompt}"
                    }
                ]
            }
        ]
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=12)
        if r.status_code == 200:
            data = r.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        pass
    return None

def query_openai_api(api_key, prompt):
    """Call OpenAI GPT-4o-Mini model directly using HTTP POST."""
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are Lexis AI Policy Assistant. Answer questions about AI regulations, laws, and compliance. Use clean markdown formatting."},
            {"role": "user", "content": prompt}
        ]
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=12)
        if r.status_code == 200:
            data = r.json()
            return data["choices"][0]["message"]["content"]
    except Exception:
        pass
    return None

def answer_question(user_message):
    """Analyze query and synthesize a detailed answer using API key or fallbacks."""
    msg = user_message.lower().strip()
    
    if not msg:
        return markdown_to_html("Please ask a question, and I'll do my best to search the global AI policy database.")

    # 1. Check for API Keys in environment variables
    gemini_key = os.getenv("GEMINI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if gemini_key:
        ai_response = query_gemini_api(gemini_key, user_message)
        if ai_response:
            return markdown_to_html(ai_response)

    if openai_key:
        ai_response = query_openai_api(openai_key, user_message)
        if ai_response:
            return markdown_to_html(ai_response)

    # 2. Fallback to local SQLite Database search
    search_term = None
    if "eu" in msg or "european" in msg:
        search_term = "EU"
    elif "us" in msg or "united states" in msg or "executive order" in msg:
        search_term = "US"
    elif "uk" in msg or "united kingdom" in msg or "dsit" in msg:
        search_term = "UK"
    elif "india" in msg or "meity" in msg:
        search_term = "India"
    elif "china" in msg or "cac" in msg:
        search_term = "China"
    elif "canada" in msg or "aida" in msg:
        search_term = "Canada"
    elif "oecd" in msg or "global" in msg:
        search_term = "Global"

    policies = []
    if search_term:
        policies = query_policies(search_term)
    else:
        keywords = [w for w in re.split(r'\W+', msg) if len(w) > 3]
        for kw in keywords[:2]:
            policies = query_policies(kw)
            if policies:
                break

    if policies:
        response = []
        response.append(f"### Found {len(policies)} matching policy document(s) in the database:\n")
        for idx, p in enumerate(policies, 1):
            response.append(f"#### {idx}. {p['policy_name']} ({p['jurisdiction']})")
            response.append(f"- **Current Status:** {p['status']}")
            response.append(f"- **Last Synced:** {p['last_updated']}")
            response.append(f"- **Official Portal:** [{p['source_url']}]({p['source_url']})\n")
            
            summary = p['summary_ai_generated']
            paragraphs = [para.strip() for para in summary.split('\n\n') if para.strip()]
            if paragraphs:
                brief = paragraphs[0]
                rest = "\n\n".join(paragraphs[1:])
                response.append(f"{brief}\n")
                if rest:
                    response.append("<details open>")
                    response.append("<summary><b>▼ Click to collapse key points & full details</b></summary>\n")
                    response.append(f"{rest}\n")
                    response.append("</details>\n")
            else:
                response.append(f"{summary}\n")
        return markdown_to_html("\n".join(response))

    # 3. Fallback to real-time DuckDuckGo web search scraper
    web_results = search_web_ddg(user_message)
    if web_results:
        response = []
        response.append(f"### 🌐 Web Search Results: \"{user_message}\"\n")
        
        # Combine snippets from the top 3 results to construct a detailed quick answer
        snippets_list = [r['snippet'].strip() for r in web_results if r['snippet'].strip()]
        combined_summary = " ".join(snippets_list[:3])
        response.append(f"**Comprehensive Summary:** {combined_summary}\n\n")
        
        response.append("<details open>")
        response.append("<summary><b>▼ Click to collapse all sources & key points</b></summary>\n")
        for idx, r in enumerate(web_results, 1):
            response.append(f"{idx}. **[{r['title']}]({r['link']})**")
            response.append(f"   * {r['snippet']}\n")
        response.append("</details>\n")
        
        # Add API Key Guide notice since no API key was configured
        response.append("\n---\n")
        response.append("💡 **Setup advanced AI:** To enable direct AI-generated conversations, create a `.env` file in the folder containing `GEMINI_API_KEY=your_free_key`. Get a free key at [Google AI Studio](https://aistudio.google.com/).")
        return markdown_to_html("\n".join(response))

    # 4. Fallback if both local database and web search returned nothing
    all_p = get_all_policies()
    list_str = "\n".join([f"- **[{p['jurisdiction']}]** {p['policy_name']} *(Status: {p['status']})*" for p in all_p])
    fallback_text = (
        "I couldn't find any specific policies matching your query.\n\n"
        "Here is a list of the global policies currently tracked in the database that you can ask about:\n"
        f"{list_str}\n\n"
        "💡 **Setup advanced AI:** To enable direct AI-generated conversations, create a `.env` file in the folder containing `GEMINI_API_KEY=your_free_key`. Get a free key at [Google AI Studio](https://aistudio.google.com/)."
    )
    return markdown_to_html(fallback_text)

if __name__ == "__main__":
    print(answer_question("can i ai video on youtube"))
