from openai import OpenAI
client = OpenAI(
    api_key="您的 APIKEY", # 从https://cloud.siliconflow.cn/account/ak获取
    base_url="https://api.siliconflow.cn/v1"
)

messages = [
    {"role": "user", "content": "用当前语言解释微调模型流程"},
]

response = client.chat.completions.create(
    model="ft:LoRA/Qwen/Qwen2.5-32B-Instruct:uy4pgkdhjs:yuqing:dkzxjcayvpokexfohjob",
    messages=messages,
    stream=True,
    max_tokens=4096
)

for chunk in response:
    print(chunk.choices[0].delta.content, end='')