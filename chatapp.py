import streamlit as st
import base64
import os
from groq import Groq
from pinecone import Pinecone, ServerlessSpec
import streamlit.components.v1 as com

os.environ["GROQ_API_KEY"] = "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"
os.environ["PINECONE_API_KEY"] = "a421fd7f-7ae5-496a-8b1d-2480d49bd4cb"         

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)
pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
index = pc.Index("quickstart")

st.session_state.api_key = os.environ.get("GROQ_API_KEY")

# Only show the API key input if the key is not already set
if not st.session_state.api_key:
    # Ask the user's API key if it doesn't exist
    api_key = st.text_input("Enter API Key", type="password")
    
    # Store the API key in the session state once provided
    if api_key:
        st.session_state.api_key = api_key
        st.rerun()  # Refresh the app once the key is entered to remove the input field
else:
    # If the API key exists, show the chat app
    com.html("""

<body>
             
             <style>
.example2 {
 color:#b6bcf8;
 height: 50px;	
 overflow: hidden;
 position: relative;
}
.example2 h1 {
 position: absolute;
 width: 100%;
 height: 100%;
 margin: 0;
 line-height: 50px;
 text-align: left;

 /* Apply animation to this element */	
 animation: example2 3s ease-out;
}
/* Move it (define the animation) */
@keyframes example2 {
 0%   { 
 transform: translateX(200%); 		
 }
 100% { 
 transform: translateX(0%); 
 }
}
</style>

<div class="example2">
<h1>HeartStrings</h1>
</div>



""")
    
    with open('style.css') as f:
        st.markdown(f'<style>{f.read()}</style>',unsafe_allow_html=True)

    with st.chat_message("assistant",avatar="🤖"):
        st.write("Hi, How can I help")
    # Initialize the chat message list in session state if it doesn't exist
    if "chat_messages" not in st.session_state:
        st.session_state.groq_chat_messages = [{"role": "system", "content": '''
        (The user is a person with poor mental health
        the user is here for your emotional support...
        they're not doing well and they badly want somebody to talk to.
        you don't have to really ask them about it unless they mention it!)
        '''
        }]
        st.session_state.chat_messages = []
    a=0
    # Display previous chat messages
    for messages in st.session_state.chat_messages:
        if messages["role"] in ["user", "assistant"]:
            a = a+1
            if a%2==0:
                with st.chat_message(messages["role"],avatar="🤖"):
                    st.markdown(messages["content"])
            else:
                with st.chat_message(messages["role"],avatar="😊"):
                    st.markdown(messages["content"])
                
    def get_chat():
        embedding = pc.inference.embed(
            model="multilingual-e5-large",
            inputs=[st.session_state.chat_messages[-1]["content"]],
            parameters={
                "input_type": "query"
            }
        )
        results = index.query(
            namespace="ns1",
            vector=embedding[0].values,
            top_k=3,
            include_values=False,
            include_metadata=True
        )
        context = ""
        for result in results.matches:
            if result['score'] > 0.8:
                context += result['metadata']['text']
            
        st.session_state.groq_chat_messages[-1]["content"] = f"User Query: {st.session_state.chat_messages[-1]['content']} \n Retrieved Content (optional): {context}"
        chat_completion = client.chat.completions.create(
            messages=st.session_state.groq_chat_messages,
            model="llama-3.1-8b-instant",
        )
        return chat_completion.choices[0].message.content

    # Handle user input
    if prompt := st.chat_input("Type your message here..."):
        # Display user message
        with st.chat_message("user",avatar="😊"):
            st.markdown(prompt)
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        st.session_state.groq_chat_messages.append({"role": "user", "content": prompt})
        # Get the assistant's response
        with st.spinner("Getting responses..."):
            response = get_chat()
        with st.chat_message("assistant",avatar="🤖"):
            st.markdown(response)
        
        # Add user message and assistant response to chat history
        st.session_state.chat_messages.append({"role": "assistant", "content": response})
        st.session_state.groq_chat_messages.append({"role": "assistant", "content": response})