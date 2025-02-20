# -*- coding: utf-8 -*-
"""241012.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1zzvGrsfKIPRKoOhIxZ0YfxJmcra8mxE-
"""

!pip install transformers torch nltk flask
!pip install datasets

import pandas as pd
from transformers import DistilBertForSequenceClassification, Trainer, TrainingArguments, DistilBertTokenizer
from datasets import Dataset
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import kagglehub
import torch
import json
from collections import defaultdict

# Download the latest version of the dataset
kagglehub.dataset_download("hassanamin/atis-airlinetravelinformationsystem")

# Load the dataset
data = pd.read_csv('/content/atis_intents_training.csv', header=None)
data.columns = ['intent', 'utterance']

# Prepare dataset for intent recognition
inputs = data['utterance'].tolist()
labels = data['intent'].tolist()

# Encode labels
label_encoder = LabelEncoder()
encoded_labels = label_encoder.fit_transform(labels)

# Create a DataFrame
df = pd.DataFrame({'utterance': inputs, 'labels': encoded_labels})

# Split the dataset into training and evaluation sets
train_df, eval_df = train_test_split(df, test_size=0.2, random_state=42)

# Create Dataset objects for training and evaluation
train_dataset = Dataset.from_dict({'input_ids': train_df['utterance'].tolist(), 'labels': train_df['labels'].tolist()})
eval_dataset = Dataset.from_dict({'input_ids': eval_df['utterance'].tolist(), 'labels': eval_df['labels'].tolist()})

# Tokenization using DistilBERT tokenizer
tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')

def tokenize_function(examples):
    return tokenizer(examples['input_ids'], padding='max_length', truncation=True)

# Tokenizing in batches to save memory
tokenized_train_dataset = train_dataset.map(tokenize_function, batched=True)
tokenized_eval_dataset = eval_dataset.map(tokenize_function, batched=True)

# Train model for intent recognition using DistilBERT
model = DistilBertForSequenceClassification.from_pretrained('distilbert-base-uncased', num_labels=len(label_encoder.classes_))
training_args = TrainingArguments(
    output_dir='./results',
    evaluation_strategy='epoch',
    learning_rate=5e-5,              # Increased learning rate for faster convergence
    per_device_train_batch_size=8,   # Keep batch size manageable
    num_train_epochs=2,              # Reduced number of epochs
    fp16=True,                       # Enable mixed precision training
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_train_dataset,
    eval_dataset=tokenized_eval_dataset,  # Add the evaluation dataset
)

# Train the model
trainer.train()

# Function to simulate user feedback
def collect_feedback(intent, response):
    print(f"Chatbot Response: {response}")
    feedback = input("Was this response helpful? (y/n): ")
    return 1 if feedback.lower() == 'y' else 0

# Simulated user input for testing
user_inputs = [
    "Book a flight from New York to San Francisco",
    "I want to know the weather in London",
    "Find me a hotel in Los Angeles",
]

# Store feedback
feedback_data = []
response_values = defaultdict(float)  # Store response values for Q-learning simulation

# Loop through the simulated user inputs
for input_text in user_inputs:
    # Perform intent recognition
    inputs_encoded = tokenizer(input_text, return_tensors="pt", padding=True, truncation=True, max_length=128)

    # Ensure no gradient computation
    with torch.no_grad():
        logits = model(**inputs_encoded).logits
    predicted_label_index = logits.argmax().item()
    predicted_intent = label_encoder.inverse_transform([predicted_label_index])[0]

    # Simulated response
    simulated_response = f"I can help you with that! Intent recognized: {predicted_intent}."

    # Collect feedback on the response
    feedback = collect_feedback(predicted_intent, simulated_response)

    # Update the response value based on feedback (simulated Q-learning)
    alpha = 0.1  # Learning rate
    response_values[simulated_response] += alpha * (feedback - response_values[simulated_response])  # Update rule

    # Store feedback
    feedback_data.append({
        'input': input_text,
        'predicted_intent': predicted_intent,
        'response': simulated_response,
        'feedback': feedback
    })

# Save feedback data to a JSON file
with open('feedback_data.json', 'w') as f:
    json.dump(feedback_data, f, indent=4)

# Save response values to a JSON file for further analysis
with open('response_values.json', 'w') as f:
    json.dump(response_values, f, indent=4)

print("Feedback collected and saved.")

import pandas as pd
from transformers import DistilBertForSequenceClassification, DistilBertTokenizer, pipeline
import torch
import json
from collections import defaultdict

# Load the pre-trained model and tokenizer
model = DistilBertForSequenceClassification.from_pretrained('distilbert-base-uncased', num_labels=len(label_encoder.classes_))
tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')

# Load the NER model
ner_model = pipeline("ner", model="dbmdz/bert-large-cased-finetuned-conll03-english", tokenizer="dbmdz/bert-large-cased-finetuned-conll03-english")

# Function to simulate user feedback
def collect_feedback(intent, response):
    print(f"Chatbot Response: {response}")
    rating = int(input("Rate the response (1-5): "))
    return rating

# Store feedback
feedback_data = []
response_values = defaultdict(float)  # Store response values for Q-learning simulation

def chatbot():
    print("Welcome to the chatbot! Type 'exit' to stop.")
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            break

        # Perform intent recognition
        inputs_encoded = tokenizer(user_input, return_tensors="pt", padding=True, truncation=True, max_length=128)

        # Ensure no gradient computation
        with torch.no_grad():
            logits = model(**inputs_encoded).logits
        predicted_label_index = logits.argmax().item()
        predicted_intent = label_encoder.inverse_transform([predicted_label_index])[0]

        # Perform entity extraction
        entities = ner_model(user_input)
        formatted_entities = [{'word': entity['word'], 'entity': entity['entity']} for entity in entities]

        # Print the intent and entities
        print(f"Intent: {predicted_intent}")
        print(f"Entities: {formatted_entities}")

        # Example response generation based on intent and entities
        if predicted_intent == 'flight_booking':
            response = "Chatbot: Where would you like to fly?"
        else:
            response = "Chatbot: How can I help you?"

        # Collect feedback on the response
        feedback = collect_feedback(predicted_intent, response)

        # Store feedback without averaging
        feedback_data.append({
            'input': user_input,
            'predicted_intent': predicted_intent,
            'response': response,
            'feedback': feedback,
            'entities': formatted_entities
        })

        # Simulated Q-learning adjustment (for demonstration purposes)
        alpha = 0.1  # Learning rate
        response_values[response] += alpha * (feedback - response_values[response])  # Update rule
        print("Feedback stored:", feedback_data)

        # Ask if the user wants to continue
        continue_prompt = input("Do you want to ask more questions? (y/n): ")
        if continue_prompt.lower() != 'y':
            break

# Start the chatbot
chatbot()

# Save feedback data to a JSON file after chat
with open('feedback_data.json', 'w') as f:
    json.dump(feedback_data, f, indent=4)

print("Feedback collected and saved.")