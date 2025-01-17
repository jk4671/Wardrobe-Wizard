
import openai 
from openai import OpenAI

import openai_secrets
client = OpenAI(api_key=openai_secrets.SECRET_KEY)


# TEXT GENERATION TEST
response = client.chat.completions.create(
  model="gpt-3.5-turbo",
  messages=[
    {
      "role": "user",
      "content": "Once upon a time"
    }
  ],
  # temperature=0,
  max_tokens=100,
  # top_p=1,
  # frequency_penalty=0,
  # presence_penalty=0
)

x = response.choices[0].message.content  
print(x)


# IMAGE GENERATION TEST

response_image = client.images.generate(
  prompt="A cute baby sea otter",
  n=1,
  size="256x256",
)

print(response_image.data[0].url)

