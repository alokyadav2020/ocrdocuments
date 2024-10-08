import streamlit as st
import os
import uuid
from src.documentsai import ocr_doc
from src.anthropic import get_base64_encoded_image,ocr_anthropic
from src.openai import encode_image,openai_ocr
from dotenv import load_dotenv
from google.oauth2 import service_account
from PIL import Image

# Load the .env file
load_dotenv()
st.set_page_config(page_title="OCR",
                   layout="wide",
                   initial_sidebar_state='collapsed',
                   )
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)


PROJECT_ID = os.getenv('PROJECT_ID')
LOCATION =  os.getenv('LOCATION')  
PROCESSOR_ID = os.getenv('PROCESSOR_ID') 
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
OPEN_AI_KEY = os.getenv('OPEN_AI_KEY')
USER = os.getenv('USER')
PASSWORD = os.getenv('PASSWORD')
credentials = service_account.Credentials.from_service_account_info(st.secrets["gcs_connections"])


# Define the folder to save the uploaded files
UPLOAD_FOLDER = "uploaded_files"

# Ensure the folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Function to delete existing files in the folder
def delete_existing_files(folder):
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)  # Delete the file
        except Exception as e:
            st.error(f"Error deleting file {file_path}: {e}")




def login_page():
    st.title("Login Page")
    # Create login input fields
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    # Login button
    if st.button("Login"):
        # Check if the credentials match
        if PASSWORD == password and USER == username:
            st.session_state['logged_in'] = True
            st.session_state['username'] = username
            st.rerun()
            # st.experimental_user()  # Refresh the page to move to the home page
        else:
            st.error("Invalid username or password")

      
def home_page():
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
    uploaded_file = st.file_uploader("Choose an image...", type=["jpeg","png"])

    if uploaded_file is not None:
        file_size = uploaded_file.size
        if file_size < MAX_FILE_SIZE:

            delete_existing_files(UPLOAD_FOLDER)
            unique_filename = str(uuid.uuid4()) + "." + "png"
            save_path = os.path.join(UPLOAD_FOLDER, unique_filename)
            model = st.selectbox(label="Select Model", options= ['Select','Document_AI','Anthropic','OpenAI'])

            jpeg_image = Image.open(uploaded_file)

        # Save the image in PNG format
            jpeg_image.save(save_path)
            # with open(save_path, "wb") as f:
            #    f.write(uploaded_file.getbuffer())
            col1, col2 = st.columns([1,1])  
            with col1:
                st.image(save_path, caption="Uploaded Image", use_column_width=True)

            with col2:
                    

                if model == 'Select':
                    ""
                elif model == "Document_AI":
                    result,confidence = ocr_doc(PROJECT_ID,LOCATION,PROCESSOR_ID,save_path,credentials)
                    st.write("Document AI, (By Google).")
                    st.write("-"*80)
                    
                    st.write(f"Confidence : {confidence:.2f} %")

                    st.write("-"*80)

                    st.write(result)

                elif model == 'Anthropic':
                        antropic_model_name = st.selectbox(label='Select Anthropic model',options=['claude-3-5-sonnet-20240620','claude-3-opus-20240229'])

                        promt_txt = st.text_input(label="Default Prompt : Transcribe this text. Only output the text and nothing else.",
                                                value="",
                                                placeholder="Please write custom prompt here.")
                        if promt_txt:
                            
                            basestring = get_base64_encoded_image(save_path)
                            result, total_tokanes = ocr_anthropic(image_strin=basestring,api_key=ANTHROPIC_API_KEY,prompt=promt_txt,MODEL_NAME=antropic_model_name)
                            st.write("-"*80)
                            st.write(f"Total tokens : {total_tokanes}")
                            st.write("-"*80)                       
                            st.write(result)

                elif model == 'OpenAI':
                    antropic_model_name = st.selectbox(label='Select OpenAI model',options=['gpt-4o','gpt-4o-mini','o1-preview','gpt-4-turbo'])
                    promt_txt_openai = st.text_input(label="Default Prompt : Transcribe this text. Only output the text and nothing else.",
                                                value="",
                                                placeholder="Please write custom prompt here.")
                    if promt_txt_openai:

                        base64_img = f"data:image/png;base64,{encode_image(save_path)}"  
                        result,ttl_tokaen = openai_ocr(base64_img=base64_img,api_key=OPEN_AI_KEY)      
                        st.write("-"*80)
                        st.write(f"Total tokens : {ttl_tokaen}")
                        st.write("-"*80)                       
                        st.write(result)

        else:
            st.warning('File size exceeds the 5 MB limit. Please upload a smaller file.')                
                    
      
    if st.button("Logout"):
        st.session_state['logged_in'] = False
        # st.experimental_user()
        st.rerun()
        
        
      
   
   
    # st.write(result)


    
    
    # Confirmation message
    # st.success(f"File saved as {unique_filename}")
    
    # # Display the uploaded image
    # st.image(save_path, caption="Uploaded Image", use_column_width=True)

if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    login_page()  # Show the login page if not logged in
else:
    home_page()    
