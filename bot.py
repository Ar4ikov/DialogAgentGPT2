from telebot import TeleBot
from telebot.types import Message
from telebot import logger
import logging
import os
import transformers
import torch


class DialogAgentGPT2Bot:
    def __init__(self):
        self.bot = TeleBot(os.environ["BOT_TOKEN"])
        self.logger = logger
        self.logger.setLevel(logging.INFO)
        self.transformers_logger = logging.getLogger("transformers")
        self.transformers_logger.setLevel(logging.ERROR)

        self.model_id = "Ar4ikov/DialogAgentGPT2"
        self.model: transformers.AutoModelForCausalLM = None
        self.tokenizer: transformers.AutoTokenizer = None
        self.pad_token = None

        self.user_cache = {}
        self.max_chat_history_size = 4 # elements in array
    
    def init_transformers_pipeline(self):
        self.logger.info("Loading model...")
        self.model = transformers.AutoModelForCausalLM.from_pretrained(self.model_id)
        self.tokenizer = transformers.AutoTokenizer.from_pretrained(self.model_id)
        self.tokenizer.padding_side = 'left'
        self.pad_token = self.tokenizer.eos_token
        self.logger.info("Model loaded")

    def create_user(self, user_id: int):
        # create a key with dict with 'enabled': bool, 'chat_history': list[str] and chat_history_ids: torch.tensor
        self.user_cache[user_id] = {
            'enabled': False,
            'chat_history': [],
            'chat_history_ids': None
        }

    def delete_user(self, user_id: int):
        self.user_cache.pop(user_id, None)

    def enable_user(self, user_id: int):
        if user_id not in self.user_cache:
            self.create_user(user_id)

        self.user_cache[user_id]['enabled'] = True

    def disable_user(self, user_id: int):
        if user_id not in self.user_cache:
            return
        self.user_cache[user_id]['enabled'] = False

    def update_user_chat_history(self, user_id: int, message: str):
        if not self.user_cache[user_id]['enabled']:
            return

        self.user_cache[user_id]['chat_history'].append(message)

        if len(self.user_cache[user_id]['chat_history']) > self.max_chat_history_size * 2:
            self.user_cache[user_id]['chat_history'] = self.user_cache[user_id]['chat_history'][-self.max_chat_history_size * 2:]

        # join with pad_token
        if len(self.user_cache[user_id]['chat_history']) > 0:
            self.user_cache[user_id]['chat_history_ids'] = self.tokenizer.encode(self.pad_token.join(self.user_cache[user_id]['chat_history']) + self.pad_token, return_tensors='pt')

    def get_user_chat_history_ids(self, user_id: int):
        return self.user_cache[user_id]['chat_history_ids']

    def drop_chat_history(self, user_id):
        self.user_cache[user_id]['chat_history'] = []
        self.user_cache[user_id]['chat_history_ids'] = None

    def chat(self, text, chat_history_ids):
        if self.model is None or self.tokenizer is None:
            self.init_transformers_pipeline()

        # encode the new user input, add the eos_token and return a tensor in Pytorch
        new_user_input_ids = self.tokenizer.encode(text + self.pad_token, return_tensors='pt')
        # print(new_user_input_ids)

        # append the new user input tokens to the chat history
        bot_input_ids = torch.cat([chat_history_ids, new_user_input_ids], dim=-1) if chat_history_ids is not None else new_user_input_ids

        # generated a response while limiting the total chat history to 1000 tokens, 
        chat_history_ids = self.model.generate(
            bot_input_ids, max_length=200,
            pad_token_id=self.tokenizer.eos_token_id,  
            no_repeat_ngram_size=3,       
            do_sample=True, 
            top_k=100, 
            top_p=0.7,
            temperature = 0.8
        )
        
        return self.tokenizer.decode(chat_history_ids[:, bot_input_ids.shape[-1]:][0], skip_special_tokens=True), chat_history_ids

    def handlers(self):
        @self.bot.message_handler(commands=['start'])
        def start(message: Message):
            self.create_user(message.from_user.id)
            self.bot.send_message(message.from_user.id, "Hello! I'm DialogAgentGPT2Bot. I can chat with you. Send /help for more info.")

        @self.bot.message_handler(commands=['help'])
        def help(message: Message):
            # /start - start the bot
            # /help - show this message
            # /enablehis = enable chat history
            # /disablehis = disable chat history
            # /restart = restart the chat_history
            self.bot.send_message(message.from_user.id, "/start - start the bot\n/help - show this message\n/enablehis - enable chat history\n/disablehis - disable chat history\n/restart - restart the chat_history")

        @self.bot.message_handler(commands=['enablehis'])
        def enablehis(message: Message):
            self.enable_user(message.from_user.id)
            self.bot.send_message(message.from_user.id, "Chat history enabled.")

        @self.bot.message_handler(commands=['disablehis'])
        def disablehis(message: Message):
            self.disable_user(message.from_user.id)
            self.drop_chat_history(message.from_user.id)
            self.bot.send_message(message.from_user.id, "Chat history disabled.")

        @self.bot.message_handler(commands=['restart'])
        def restart(message: Message):
            self.drop_chat_history(message.from_user.id)
            self.bot.send_message(message.from_user.id, "Chat history restarted.")

        @self.bot.message_handler(content_types=['text'])
        def text(message: Message):
            if message.from_user.id not in self.user_cache:
                self.create_user(message.from_user.id)

            response, chat_history_ids = self.chat(message.text, self.get_user_chat_history_ids(message.from_user.id))

            self.bot.send_message(message.from_user.id, response)

            if self.user_cache[message.from_user.id]['enabled']:
                self.update_user_chat_history(message.from_user.id, message.text)
                self.update_user_chat_history(message.from_user.id, response)

    def run(self):
        self.init_transformers_pipeline()
        self.handlers()
        self.bot.infinity_polling(timeout=9999999)


if __name__ == '__main__':
    bot = DialogAgentGPT2Bot()
    bot.run()
