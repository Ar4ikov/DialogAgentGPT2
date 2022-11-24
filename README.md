# DialogAgentGPT2

This is a DialogAgent that uses GPT2 as the underlying model. It is based on the [microsoft/DialoGPT](https://huggingface.co/microsoft/DialoGPT-small). <br>

HuggingFace Model: https://huggingface.co/Ar4ikov/DialogAgentGPT2 <br>

![img](https://i.imgur.com/bGXIWqm.png)

### Usage

> Add the `BOT_TOKEN` in `.env` file

**Build the container**

```bash
docker build -t dialogagentgpt2 .
```

**Run the container**

```bash
docker run -d -v /workspaces/DialogAgentGPT2/.cache:/dialogagentbot/.cache --env-file .env dialogagentgpt2
```

> In case you want to set your `.cache` local directory, you should set the absolute path to the `docker run` command. (e.g. `-v /home/username/.cache:/dialogagentbot/.cache`)

Just not edit --volume and --env-file vars please uwu

### Credits

- [microsoft/DialoGPT](https://huggingface.co/microsoft/DialoGPT)
- [HuggingFace](https://huggingface.co/)
- [DialogAgentGPT2 by Ar4ikov](https://huggingface.co/Ar4ikov/DialogAgentGPT2)
- [PyTorch](https://pytorch.org/)
- [Docker](https://www.docker.com/)