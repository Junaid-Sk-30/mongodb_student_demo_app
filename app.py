import streamlit as st
from pymongo import MongoClient
import pandas as pd

st.set_page_config(page_title='MongoDB Student Demo', page_icon='🎓', layout='wide')

# -----------------------------
# MongoDB Connection Configuration
# -----------------------------
# Corrected variable declaration and fallback logic
try:
    MONGO_URI = st.secrets["MONGO_URI"]
except Exception:
    MONGO_URI = "mongodb+srv://junaidsk3007_db_user:6A12NuYvHguIF3pz@cluster0.smnwx2j.mongodb.net/?appName=Cluster0"

# Parentheses used correctly here instead of square brackets
client = MongoClient(MONGO_URI)
db = client['college_db']
students = db['students']

# -----------------------------
# Helper functions
# -----------------------------
def student_to_row(doc):
    subject_marks = {s['name']: s['marks'] for s in doc.get('subjects', [])}
    return {
        'Student ID': doc.get('student_id', ''),
        'Name': doc.get('name', ''),
        'Program': doc.get('program', ''),
        'Semester': doc.get('semester', ''),
        'Age': doc.get('age', ''),
        'City': doc.get('city', ''),
        'Skills': ', '.join(doc.get('skills', [])),
        'DBMS': subject_marks.get('DBMS', ''),
        'Machine Learning': subject_marks.get('Machine Learning', ''),
        'Statistics': subject_marks.get('Statistics', ''),
    }

def load_students(query=None):
    query = query or {}
    docs = list(students.find(query, {'_id': 0}))
    return pd.DataFrame([student_to_row(d) for d in docs]) if docs else pd.DataFrame()

# -----------------------------
# Sidebar Navigation Menu
# -----------------------------
st.sidebar.title('🎓 MongoDB Demo')
page = st.sidebar.radio(
    'Choose Module',
    ['Dashboard', 'Add Student', 'Search Students', 'Update/Delete', 'Student Records', 'Analytics']
)
st.sidebar.markdown('---')
st.sidebar.caption('Database: college_db | Collection: students')

# -----------------------------
# Dashboard Module
# -----------------------------
if page == 'Dashboard':
    st.title('MongoDB Student Performance Management System')
    st.write('A compact demo app for teaching MongoDB CRUD operations, embedded documents, arrays, filtering, and aggregation.')

    try:
        total = students.count_documents({})
        python_count = students.count_documents({'skills': 'Python'})
        sem2_count = students.count_documents({'semester': 2})
    except Exception as e:
        st.error(f"Database connection error: {e}")
        total, python_count, sem2_count = 0, 0, 0

    c1, c2, c3 = st.columns(3)
    c1.metric('Total Students', total)
    c2.metric('Students with Python Skill', python_count)
    c3.metric('Semester 2 Students', sem2_count)

# -----------------------------
# Add Student Module
# -----------------------------
elif page == 'Add Student':
    st.title('➕ Add Student')
    with st.form('add_student_form'):
        c1, c2 = st.columns(2)
        student_id = c1.text_input('Student ID')
        name = c2.text_input('Name')
        program = c1.selectbox('Program', ['MSc Data Science', 'MSc Statistics', 'MSc Computer Science'])
        # Fixed empty selectbox option options list
        semester = c2.selectbox('Semester', [1, 2, 3, 4])
        age = c1.number_input('Age', min_value=18, max_value=60, value=22)
        city = c2.text_input('City')
        
        st.subheader('Subject Marks')
        m1, m2, m3 = st.columns(3)
        dbms_marks = m1.number_input('DBMS', min_value=0, max_value=100, value=75)
        ml_marks = m2.number_input('Machine Learning', min_value=0, max_value=100, value=75)
        stat_marks = m3.number_input('Statistics', min_value=0, max_value=100, value=75)
        skills_text = st.text_input('Skills (comma-separated)', 'Python, MongoDB')
        submitted = st.form_submit_button('Insert Student')

    if submitted and student_id and name:
        if students.find_one({'student_id': student_id}):
            st.error('Student ID already exists.')
        else:
            doc = {
                'student_id': student_id, 'name': name, 'program': program, 
                'semester': semester, 'age': int(age), 'city': city,
                'subjects': [
                    {'name': 'DBMS', 'marks': int(dbms_marks)}, 
                    {'name': 'Machine Learning', 'marks': int(ml_marks)}, 
                    {'name': 'Statistics', 'marks': int(stat_marks)}
                ], 
                'skills': [s.strip() for s in skills_text.split(',') if s.strip()]
            }
            students.insert_one(doc)
            st.success('Student inserted successfully.')

# -----------------------------
# Search Module
# -----------------------------
elif page == 'Search Students':
    st.title('🔍 Search Students')
    search_type = st.selectbox('Search by', ['Student ID', 'City', 'Skill', 'Semester'])
    query = {}
    if search_type == 'Student ID':
        v = st.text_input('Enter Student ID')
        if v: query = {'student_id': v}
    elif search_type == 'City':
        v = st.text_input('Enter City')
        if v: query = {'city': v}
    elif search_type == 'Skill':
        v = st.text_input('Enter Skill')
        if v: query = {'skills': v}
    elif search_type == 'Semester':
        # Fixed missing selectbox options target list values array lookup matrix
        query = {'semester': st.selectbox('Select Semester', [1, 2, 3, 4])}

    if st.button('Run Query'):
        df = load_students(query)
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info('No results found.')

# -----------------------------
# Update/Delete Module
# -----------------------------
elif page == 'Update/Delete':
    st.title('✏️ Update / Delete Student')
    student_id = st.text_input('Enter Student ID')
    doc = students.find_one({'student_id': student_id}, {'_id': 0}) if student_id else None
    if doc:
        st.json(doc)
        action = st.radio('Action', ['Update City', 'Add Skill', 'Delete Student'])
        if action == 'Update City':
            nc = st.text_input('New City')
            if st.button('Update'):
                students.update_one({'student_id': student_id}, {'$set': {'city': nc}})
                st.success('Updated successfully.')
        elif action == 'Add Skill':
            ns = st.text_input('New Skill')
            if st.button('Add'):
                students.update_one({'student_id': student_id}, {'$addToSet': {'skills': ns}})
                st.success('Skill added successfully.')
        elif action == 'Delete Student' and st.checkbox('Confirm'):
            if st.button('Delete'):
                students.delete_one({'student_id': student_id})
                st.success('Student record deleted.')

# -----------------------------
# Student Records Module
# -----------------------------
elif page == 'Student Records':
    st.title('📋 Student Records')
    df = load_students()
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info('No student records found in the database collection.')

# -----------------------------
# Analytics Module
# -----------------------------
elif page == 'Analytics':
    st.title('📊 Aggregation Analytics')
    pipeline = [
        {'$unwind': '$subjects'}, 
        {'$group': {'_id': '$subjects.name', 'average_marks': {'$avg': '$subjects.marks'}}}, 
        {'$sort': {'average_marks': -1}}
    ]
    try:
        res = list(students.aggregate(pipeline))
    except Exception:
        res = []
        
    if res:
        df = pd.DataFrame([{'Subject': r['_id'], 'Average Marks': round(r['average_marks'], 2)} for r in res])
        st.dataframe(df, use_container_width=True)
        st.bar_chart(df.set_index('Subject'))
    else:
        st.info('No metrics telemetry data found to visualize.')
