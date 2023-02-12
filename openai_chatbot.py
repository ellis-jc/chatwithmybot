import openai
import time

def get_message_response(previous_messages_user, previous_messages_bot, new_message, prompt, key):
    # Using the OpenAI API generate a response to the new message
    # The prompt is the chatbot prompt + the previous messages from the user and the bot

    openai.api_key = key

    # Print the type of each argument
    zip_user_bot = zip(previous_messages_user, previous_messages_bot)

    full_prompt = prompt + ''.join([f"\n\nUser: {user_message}\n\nBot: {bot_message}" for user_message, bot_message in zip_user_bot]) + f"\n\nUser: {new_message}\n\nBot: "

    print(f"full_prompt: {full_prompt}")
    
    # Call the OpenAI API
    for attempt in range(5):
        try:
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=full_prompt,
                temperature=0.9,
                max_tokens=1000,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0.6,
                best_of=1,
                n=1,
                stream=False,
                stop=[" User:", " Bot:"],
            )
            print(response)
            break
        except openai.error.RateLimitError as e:
            print(e)
            print("API rate limit exceeded, sleeping for 2 seconds")
            time.sleep(2)

    # Return the response choice
    return response.choices[0].text
    
