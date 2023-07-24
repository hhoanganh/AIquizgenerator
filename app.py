from flask import Flask, request, render_template, redirect, url_for, g
import openai
import requests
import json
import sqlite3
import re
import datetime
import os
import random

app = Flask(__name__, static_folder='C:/aigenquiz - 2307/static')

# Create a connection to the database
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect("quiz_responses.db")
    return db
# Initialize the database connection outside of the request handling functions
def initialize_database_connection():
    with app.app_context():
        db = get_db()
        db.row_factory = sqlite3.Row  # Set the row_factory to use column names as keys
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS aiquizgen (
                question_id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT,
                category TEXT,
                circumstance TEXT,
                question TEXT,
                answer1 TEXT,
                answer2 TEXT,
                answer3 TEXT,
                correct_answer INTEGER,
                explanation TEXT,
                example TEXT
            )
        ''')
        db.commit()

# Define the function to call OpenAI API
def call_chatgpt_api(prompt):
    api_endpoint = "https://api.openai.com/v1/completions"
    api_key = "sk-xWbuyrYy621Ud9jo4DK4T3BlbkFJI8qhTcopusH9b6....."
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    data = {
    "prompt": prompt,               # The prompt containing your desired text
    "model": "text-davinci-003",    # The model to use for generating the response
    "temperature": 0.8,             # Controls the randomness of the generated response
    "max_tokens": 1000,             # Limits the response to a maximum of 1000 tokens, bởi vì giới hạn của model này là 4000, mà câu prompt đã 1700, và càng gọi ít token càng đỡ tốn tiền
    "top_p": 1,                     # Controls the diversity of the generated response
    "frequency_penalty": 0.8,       # Encourages diverse responses by reducing repetition
    "presence_penalty": 0.6,        # Encourages exploration of different ideas
    "n": 1,                         # Generates a single response
    "stop": ["\n\n\n\"\"\""]        # Specifies a stop sequence to truncate the response
}


    response = requests.post(api_endpoint, headers=headers, json=data)
    response_json = response.json()
    if "error" in response_json and response_json["error"]["code"] == "rate_limit_exceeded":
        return None
    text = response_json['choices'][0]['text'].strip()
    return text

# Define the function to split quiz text
def split_quiz_text(quiz_text):
    parts = {}
    # Category
    match = re.search(r'Category[^:]*:\s*(.*)', quiz_text)
    if match:
        parts['Category'] = match.group(1).strip()
    # Circumstance
    match = re.search(r'Circumstance[^:]*:\s*(.*)', quiz_text)
    if match:
        parts['Circumstance'] = match.group(1).strip()
    # Q
    match = re.search(r'Q[^:]*:\s*(.*)', quiz_text)
    if match:
        parts['Q'] = match.group(1).strip()
    # A1
    match = re.search(r'A[^:]*1[^:]*:\s*(.*)', quiz_text)
    if match:
        parts['A1'] = match.group(1).strip()
    # A2
    match = re.search(r'A[^:]*2[^:]*:\s*(.*)', quiz_text)
    if match:
        parts['A2'] = match.group(1).strip()
    # A3
    match = re.search(r'A[^:]*3[^:]*:\s*(.*)', quiz_text)
    if match:
        parts['A3'] = match.group(1).strip()

    # Correct
    match = re.search(r'Correct[^:]*:\s*(\d+)', quiz_text)
    if match:
        parts['Correct'] = match.group(1).strip()

    # Explanation and Example
    match = re.search(r'Explanation[^:]*:\s*((?:.|\n)*?)(?=\n\n|$)', quiz_text)
    if match:
        explanation = match.group(1).strip()
        example_match = re.search(r'Example[^:]*:\s*((?:.|\n)*?)$', explanation, re.IGNORECASE | re.MULTILINE)
        if example_match:
            parts['Explanation'] = explanation.split(example_match.group(0))[0].strip()
            parts['Example'] = example_match.group(1).strip()
        else:
            parts['Explanation'] = explanation.strip()

    return parts

# Initialize the database connection
initialize_database_connection()

def save_quiz_to_database(quiz_parts, level):
    db = get_db()
    cursor = db.cursor()

    category = quiz_parts['Category']
    circumstance = quiz_parts['Circumstance']
    question = quiz_parts['Q']
    answer1 = quiz_parts['A1']
    answer2 = quiz_parts['A2']
    answer3 = quiz_parts['A3']
    correct_answer = int(''.join(filter(str.isdigit, quiz_parts['Correct'])))
    explanation = quiz_parts['Explanation']
    example = quiz_parts['Example']

    sql = "INSERT INTO aiquizgen (level, category, circumstance, question, answer1, answer2, answer3, correct_answer, explanation, example) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    values = (level, category, circumstance, question, answer1, answer2, answer3, correct_answer, explanation, example)

    # Execute the query with the parameter values
    cursor.execute(sql, values)
    db.commit()

def retrieve_quiz_from_database():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT level, category, circumstance, question, answer1, answer2, answer3, correct_answer, explanation, example FROM aiquizgen ORDER BY rowid DESC LIMIT 1")
    quiz_data = cursor.fetchone()

    cursor.close()

    if quiz_data:
        quiz_parts = {
            'Level': quiz_data[0],
            'Category': quiz_data[1],
            'Circumstance': quiz_data[2],
            'Q': quiz_data[3],
            'A1': quiz_data[4],
            'A2': quiz_data[5],
            'A3': quiz_data[6],
            'Correct': quiz_data[7],
            'Explanation': quiz_data[8],
            'Example': quiz_data[9]
        }
        return quiz_parts
    else:
        return None

# Define the quiz route
@app.route('/')
def index():
    #return render_template("index.html")
    error_message = request.args.get('error_message')
    return render_template("index.html", error_message=error_message)    

# Define start route
@app.route('/start', methods=['POST'])
def start_quiz():
    # Retrieve the selected BA level from the form data
    level = request.form.get('levelText')

    if level:
        # Prompt for generating quiz
        prompt = """
        "I need your help in creating quizzes to test the Business Analyst knowledge, skills, and problem-solving abilities, both Junior and Senior levels.

The Junior's responsibilities primarily focus on learning and gaining practical experience. They assist senior team members in gathering requirements, documenting processes, conducting basic analysis, and supporting the development of business solutions. They may also assist in user acceptance testing and troubleshooting issues. Junior analysts collaborate with various stakeholders, including business users, developers, and quality assurance teams, to gather requirements and ensure that business needs are translated into technical solutions accurately.
The Senior's responsibilities take on leadership roles and are responsible for overseeing complex projects from initiation to implementation. They lead the requirements gathering and analysis processes, facilitate workshops and meetings, conduct in-depth analysis, and provide recommendations for business process improvements. They also play a vital role in translating business needs into technical requirements and ensuring alignment between business and technology teams. Senior analysts provide strategic insights to support decision-making at the organizational level. They have a broader understanding of business goals, industry trends, and emerging technologies. They work closely with stakeholders, including executives and senior management, to align business objectives with technology solutions.
The Junior level must has these skill categories in basic level:
- System analysis
- User interface design
- Testing and quality assurance
- Communication
- Problem-solving
- Analytical thinking
- Time management
- Collaboration
- Adaptability and flexibility
- Attention to detail
- Requirements gathering and documentation
- Process modeling and workflow analysis
- Stakeholder management and engagement
- Agile and Scrum methodologies
- User acceptance testing and validation
- Change management and impact analysis
- Documentation and technical writing
- Knowledge of business analysis frameworks

The Senior level must has above Junior's skill categories but in higher level and also requires these additional skill categories:
- Data Modeling and Database Design
- Advanced SQL Queries and Optimization
- API Integration and Web Services
- Data Warehousing and ETL Processes
- Cloud Computing and Infrastructure
- Leadership and Mentoring
- Negotiation and Conflict Resolution
- Strategic Thinking and Decision Making
- Stakeholder Management and Relationship Building
- Presentation and Facilitation
- Business Process Reengineering
- Business Impact Analysis
- Business Strategy and Alignment
- Agile Methodologies (Scrum, Kanban)
- Change Management and Risk Assessment

To gather data for the quiz, please refer to the following books:
- 'Agile and Business Analysis: Practical guidance for IT professionals' by Lynda Girvan, Debra Paul
- 'Business Analysis 4th ed. Edition' by Debra Paul, James Cadle
- 'Business Analysis Best Practice for Success' by Steven P. Blais
- 'Business Analysis for Dummies' by Kupe Kupersmith, Paul Mulvey, and Kate McGoey
- 'Business Analysis for Practitioners: A Practice Guide'
- 'Business Analysis Handbook' by Howard Podeswa
- 'Business Analysis Methodology Book' by Emrah Yayici
- 'Business Analysis Techniques for Process, Requirements, and Decision Modeling' by Hemant K. Jain
- 'Business Analysis Techniques: 99 Essential Tools for Success' by James Cadle, Debra Paul, and Paul Turner
- 'Business Analyst's Mentor Book: With Best Practice Business Analysis Techniques and Software Requirements Management Tips' by Emrah Yayici
- 'Digital Business and E-Commerce Management 7th Edition' by Dave Chaffey
- 'Directing the ERP Implementation: A Best Practice Guide to Avoiding Program Failure Traps While Tuning System Performance' by Michael W. Pelphrey
- 'Mastering the Requirements Process: Getting Requirements Right' by Suzanne Robertson and James Robertson
- 'Modern Systems Analysis and Design' by Joseph Valacich, Joey George
- 'REQUIREMENTS GATHERING FOR THE NEW BUSINESS ANALYST: The Simplified Beginners Guide to Business Systems Analysis (New Business Analyst Toolkit Book 1)' by Lane Bailey
- 'Requirements Writing for System Engineering' by George Koelsch
- 'Requirements Engineering: From System Goals to UML Models to Software Specifications' by Axel van Lamsweerde
- 'Software Requirements 3rd Edition' by Karl Wiegers and Joy Beatty
- 'Systems Analysis and Design 5th edition' by Alan Dennis, Barbara Wixom, Roberta M. Roth
- 'The Agile Business Analyst: Moving from Waterfall to Agile' by Ryland Leyton
- 'The Business Analysis Handbook' by Howard Podeswa
- 'The New Business Analyst's Guide to a Rock Solid Requirements Document: The Best Tips, Ideas and Methods to Help You Succeed in Your New Role (New Business Analyst Toolkit Book 2)' by Lane Bailey
- 'UML 2.0 in Action - A Project-Based Tutorial' by Patrick Grässle, Henriette Baumann, Philippe Baumann
- 'Use Case Modeling' by Kurt Bittner and Ian Spence
- 'User Stories Applied: For Agile Software Development' by Mike Cohn
- 'Writing Effective Use Cases' by Alistair Cockburn

Please gather as much relevant data as possible from these books. If any of the books do not contain specific content for a category, you can ignore it without mentioning that as an AI limitation. Do not collect data outside these books."
"""
        if level:
            prompt += f" Here is the selected level: {level}. Depend on the selected level is Junior or Senior, you will randomly choose a skill category from the category list. Based on the level, the chosen skill category, the responsibilities, and the collected information from books, you will create a real-life circumstance in the form of a story that puts the interviewee in a specific situation. The circumstance's complexity, depth, and breadth should be suitable for the {level} level of the IT BA or the BSA mentioned."
        prompt += """

After that, from the circumstance you will formulate a quiz question in the 'Q:' part.
The circumstance provided will not contain the whole answers to maintain the integrity of the quiz.
Ensure that the question and answers are clear, relevant, and do not confuse the interviewee.  

The structure of the quiz will consist of exactly 9 parts, each part in a different paragraph:
Part 1: "Category:" (Give the category name)
Part 2: "Circumstance:" (Set the context by providing a scenario or a brief description of a business situation. This could be a hypothetical scenario or a real-life example relevant to the organization or industry. The circumstance should include enough information for the candidate to understand the business problem or opportunity at hand.)
Part 3: "Q:"
Part 4: "A1:"
Part 5: "A2:"
Part 6: "A3:"
Part 7: "Correct:" (Is an integer number of the correct answer, give number "1" if "A1" is the correct answer, give number "2" if "A2" is the correct answer, give number "3" if "A3" is the correct answer)
Part 8: "Explanation:" (Give detailed explanation why the answer number is the most correct, why each other answers number are not correct or not fully correct.)
Part 9: "Example:" (Give an clear, easy-to-understand, easy-to-practice example for the correct answer number)

Ensure that each part is separated by a new paragraph to maintain the proper structure of the quiz.

"""
        # Call OpenAI API and get the response
        response = call_chatgpt_api(prompt)

        # Save the response to a text file
        filename = save_response_to_file(response)

         # Generate quiz parts using OpenAI's GPT-3
        quiz_parts = split_quiz_text(response)
        if quiz_parts is None:
            # Display an error message on the start.html page
            error_message = "Rate limit exceeded. Please try again later."
            return render_template("start.html", error_message=error_message, value=level)

        # Save the quiz response into the database
        save_quiz_to_database(quiz_parts, level)

        # Retrieve the latest quiz response from the database
        latest_response = retrieve_quiz_from_database()

        # Render the start.html template with quiz parts
        return render_template("start.html", quiz=latest_response, value=level)
    else:
        return "Invalid BA level"

def save_response_to_file(response):
    # Create the 'responses' folder if it doesn't exist
    if not os.path.exists("responses"):
        os.makedirs("responses")

    # Get the current timestamp
    current_time = datetime.datetime.now()
    timestamp = current_time.strftime("%Y%m%d_%H%M%S")

    # Create the filename using the timestamp
    filename = f"responses/response_{timestamp}.txt"

    # Save the response to a text file
    with open(filename, "w") as file:
        file.write(response)

    # Return the filename for reference
    return filename

# Define the reuse route
@app.route('/reuse', methods=['POST'])
def reuse_quiz():
    level = request.form.get('level')
    # Check if the selected level has at least 10 quizzes in the database
    db = get_db()
    db.row_factory = sqlite3.Row  # Set the row_factory to use column names as keys
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM aiquizgen WHERE level = ?", (level,))
    quiz_count = cursor.fetchone()[0]

    if quiz_count < 10:
        error_message = "Not enough quizzes available for reuse. Please try again later."
        return redirect(url_for('index', error_message=error_message))

    # Retrieve a random quiz from the database
    cursor.execute("SELECT * FROM aiquizgen WHERE level = ? ORDER BY RANDOM() LIMIT 1", (level,))
    quiz_data = cursor.fetchone()
    cursor.close()

    # If quiz data was found, return the quiz parts, otherwise return an error message
    if quiz_data:
        quiz_parts = {
            'Category': quiz_data['category'],
            'Circumstance': quiz_data['circumstance'],
            'Q': quiz_data['question'],
            'A1': quiz_data['answer1'],
            'A2': quiz_data['answer2'],
            'A3': quiz_data['answer3'],
            'Correct': quiz_data['correct_answer'],
            'Explanation': quiz_data['explanation'],
            'Example': quiz_data['example']
        }
        return render_template("reuse.html", quiz=quiz_parts, value=level)
    else:
        error_message = "No quizzes available for reuse. Please try again later."
        return render_template("reuse.html", error_message=error_message, value=level)

# Define the check_quiz_count route
@app.route('/check_quiz_count', methods=['GET'])
def check_quiz_count():
    level = request.args.get('level')
    db = get_db()
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM aiquizgen WHERE level = ?", (level,))
    quiz_count = cursor.fetchone()[0]
    cursor.close()

    # Respond with the quiz count as a JSON object
    response = {'quiz_count': quiz_count}
    return json.dumps(response)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
