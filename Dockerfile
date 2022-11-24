FROM python:3.9-slim-buster
WORKDIR /dialogagentbot

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy source code
COPY . .

# Run the bot
CMD ["python", "bot.py"]